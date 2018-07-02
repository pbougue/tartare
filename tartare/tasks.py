# Copyright (c) 2001-2016, Canal TP and/or its affiliates. All rights reserved.
#
# This file is part of Navitia,
#     the software to build cool stuff with public transport.
#
# Hope you'll enjoy and contribute to this project,
#     powered by Canal TP (www.canaltp.fr).
# Help us simplify mobility and open public transport:
#     a non ending quest to the responsive locomotion way of traveling!
#
# LICENCE: This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
# Stay tuned using
# twitter @navitia
# IRC #navitia on freenode
# https://groups.google.com/d/forum/navitia
# www.navitia.io

import logging
from typing import Optional, List, Union

from billiard.einfo import ExceptionInfo
from celery import chain, chord, group
from celery.apps.worker import Worker
from celery.result import AsyncResult
from celery.task import Task
from celery.utils.dispatch import Signal

import tartare
from tartare import celery
from tartare.core import contributor_export_functions
from tartare.core import coverage_export_functions
from tartare.core import models
from tartare.core.constants import ACTION_TYPE_AUTO_CONTRIBUTOR_EXPORT, ACTION_TYPE_AUTO_COVERAGE_EXPORT, \
    JOB_STATUS_FAILED, JOB_STATUS_RUNNING, JOB_STATUS_DONE
from tartare.core.context import Context, ContributorExportContext, CoverageExportContext
from tartare.core.gridfs_handler import GridFsHandler
from tartare.core.models import CoverageExport, Coverage, Job, Contributor, PreProcess, SequenceContainer, \
    PublicationPlatform
from tartare.core.publisher import ProtocolException, ProtocolManager, PublisherManager
from tartare.exceptions import FetcherException, ProtocolManagerException, PublisherManagerException, IntegrityException
from tartare.processes.processes import PreProcessManager

logger = logging.getLogger(__name__)


class CallbackTask(tartare.ContextTask):
    def on_failure(self, exc: Exception, task_id: str, args: list, kwargs: dict, einfo: ExceptionInfo) -> None:
        # if contributor_export or coverage_export is failing we clean the context
        if isinstance(args[0], Context):
            context = args[0]
            self.update_job(context.job, exc)
            if tartare.app.config.get('SEND_MAIL_ON_FAILURE'):
                self.send_mail(context.job)
            super(CallbackTask, self).on_failure(exc, task_id, args, kwargs, einfo)

    def send_mail(self, job: Job) -> None:
        from tartare import mailer
        mailer.build_msg_and_send_mail(job)

    def update_job(self, job: Job, exc: Exception) -> None:
        if job:
            with tartare.app.app_context():
                job.update(state=JOB_STATUS_FAILED, error_message=str(exc))


def publish_data_on_platform(platform: PublicationPlatform, coverage: Coverage, environment_id: str, job: Job) -> None:
    step = "publish_data {env} {platform} on {url}".format(env=environment_id, platform=platform.type, url=platform.url)
    job.update(step=step)
    coverage_export = CoverageExport.get_last(coverage.id)
    if coverage_export:
        gridfs_handler = GridFsHandler()
        file = gridfs_handler.get_file_from_gridfs(coverage_export.gridfs_id)

        try:
            publisher = PublisherManager.select_from_publication_platform(platform)
            protocol_uploader = ProtocolManager.select_from_platform(platform)
            publisher.publish(protocol_uploader, file, coverage, coverage_export, platform.input_data_source_ids)
            # Upgrade current_ntfs_id
            current_ntfs_id = coverage_export.gridfs_id
            coverage.environments[environment_id].current_ntfs_id = current_ntfs_id
            coverage.update()
        except (ProtocolException, ProtocolManagerException, PublisherManagerException) as exc:
            msg = 'publish data on platform "{type}" with url {url} failed, {error}'.format(
                error=str(exc), url=platform.url, type=platform.type)
            logger.error(msg)
            raise exc


def finish_job(context: Context) -> None:
    context.job = context.job.update(state=JOB_STATUS_DONE)


@celery.task(bind=True, default_retry_delay=180,
             max_retries=tartare.app.config.get('RETRY_NUMBER_WHEN_FAILED_TASK'),
             base=CallbackTask)
def contributor_export(self: Task, context: ContributorExportContext, contributor: Contributor,
                       check_for_update: bool = True, data_source_to_fetch_id: str = None) -> \
        Optional[List[str]]:
    try:
        context.job = context.job.update(state=JOB_STATUS_RUNNING, step="fetching data")
        logger.info(
            'contributor_export of {cid} from job {action}'.format(cid=contributor.id, action=context.job.action_type))
        # Launch fetch all dataset for contributor
        nb_updated_data_sources_fetched = contributor_export_functions.fetch_datasets_and_return_updated_number(
            contributor, data_source_to_fetch_id)
        logger.info('number of data_sources updated for contributor {cid}: {number}'.
                    format(cid=contributor.id, number=nb_updated_data_sources_fetched))
        # contributor export is always done if coming from API call, we skip updated data verification
        # when in automatic update, it's only done if at least one of data sources has changed
        if not check_for_update or nb_updated_data_sources_fetched:
            context.job = context.job.update(step="building preprocesses context")
            context.fill_context(contributor)
            context.job = context.job.update(step="preprocess")
            return launch(contributor.preprocesses, context)
        else:
            finish_job(context)
    except FetcherException as exc:
        msg = 'contributor export failed{retry_or_not}, error {error}'.format(
            error=str(exc),
            retry_or_not=' (retrying)' if int(tartare.app.config.get('RETRY_NUMBER_WHEN_FAILED_TASK')) else ''
        )
        logger.error(msg)
        raise self.retry(exc=exc)


@celery.task(base=CallbackTask)
def contributor_export_finalization(context: ContributorExportContext) -> List[str]:
    contributor = context.contributor_contexts[0].contributor
    logger.info('contributor_export_finalization of {cid} from job {action}'.format(cid=contributor.id,
                                                                                    action=context.job.action_type))
    context.job.update(state=JOB_STATUS_RUNNING, step="merge")
    context = contributor_export_functions.merge(contributor, context)

    context.job.update(step="postprocess")
    context = contributor_export_functions.postprocess(contributor, context)

    # insert export in mongo db
    context.job.update(step="save_contributor_export")
    exports_ids = contributor_export_functions.save_export(contributor, context)
    finish_job(context)
    return exports_ids


@celery.task(base=CallbackTask)
def coverage_export(context: CoverageExportContext) -> CoverageExportContext:
    coverage = context.coverage
    job = context.job
    logger.info('coverage_export of {cov} from job {action}'.format(cov=coverage.id, action=job.action_type))
    context.job.update(state=JOB_STATUS_RUNNING, step="fetching context")
    if not coverage.input_data_source_ids:
        raise IntegrityException(
            'no data sources are attached to coverage {}'.format(
                coverage.id))

    context.job.update(step="preprocess")
    launch(coverage.preprocesses, context)


@celery.task(base=CallbackTask)
def coverage_export_finalization(context: CoverageExportContext) -> CoverageExportContext:
    coverage = context.coverage
    job = context.job
    logger.info('coverage_export_finalization of {cov} from job {action}'.format(cov=coverage, action=job.action_type))
    context.job.update(step="merge")
    context = coverage_export_functions.merge(coverage, context)

    context.job.update(step="postprocess")
    coverage_export_functions.postprocess(coverage, context)

    # insert export in mongo db
    context.job.update(step="save_coverage_export")
    coverage_export_functions.save_export(coverage, context)

    # launch publish for all environment
    sorted_environments = {}
    # flip env: object in object: env
    flipped_environments = dict((v, k) for k, v in coverage.environments.items())
    # sort envs
    raw_sorted_environments = SequenceContainer.sort_by_sequence(list(coverage.environments.values()))
    # restore mapping
    for environment in raw_sorted_environments:
        sorted_environments[flipped_environments[environment]] = environment
    for env in sorted_environments:
        environment = coverage.environments[env]
        sorted_publication_platforms = SequenceContainer.sort_by_sequence(environment.publication_platforms)
        for publication_platform in sorted_publication_platforms:
            publish_data_on_platform(publication_platform, coverage, env, job)
    finish_job(context)
    return context


def launch(processes: List[PreProcess], context: Context) -> List[str]:
    enabled_processes = [process for process in processes if process.enabled]
    sorted_preprocesses = SequenceContainer.sort_by_sequence(enabled_processes)
    actions = []

    # Do better
    def get_queue(preprocess: PreProcess) -> str:
        return {
            "Ruspell": "tartare_ruspell",
            "Gtfs2Ntfs": "tartare_gtfs2ntfs",

        }.get(preprocess.type, "tartare")

    if not sorted_preprocesses:
        if isinstance(context, ContributorExportContext):
            return contributor_export_finalization.s(context).delay()
        else:
            return coverage_export_finalization.s(context).delay()
    else:
        first_process = sorted_preprocesses[0]
        actions.append(run_preprocess.s(context, first_process).set(queue=get_queue(first_process)))

        for p in sorted_preprocesses[1:]:
            actions.append(run_preprocess.s(p).set(queue=get_queue(p)))

        if isinstance(context, ContributorExportContext):
            actions.append(contributor_export_finalization.s())
        else:
            actions.append(coverage_export_finalization.s())

    return chain(*actions).delay()


@celery.task(base=CallbackTask)
def run_preprocess(context: Context, preprocess: PreProcess) -> Context:
    process_instance = PreProcessManager.get_preprocess(context, preprocess=preprocess)
    logging.getLogger(__name__).info('Applying preprocess {preprocess_name}'.format(preprocess_name=preprocess.type))
    return process_instance.do()


@celery.task()
def automatic_update() -> None:
    logger.info('automatic_update')
    contributors = models.Contributor.all()
    if contributors:
        actions_header = []
        logger.info("fetching {} contributors".format(len(contributors)))
        for contributor in contributors:
            for data_source in contributor.data_sources:
                if data_source.should_fetch():
                    # launch contributor export for data source
                    job = models.Job(contributor_id=contributor.id, data_source_id=data_source.id,
                                     action_type=ACTION_TYPE_AUTO_CONTRIBUTOR_EXPORT)
                    job.save()
                    action_export = contributor_export.si(ContributorExportContext(job), contributor,
                                                          data_source_to_fetch_id=data_source.id)
                    actions_header.append(action_export)
        chord(actions_header)(automatic_update_launch_coverage_exports.s())
    else:
        logger.info("no contributors found")


@celery.task(bind=True, default_retry_delay=tartare.app.config.get('RETRY_DELAY_COVERAGE_EXPORT_TRIGGER'),
             max_retries=None)
def automatic_update_launch_coverage_exports(self: Task,
                                             contributor_export_results: Union[
                                                 List[Optional[AsyncResult]], Optional[AsyncResult]
                                             ]) -> None:
    logger.info('automatic_update_launch_coverage_exports')
    logger.debug("{}".format(contributor_export_results))
    contributor_export_results = contributor_export_results if isinstance(contributor_export_results, list) \
        else [contributor_export_results]
    updated_data_source_ids = []  # type: List[str]
    for contributor_export_result in contributor_export_results:
        if isinstance(contributor_export_result, AsyncResult):
            logger.debug('subtask launched {} with info {} is ready ? {}'.format(contributor_export_result,
                                                                                 contributor_export_result.info,
                                                                                 contributor_export_result.ready()))
            if not contributor_export_result.ready():
                logger.debug('retrying callback...')
                self.retry()
            else:
                logger.debug('subtask finished with {}'.format(contributor_export_result.info))
                # if contributor_export action generated some exports in database (new data set fetched)
                if isinstance(contributor_export_result.info, list):
                    updated_data_source_ids += contributor_export_result.info
    logger.debug("{}".format(updated_data_source_ids))
    if updated_data_source_ids:
        coverages = models.Coverage.all()
        logger.info("updated_data_source_ids = " + (','.join(updated_data_source_ids)))
        logger.info("fetching {} coverages".format(len(coverages)))
        actions = []
        for coverage in coverages:
            if any(data_source_id in updated_data_source_ids for data_source_id in coverage.input_data_source_ids):
                job = models.Job(coverage_id=coverage.id, action_type=ACTION_TYPE_AUTO_COVERAGE_EXPORT)
                job.save()
                actions.append(coverage_export.si(CoverageExportContext(job, coverage=coverage)))
        if actions:
            group(actions).delay()
    else:
        logger.info("none of the contributors have been updated")


from celery.signals import worker_init


@worker_init.connect
def limit_chord_unlock_retry_delay(signal: Signal, sender: Worker, **kwargs: dict) -> None:
    task = sender.app.tasks['celery.chord_unlock']
    task.default_retry_delay = tartare.app.config.get('RETRY_DELAY_UNLOCK_CHORD')
    logger.debug('limit_chord_unlock_retry_delay made celery.chord_unlock.default_retry_delay = {}'.format(
        task.default_retry_delay))


@celery.task()
def purge_pending_jobs() -> None:
    from tartare import mailer
    logger.info('purge_pending_jobs')
    statuses = ['pending', 'running']
    nb_hours = 4
    cancelled_jobs = models.Job.cancel_pending_updated_before(nb_hours, statuses)
    if cancelled_jobs:
        mailer.build_purge_report_and_send_mail(cancelled_jobs, nb_hours, statuses)
