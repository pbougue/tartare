import glob
import logging
import shutil
import os
import datetime
import zipfile
from zipfile import ZipFile
from shutil import copyfile

from tartare import app
from tartare import celery
from tartare.core import calendar_handler, models
from tartare.core.calendar_handler import GridCalendarData
from tartare.core.data_handler import type_of_data, is_ntfs_data, is_calendar_data
from tartare.helper import upload_file
import tempfile

logger = logging.getLogger(__name__)


@celery.task()
def update_all_data_task():
    for coverage in models.Coverage.all():
        update_data(coverage)


@celery.task()
def update_data(coverage):
    input_dir = coverage.technical_conf.input_dir
    logger.info('scanning directory %s', input_dir)
    handle_data(coverage)


def remove_old_ntfs_files(directory):
    files = glob.glob(os.path.join(directory, "*"))

    for f in files:
        if os.path.isfile(f):
            if f.endswith('.zip') and (type_of_data(f)[0] == 'fusio'):
                logger.debug("Cleaning NTFS file {}".format(f))
                os.remove(f)


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


def handle_data(coverage):
    """
    Move all file from the input_dir to output_dir
    All interesting data are also moved to the current_dir
    """
    input_dir = coverage.technical_conf.input_dir
    current_data_dir = coverage.technical_conf.current_data_dir
    output_dir = coverage.technical_conf.output_dir
    if not os.path.exists(input_dir):
        logger.debug('directory {} does not exists, skipping scan'.format(input_dir))
        return

    create_dir(output_dir)
    create_dir(current_data_dir)

    for filename in os.listdir(input_dir):
        input_file = os.path.join(input_dir, filename)
        output_ntfs_file = os.path.join(output_dir, '{}-database.zip'\
                .format(datetime.datetime.now().strftime("%Y%m%d%H%M%S")))
        output_file = os.path.join(output_dir, filename)
        logger.debug("Working on [{}] to generate [{}]".format(input_file, output_file))
        # copy data interesting data

        calendar_dir = os.path.join(current_data_dir,
                                    app.config.get("GRID_CALENDAR_DIR"))
        calendar_file = os.path.join(calendar_dir, app.config.get("CALENDAR_FILE"))
        if is_ntfs_data(input_file):
            # NTFS file is moved to the CURRENT_DATA_DIR, old NTFS file is deleted
            remove_old_ntfs_files(current_data_dir)
            copyfile(input_file, os.path.join(current_data_dir, filename))
            grid_calendars_file = coverage.get_grid_calendars()
            if grid_calendars_file:
                # Merge
                _do_merge_calendar(grid_calendars_file, input_file, output_ntfs_file)
                os.remove(input_file)
            else:
                shutil.move(input_file, output_ntfs_file)
        elif input_file.endswith(".tmp"):
            pass
        else:
            shutil.move(input_file, output_file)


@celery.task(bind=True)
def update_calendars(self, coverage_id):
    coverage = models.Coverage.get(coverage_id)
    input_dir = coverage.technical_conf.input_dir
    current_data_dir = coverage.technical_conf.current_data_dir
    output_dir = coverage.technical_conf.output_dir
    # Merge with last NTFS
    current_ntfs = _get_current_nfts_file(current_data_dir)
    grid_calendars_file = coverage.get_grid_calendars()
    if current_ntfs and grid_calendars_file:
        output_ntfs_file = os.path.join(output_dir, '{}-database.zip'\
                .format(datetime.datetime.now().strftime("%Y%m%d%H%M%S")))
        logger.debug("Working to generate [{}]".format(output_ntfs_file))
        _do_merge_calendar(grid_calendars_file, current_ntfs, output_ntfs_file)

@celery.task(bind=True, default_retry_delay=300, max_retries=5, acks_late=True)
def send_file(self, coverage_id, environment_type, file_id):
    coverage = models.Coverage.get(coverage_id)
    url = coverage.environments[environment_type].tyr_url
    file = models.get_file_from_gridfs(file_id)
    logging.debug('file: %s', file)
    logger.info('trying to send %s to %s', file.filename, url)
    #how to handle timeout?
    response = upload_file(url, file.filename, file)
    if response.status_code != 200:
        raise self.retry()
    else:
        models.delete_file_from_gridfs(file_id)

@celery.task(bind=True, default_retry_delay=300, max_retries=5, acks_late=True)
def update_ntfs(self, coverage_id, environment_type):
    coverage = models.Coverage.get(coverage_id)
    url = coverage.environments[environment_type].tyr_url
    ntfs_file = models.get_file_from_gridfs(coverage.environments[environment_type].current_ntfs_id)
    grid_calendars_file = coverage.get_grid_calendars()
    response = None
    if grid_calendars_file:
        with tempfile.TemporaryDirectory() as tmpdirname:
            output_ntfs_file = os.path.join(tmpdirname, '{}-database.zip'\
                    .format(datetime.datetime.now().strftime("%Y%m%d%H%M%S")))
            logger.debug("Working to generate [{}]".format(output_ntfs_file))
            _do_merge_calendar(grid_calendars_file, ntfs_file, output_ntfs_file)
            logger.info('trying to send data to %s', url)
            #how to handle the timeout?
            with open(output_ntfs_file, 'rb') as file:
                response = upload_file(url, output_ntfs_file, file)
    else:
        response = upload_file(url, ntfs_file.filename, ntfs_file)

    if response.status_code != 200:
        raise self.retry()

