import glob
import logging
import os
import datetime

from zipfile import ZipFile
from tartare import celery
from tartare.core import calendar_handler, models
from tartare.core.calendar_handler import GridCalendarData
from tartare.core.data_handler import is_ntfs_data
from tartare.helper import upload_file
import tempfile
from tartare.core.contributor_export_functions import merge, postprocess
from tartare.core.contributor_export_functions import fetch_dataset
import tartare.processes
from tartare.core.gridfs_handler import GridFsHandler

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


@celery.task(bind=True, default_retry_delay=300, max_retries=5, acks_late=True)
def send_file_to_tyr_and_discard(self, coverage_id, environment_type, file_id):
    coverage = models.Coverage.get(coverage_id)
    url = coverage.environments[environment_type].tyr_url
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

@celery.task(bind=True, default_retry_delay=300, max_retries=5, acks_late=True)
def send_ntfs_to_tyr(self, coverage_id, environment_type):
    coverage = models.Coverage.get(coverage_id)
    url = coverage.environments[environment_type].tyr_url
    grifs_handler = GridFsHandler()
    ntfs_file = grifs_handler.get_file_from_gridfs(coverage.environments[environment_type].current_ntfs_id)
    grid_calendars_file = coverage.get_grid_calendars()
    response = None
    if grid_calendars_file:
        with tempfile.TemporaryDirectory() as tmpdirname:
            output_ntfs_file = os.path.join(tmpdirname, '{}-database.zip'\
                    .format(datetime.datetime.now().strftime("%Y%m%d%H%M%S")))
            logger.debug("Working to generate [{}]".format(output_ntfs_file))
            _do_merge_calendar(grid_calendars_file, ntfs_file, output_ntfs_file)
            logger.info('trying to send data to %s', url)
            #TODO: how to handle the timeout?
            with open(output_ntfs_file, 'rb') as file:
                response = upload_file(url, output_ntfs_file, file)
    else:
        response = upload_file(url, ntfs_file.filename, ntfs_file)

    if response.status_code != 200:
        raise self.retry()


@celery.task(default_retry_delay=300, max_retries=5)
def contributor_export(contributor, job):
    try:

        models.Job.update(job_id=job.id, state="running", step="fetching data")
        context = fetch_dataset(contributor.data_sources)

        models.Job.update(job_id=job.id, state="running", step="preprocess")
        context = launch([], context)

        models.Job.update(job_id=job.id, state="running", step="merge")
        context = merge(contributor, context)

        models.Job.update(job_id=job.id, state="running", step="postprocess")
        postprocess(contributor, context)

        models.Job.update(job_id=job.id, state="done")
    except Exception as e:
        models.Job.update(job_id=job.id, state="failed", error_message=str(e))
        logger.error('Contributor export failed, error {}'.format(str(e)))


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
