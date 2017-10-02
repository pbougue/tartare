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
from urllib.error import ContentTooShortError, HTTPError, URLError
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
from tartare.core.context import Context
from tartare.core.gridfs_handler import GridFsHandler
from tartare.core.models import CoverageExport, Coverage, Job, Platform, Contributor, PreProcess, SequenceContainer
from tartare.core.publisher import HttpProtocol, FtpProtocol, ProtocolException, AbstractPublisher, AbstractProtocol
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
        # if contributor_export or coverage_export is failing we clean the context
        if isinstance(args[0], Context):
            with tartare.app.app_context():
                args[0].cleanup()
        self.update_job(args, exc)
        self.send_mail(args)
        super(CallbackTask, self).on_failure(exc, task_id, args, kwargs, einfo)

    def send_mail(self, args: list) -> None:
        from tartare import mailer
        mailer.build_msg_and_send_mail(self.get_job(args))

    @staticmethod
    def get_job(args: list) -> Optional[Job]:
        for arg in args:
            if isinstance(arg, models.Job):
                with tartare.app.app_context():
                    return models.Job.get_one(arg.id)
        return None

    def update_job(self, args: list, exc: Exception) -> None:
        job = self.get_job(args)
        if job:
            with tartare.app.app_context():
                models.Job.update(job_id=job.id, state="failed", error_message=str(exc))


@celery.task(bind=True, default_retry_delay=300, max_retries=5, acks_late=True)
def send_file_to_tyr_and_discard(self: Task, coverage_id: str, environment_type: str, file_id: str) -> None:
    coverage = models.Coverage.get(coverage_id)
    url = coverage.environments[environment_type].publication_platforms[0].url
    grifs_handler = GridFsHandler()
    file = grifs_handler.get_file_from_gridfs(file_id)
    logging.debug('file: %s', file)
    logger.info('trying to send %s to %s', file.filename, url)
    # TODO: how to handle timeout?
    try:
        response = upload_file(url, file.filename, file)
        if response.status_code != 200:
            raise self.retry()
        else:
            grifs_handler.delete_file_from_gridfs(file_id)
    except:
        logging.exception('error')


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


@celery.task(bind=True, default_retry_delay=180, max_retries=0, acks_late=True, base=CallbackTask)
def publish_data_on_platform(self: Task, platform: Platform, coverage: Coverage, environment_id: str, job: Job) -> None:
    logger.info('publish_data_on_platform {}'.format(platform.url))
    coverage_export = CoverageExport.get_last(coverage.id)
    gridfs_handler = GridFsHandler()
    file = gridfs_handler.get_file_from_gridfs(coverage_export.gridfs_id)

    try:
        publisher = _get_publisher(platform)
        publisher.publish(_get_protocol_uploader(platform, job), file, coverage, coverage_export)
        # Upgrade current_ntfs_id
        current_ntfs_id = gridfs_handler.copy_file(coverage_export.gridfs_id)
        coverage.update(coverage.id, {'environments.{}.current_ntfs_id'.format(environment_id): current_ntfs_id})
    except (ProtocolException, Exception) as exc:
        msg = 'publish data on  platform failed, error {}'.format(str(exc))
        logger.error(msg)
        self.retry(exc=exc)


@celery.task()
def finish_job(job_id: str) -> None:
    models.Job.update(job_id=job_id, state="done")


@celery.task(bind=True, default_retry_delay=300, max_retries=5, acks_late=True)
def send_ntfs_to_tyr(self: Task, coverage_id: str, environment_type: str) -> None:
    coverage = models.Coverage.get(coverage_id)
    url = coverage.environments[environment_type].publication_platforms[0].url
    grifs_handler = GridFsHandler()
    ntfs_file = grifs_handler.get_file_from_gridfs(coverage.environments[environment_type].current_ntfs_id)
    grid_calendars_file = coverage.get_grid_calendars()
    if grid_calendars_file:
        with tempfile.TemporaryDirectory() as tmpdirname:
            output_ntfs_file = os.path.join(tmpdirname, '{}-database.zip' \
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


@celery.task(bind=True, default_retry_delay=180, max_retries=tartare.app.config.get('RETRY_NUMBER_WHEN_FAILED_TASK'),
             base=CallbackTask)
def contributor_export(self: Task, context: Context, contributor: Contributor, job: Job,
                       check_for_update: bool = True) -> Context:
    try:
        models.Job.update(job_id=job.id, state="running", step="fetching data")
        logger.info('contributor_export')
        # Launch fetch all dataset for contributor
        nb_updated_data_sources_fetched = contributor_export_functions.fetch_datasets_and_return_updated_number(
            contributor)
        logger.info('number of data_sources updated for contributor {cid}: {number}'.format(cid=contributor.id,
                                                                                            number=nb_updated_data_sources_fetched))
        # contributor export is always done if coming from API call, we skip updated data verification
        # when in automatic update, it's only done if at least one of data sources has changed
        if not check_for_update or nb_updated_data_sources_fetched:
            context = contributor_export_functions.build_context(contributor, context)
            models.Job.update(job_id=job.id, state="running", step="preprocess")
            context = launch(contributor.preprocesses, context)

            models.Job.update(job_id=job.id, state="running", step="merge")
            context = contributor_export_functions.merge(contributor, context)

            models.Job.update(job_id=job.id, state="running", step="postprocess")
            context = contributor_export_functions.postprocess(contributor, context)

            # insert export in mongo db
            models.Job.update(job_id=job.id, state="running", step="save_contributor_export")
            contributor_export_functions.save_export(contributor, context)
            coverages = [coverage for coverage in models.Coverage.all() if coverage.has_contributor(contributor)]
            actions = []
            if coverages:
                actions.append(coverage_export.s(context, coverages[0], job))
                for coverage in coverages[1:]:
                    # Launch coverage export
                    actions.append(coverage_export.s(coverage, job))
                context = chain(*actions).apply().get()
            return context

    except (HTTPError, ContentTooShortError, URLError, Exception) as exc:
        msg = 'Contributor export failed, error {}'.format(str(exc))
        logger.error(msg)
        raise self.retry(exc=exc)


@celery.task(bind=True, default_retry_delay=180, max_retries=tartare.app.config.get('RETRY_NUMBER_WHEN_FAILED_TASK'),
             base=CallbackTask)
def coverage_export(self: Task, context: Context, coverage: Coverage, job: Job) -> Context:
    logger.info('coverage_export')
    try:
        context.instance = 'coverage'
        models.Job.update(job_id=job.id, state="running", step="fetching data")
        context.fill_contributor_contexts(coverage)

        models.Job.update(job_id=job.id, state="running", step="preprocess")
        context = launch(coverage.preprocesses, context)

        models.Job.update(job_id=job.id, state="running", step="merge")
        context = coverage_export_functions.merge(coverage, context)

        models.Job.update(job_id=job.id, state="running", step="postprocess")
        coverage_export_functions.postprocess(coverage, context)

        # insert export in mongo db
        models.Job.update(job_id=job.id, state="running", step="save_coverage_export")
        coverage_export_functions.save_export(coverage, context)
        actions = []
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
                actions.append(publish_data_on_platform.si(platform, coverage, env, job))
        if actions:
            chain(*actions).apply()
        return context
    except Exception as exc:
        msg = 'coverage export failed, error {}'.format(str(exc))
        logger.error(msg)
        raise self.retry(exc=exc)


def launch(processes: List[PreProcess], context: Context) -> Context:
    if not processes:
        return context
    sorted_preprocesses = SequenceContainer.sort_by_sequence(processes)
    actions = []

    # Do better
    def get_queue(preprocess: PreProcess) -> str:
        return 'process_ruspell' if preprocess.type == 'Ruspell' else 'tartare'

    first_process = sorted_preprocesses[0]
    actions.append(run_contributor_preprocess.s(context, first_process).set(queue=get_queue(first_process)))

    for p in sorted_preprocesses[1:]:
        actions.append(run_contributor_preprocess.s(p).set(queue=get_queue(p)))

    return chain(*actions).apply_async().get(disable_sync_subtasks=False)


@celery.task
def run_contributor_preprocess(context: Context, preprocess: PreProcess) -> Context:
    process_instance = PreProcessManager.get_preprocess(context, preprocess=preprocess)
    logging.getLogger(__name__).info('Applying preprocess {preprocess_name}'.format(preprocess_name=preprocess.type))
    return process_instance.do()


@celery.task()
def automatic_update() -> None:
    contributors = models.Contributor.all()
    logger.info("fetching {} contributors".format(len(contributors)))
    for contributor in contributors:
        # launch contributor export
        job = models.Job(contributor_id=contributor.id, action_type="automatic_update")
        job.save()
        chain(contributor_export.si(Context(), contributor, job), finish_job.si(job.id)).delay()
