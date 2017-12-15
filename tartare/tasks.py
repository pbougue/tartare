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

import datetime
import logging
import os
import tempfile
from typing import Optional, List
from zipfile import ZipFile

from billiard.einfo import ExceptionInfo
from celery import chain
from celery.task import Task

import tartare
from tartare import celery
from tartare.core import calendar_handler, models
from tartare.core import contributor_export_functions
from tartare.core import coverage_export_functions
from tartare.core.calendar_handler import GridCalendarData
from tartare.core.constants import ACTION_TYPE_AUTO_CONTRIBUTOR_EXPORT, ACTION_TYPE_AUTO_COVERAGE_EXPORT
from tartare.core.context import Context
from tartare.core.gridfs_handler import GridFsHandler
from tartare.core.models import CoverageExport, Coverage, Job, Platform, Contributor, PreProcess, SequenceContainer, \
    ContributorExport
from tartare.core.publisher import HttpProtocol, FtpProtocol, ProtocolException, AbstractPublisher, AbstractProtocol
from tartare.exceptions import FetcherException
from tartare.helper import upload_file
from tartare.processes.processes import PreProcessManager

logger = logging.getLogger(__name__)


def _do_merge_calendar(calendar_file: str, ntfs_file: str, output_file: str) -> None:
    with ZipFile(calendar_file, 'r') as calendars_zip, ZipFile(ntfs_file, 'r') as ntfs_zip:
        grid_calendar_data = GridCalendarData()
        grid_calendar_data.load_zips(calendars_zip, ntfs_zip)
        new_ntfs_zip = calendar_handler.merge_calendars_ntfs(grid_calendar_data, ntfs_zip)
        calendar_handler.save_zip_as_file(new_ntfs_zip, output_file)


class CallbackTask(tartare.ContextTask):
    def on_failure(self, exc: Exception, task_id: str, args: list, kwargs: dict, einfo: ExceptionInfo) -> None:
        logger.debug('on_failure')
        logger.debug(exc)
        logger.debug(args)
        # if contributor_export or coverage_export is failing we clean the context
        if isinstance(args[0], Context):
            context = args[0]
            with tartare.app.app_context():
                context.cleanup()
            self.update_job(context.job, exc)
            self.send_mail(context.job)
            super(CallbackTask, self).on_failure(exc, task_id, args, kwargs, einfo)

    def send_mail(self, job: Job) -> None:
        from tartare import mailer
        mailer.build_msg_and_send_mail(job)

    def update_job(self, job: Job, exc: Exception) -> None:
        logger.debug('update_job')
        logger.debug(job)
        if job:
            with tartare.app.app_context():
                models.Job.update(job_id=job.id, state="failed", error_message=str(exc))


def _get_publisher(platform: Platform) -> AbstractPublisher:
    from tartare import navitia_publisher, stop_area_publisher, ods_publisher
    publishers_by_type = {
        "navitia": navitia_publisher,
        "ods": ods_publisher,
        "stop_area": stop_area_publisher
    }
    if platform.type not in publishers_by_type:
        error_message = 'unknown platform type "{type}"'.format(type=platform.type)
        logger.error(error_message)
        raise Exception(error_message)

    return publishers_by_type[platform.type]


def _get_protocol_uploader(platform: Platform, job: Job) -> AbstractProtocol:
    publishers_by_protocol = {
        "http": HttpProtocol,
        "ftp": FtpProtocol
    }
    if platform.protocol not in publishers_by_protocol:
        error_message = 'unknown platform protocol "{protocol}"'.format(protocol=platform.protocol)
        models.Job.update(job_id=job.id, state="failed", error_message=error_message)
        logger.error(error_message)
        raise Exception(error_message)

    return publishers_by_protocol[platform.protocol](platform.url, platform.options)


def publish_data_on_platform(platform: Platform, coverage: Coverage, environment_id: str, job: Job) -> None:
    step = "publish_data {env} {platform} on {url}".format(env=environment_id, platform=platform.type, url=platform.url)
    models.Job.update(job_id=job.id, state="running", step=step)
    coverage_export = CoverageExport.get_last(coverage.id)
    gridfs_handler = GridFsHandler()
    file = gridfs_handler.get_file_from_gridfs(coverage_export.gridfs_id)

    try:
        publisher = _get_publisher(platform)
        publisher.publish(_get_protocol_uploader(platform, job), file, coverage, coverage_export)
        # Upgrade current_ntfs_id
        current_ntfs_id = coverage_export.gridfs_id
        coverage.update(coverage.id, {'environments.{}.current_ntfs_id'.format(environment_id): current_ntfs_id})
    except ProtocolException as exc:
        msg = 'publish data on platform "{type}" failed, {error}'.format(
            error=str(exc), url=platform.url, type=platform.type)
        logger.error(msg)
        raise exc


@celery.task()
def finish_job(context: Context) -> None:
    context.job = models.Job.update(job_id=context.job.id, state="done")


@celery.task(bind=True, default_retry_delay=300, max_retries=5, acks_late=True)
def send_ntfs_to_tyr(self: Task, coverage_id: str, environment_type: str) -> None:
    coverage = models.Coverage.get(coverage_id)
    url = coverage.environments[environment_type].publication_platforms[0].url
    grifs_handler = GridFsHandler()
    ntfs_file = grifs_handler.get_file_from_gridfs(coverage.environments[environment_type].current_ntfs_id)
    grid_calendars_file = coverage.get_grid_calendars()
    if grid_calendars_file:
        with tempfile.TemporaryDirectory() as tmpdirname:
            output_ntfs_file = os.path.join(tmpdirname, '{}-database.zip'
                                            .format(datetime.datetime.now().strftime("%Y%m%d%H%M%S")))
            logger.debug("Working to generate [{}]".format(output_ntfs_file))
            _do_merge_calendar(grid_calendars_file, ntfs_file, output_ntfs_file)
            logger.info('trying to send data to %s', url)
            # TODO: how to handle the timeout?
            with open(output_ntfs_file, 'rb') as file:
                response = upload_file(url, output_ntfs_file, file)
    else:
        response = upload_file(url, ntfs_file.filename, ntfs_file)

    if response.status_code != 200:
        raise self.retry()


@celery.task(bind=True, default_retry_delay=180,
             max_retries=tartare.app.config.get('RETRY_NUMBER_WHEN_FAILED_TASK'),
             base=CallbackTask)
def contributor_export(self: Task, context: Context, contributor: Contributor,
                       check_for_update: bool = True) -> Optional[ContributorExport]:
    try:
        context.job = models.Job.update(job_id=context.job.id, state="running", step="fetching data")
        logger.info('contributor_export from job {action}'.format(action=context.job.action_type))
        # Launch fetch all dataset for contributor
        nb_updated_data_sources_fetched = contributor_export_functions.fetch_datasets_and_return_updated_number(
            contributor)
        logger.info('number of data_sources updated for contributor {cid}: {number}'.
                    format(cid=contributor.id, number=nb_updated_data_sources_fetched))
        # contributor export is always done if coming from API call, we skip updated data verification
        # when in automatic update, it's only done if at least one of data sources has changed
        if not check_for_update or nb_updated_data_sources_fetched:
            context.job = models.Job.update(job_id=context.job.id, state="running",
                                            step="building preprocesses context")
            context = contributor_export_functions.build_context(contributor, context)
            context.job = models.Job.update(job_id=context.job.id, state="running", step="preprocess")
            launch(contributor.preprocesses, context)

    except FetcherException as exc:
        msg = 'contributor export failed{retry_or_not}, error {error}'.format(
            error=str(exc),
            retry_or_not=' (retrying)' if int(tartare.app.config.get('RETRY_NUMBER_WHEN_FAILED_TASK')) else ''
        )
        logger.error(msg)
        raise self.retry(exc=exc)


@celery.task(base=CallbackTask)
def contributor_export_finalization(context: Context) -> Optional[ContributorExport]:
    logger.info('contributor_export_finalization from job {action}'.format(action=context.job.action_type))
    contributor = context.contributor_contexts[0].contributor
    models.Job.update(job_id=context.job.id, state="running", step="merge")
    context = contributor_export_functions.merge(contributor, context)

    models.Job.update(job_id=context.job.id, state="running", step="postprocess")
    context = contributor_export_functions.postprocess(contributor, context)

    # insert export in mongo db
    models.Job.update(job_id=context.job.id, state="running", step="save_contributor_export")
    export = contributor_export_functions.save_export(contributor, context)
    finish_job(context)
    return export


@celery.task(base=CallbackTask)
def coverage_export(context: Context) -> Context:
    coverage = context.coverage
    job = context.job
    logger.info('coverage_export from job {action}'.format(action=job.action_type))
    context.instance = 'coverage'
    models.Job.update(job_id=job.id, state="running", step="fetching context")
    context.fill_contributor_contexts(coverage)

    models.Job.update(job_id=job.id, state="running", step="preprocess")
    launch(coverage.preprocesses, context)


@celery.task(base=CallbackTask)
def coverage_export_finalization(context: Context) -> Optional[ContributorExport]:
    coverage = context.coverage
    job = context.job
    logger.info('coverage_export_finalization from job {action}'.format(action=job.action_type))
    models.Job.update(job_id=job.id, state="running", step="merge")
    context = coverage_export_functions.merge(coverage, context)

    models.Job.update(job_id=job.id, state="running", step="postprocess")
    coverage_export_functions.postprocess(coverage, context)

    # insert export in mongo db
    models.Job.update(job_id=job.id, state="running", step="save_coverage_export")
    export = coverage_export_functions.save_export(coverage, context)
    if export:
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
            environment = coverage.get_environment(env)
            sorted_publication_platforms = SequenceContainer.sort_by_sequence(environment.publication_platforms)
            for platform in sorted_publication_platforms:
                publish_data_on_platform(platform, coverage, env, job)
    finish_job(context)
    return context


def launch(processes: List[PreProcess], context: Context) -> Context:
    logger.debug('launch')
    if not processes:
        if context.instance == 'contributor':
            contributor_export_finalization.si(context).delay()
        else:
            coverage_export_finalization.si(context).delay()
    else:
        sorted_preprocesses = SequenceContainer.sort_by_sequence(processes)
        actions = []

        # Do better
        def get_queue(preprocess: PreProcess) -> str:
            return 'process_ruspell' if preprocess.type == 'Ruspell' else 'tartare'

        first_process = sorted_preprocesses[0]
        actions.append(run_contributor_preprocess.s(context, first_process).set(queue=get_queue(first_process)))

        for p in sorted_preprocesses[1:]:
            actions.append(run_contributor_preprocess.s(p).set(queue=get_queue(p)))

        if context.instance == 'contributor':
            actions.append(contributor_export_finalization.s())
        else:
            actions.append(coverage_export_finalization.s())

        chain(*actions).delay()


@celery.task(base=CallbackTask)
def run_contributor_preprocess(context: Context, preprocess: PreProcess) -> Context:
    process_instance = PreProcessManager.get_preprocess(context, preprocess=preprocess)
    logging.getLogger(__name__).info('Applying preprocess {preprocess_name}'.format(preprocess_name=preprocess.type))
    return process_instance.do()


@celery.task()
def automatic_update(current_date: datetime.date = datetime.date.today()) -> None:
    logger.info('automatic_update')
    contributors = models.Contributor.all()
    logger.info("fetching {} contributors".format(len(contributors)))
    updated_contributors = []
    for contributor in contributors:
        # launch contributor export
        job = models.Job(contributor_id=contributor.id, action_type=ACTION_TYPE_AUTO_CONTRIBUTOR_EXPORT)
        job.save()
        action_export = contributor_export.si(Context('contributor', job, current_date=current_date), contributor)
        export = action_export.apply_async().get(disable_sync_subtasks=False)
        if export:
            updated_contributors.append(contributor.id)
        finish_job.si(job.id).delay()

    if updated_contributors:
        coverages = models.Coverage.all()
        logger.info("updated_contributors = " + (','.join(updated_contributors)))
        logger.info("fetching {} coverages".format(len(coverages)))
        for coverage in coverages:
            if any(contributor_id in updated_contributors for contributor_id in coverage.contributors):
                job = models.Job(coverage_id=coverage.id, action_type=ACTION_TYPE_AUTO_COVERAGE_EXPORT)
                job.save()
                chain(coverage_export.si(Context('coverage', job, current_date=current_date), coverage),
                      finish_job.si(job.id)).delay()
    else:
        logger.info("none of the contributors have been updated")
