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

import glob
import logging
import os
import datetime

from zipfile import ZipFile
from tartare import celery
from tartare.core import calendar_handler, models
from tartare.core.calendar_handler import GridCalendarData
from tartare.core.context import Context
from tartare.core.publisher import HttpProtocol, FtpProtocol, ProtocolException
from tartare.core.data_handler import is_ntfs_data
from tartare.helper import upload_file
import tempfile
from tartare.core import contributor_export_functions
from tartare.core import coverage_export_functions
import tartare.processes
from tartare.core.gridfs_handler import GridFsHandler
from tartare.core.models import CoverageExport, Coverage
from celery import chain
from urllib.error import ContentTooShortError, HTTPError, URLError



logger = logging.getLogger(__name__)


def create_dir(directory):
    """create directory if needed"""
    if not os.path.exists(directory):
        os.makedirs(directory)


def _do_merge_calendar(calendar_file, ntfs_file, output_file):
    with ZipFile(calendar_file, 'r') as calendars_zip, ZipFile(ntfs_file, 'r') as ntfs_zip:
        grid_calendar_data = GridCalendarData()
        grid_calendar_data.load_zips(calendars_zip, ntfs_zip)
        new_ntfs_zip = calendar_handler.merge_calendars_ntfs(grid_calendar_data, ntfs_zip)
        calendar_handler.save_zip_as_file(new_ntfs_zip, output_file)


def _get_current_nfts_file(current_data_dir):
    files = glob.glob(os.path.join(current_data_dir, "*"))

    return next((f for f in files if os.path.isfile(f) and f.endswith('.zip') and is_ntfs_data(f)), None)


class MailSender(tartare.celery.Task):
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        self.send_mail()
        super(MailSender, self).on_failure(exc, task_id, args, kwargs, einfo)

    def send_mail(self):
        # TODO sendmail
        pass

@celery.task(bind=True, default_retry_delay=300, max_retries=5, acks_late=True)
def send_file_to_tyr_and_discard(self, coverage_id, environment_type, file_id):
    coverage = models.Coverage.get(coverage_id)
    url = coverage.environments[environment_type].publication_platforms[0].url
    grifs_handler = GridFsHandler()
    file = grifs_handler.get_file_from_gridfs(file_id)
    logging.debug('file: %s', file)
    logger.info('trying to send %s to %s', file.filename, url)
    #TODO: how to handle timeout?
    try:
        response = upload_file(url, file.filename, file)
        if response.status_code != 200:
            raise self.retry()
        else:
            grifs_handler.delete_file_from_gridfs(file_id)
    except:
        logging.exception('error')


def _get_publisher(platform, job):
    from tartare import navitia_publisher, ods_publisher, stop_area_publisher
    publishers_by_type = {
        "navitia": navitia_publisher,
        "ods": ods_publisher,
        "stop_area": stop_area_publisher
    }
    if platform.type not in publishers_by_type:
        error_message = 'unknown platform type "{type}"'.format(type=platform.type)
        models.Job.update(job_id=job.id, state="failed", error_message=error_message)
        logger.error(error_message)
        raise Exception(error_message)

    return publishers_by_type[platform.type]


def _get_protocol_uploader(platform, job):
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


@celery.task(bind=True, default_retry_delay=180, max_retries=0, acks_late=True)
def publish_data_on_platform(self, platform, coverage, environment_id, job):
    gridfs_id = CoverageExport.get_last(coverage.id).get('gridfs_id')
    logger.info('publish_data_on_platform {}'.format(platform.url))
    gridfs_handler = GridFsHandler()
    file = gridfs_handler.get_file_from_gridfs(gridfs_id)

    publisher = _get_publisher(platform, job)

    try:
        publisher.publish(_get_protocol_uploader(platform, job), file, coverage.id)
        # Upgrade current_ntfs_id
        current_ntfs_id = gridfs_handler.copy_file(gridfs_id)
        coverage.update(coverage.id, {'environments.{}.current_ntfs_id'.format(environment_id): current_ntfs_id})
    except ProtocolException:
        models.Job.update(job_id=job.id, state="failed", error_message=str(e))
        self.retry()

@celery.task()
def finish_job(job_id):
    models.Job.update(job_id=job_id, state="done")

@celery.task(bind=True, default_retry_delay=300, max_retries=5, acks_late=True)
def send_ntfs_to_tyr(self, coverage_id, environment_type):
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

@celery.task(bind=True, default_retry_delay=180, max_retries=1, base=MailSender)
def contributor_export(self, contributor, job):
    try:
        context = Context()
        models.Job.update(job_id=job.id, state="running", step="fetching data")
        # Launch fetch all dataset for contributor
        context = contributor_export_functions.fetch_datasets(contributor, context)
        if context.data_sources_fetched:
            models.Job.update(job_id=job.id, state="running", step="preprocess")
            context = launch([], context)

            models.Job.update(job_id=job.id, state="running", step="merge")
            context = contributor_export_functions.merge(contributor, context)

            models.Job.update(job_id=job.id, state="running", step="postprocess")
            context = contributor_export_functions.postprocess(contributor, context)

            # insert export in mongo db
            models.Job.update(job_id=job.id, state="running", step="save_contributor_export")
            contributor_export_functions.save_export(contributor, context)
            coverages = [coverage for coverage in models.Coverage.all() if coverage.has_contributor(contributor)]
            if coverages:
                for coverage in coverages:
                    # Launch coverage export
                    coverage_export.delay(coverage, job)

    except (HTTPError, ContentTooShortError, URLError, Exception) as e:
        models.Job.update(job_id=job.id, state="failed", error_message=str(e))
        logger.error('Contributor export failed, error {}'.format(str(e)))
        raise self.retry()


@celery.task(bind=True, default_retry_delay=180, max_retries=1, base=MailSender)
def coverage_export(self, coverage, job):
    logger.info('coverage_export')
    try:
        context = Context()
        models.Job.update(job_id=job.id, state="running", step="fetching data")
        context.fill_contributor_exports(coverage=coverage)
        models.Job.update(job_id=job.id, state="running", step="merge")
        context = coverage_export_functions.merge(coverage, context)

        models.Job.update(job_id=job.id, state="running", step="postprocess")
        coverage_export_functions.postprocess(coverage, context)

        # insert export in mongo db
        models.Job.update(job_id=job.id, state="running", step="save_coverage_export")
        coverage_export_functions.save_export(coverage, context)
        actions = []
        # launch publish for all environment
        for env in coverage.environments:
            environment = coverage.get_environment(env)
            for platform in environment.publication_platforms:
                actions.append(publish_data_on_platform.si(platform, coverage, env, job))
        if actions:
            chain(*actions).delay()
    except Exception as e:
        models.Job.update(job_id=job.id, state="failed", error_message=str(e))
        logger.error('coverage export failed, error {}'.format(str(e)))
        raise self.retry()


def launch(processes, context):
    for p in processes:
        p_type = p.get('type')
        # Call p_type class

        kls = getattr(tartare.processes, p_type, None)
        if kls is None:
            logger.error('Unknown type %s', p_type)
            continue
        context = kls(context, p.get("source_params")).do()

    return context


@celery.task()
def automatic_update():
    contributors = models.Contributor.all()
    logger.info("fetching {} contributors".format(len(contributors)))
    for contributor in contributors:
        # launch contributor export
        job = models.Job(contributor_id=contributor.id, action_type="automatic_update")
        job.save()
        chain(contributor_export.si(contributor, job), finish_job(job.id)).delay()

