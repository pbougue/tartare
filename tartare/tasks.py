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

logger = logging.getLogger(__name__)


@celery.task()
def update_all_data_task():
    for coverage in models.Coverage.all():
        update_data(coverage)


@celery.task()
def update_data(coverage):
    input_dir = coverage.technical_conf.input_dir
    logger.info('scanning directory %s', input_dir)
    handle_data(input_dir, coverage.technical_conf.output_dir, coverage.technical_conf.current_data_dir)


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


def handle_data(input_dir, output_dir, current_data_dir):
    """
    Move all file from the input_dir to output_dir
    All interesting data are also moved to the current_dir
    """
    if not os.path.exists(input_dir):
        logger.debug('directory {} does not exists, skipping scan'.format(input_dir))
        return

    create_dir(output_dir)
    create_dir(current_data_dir)

    for filename in os.listdir(input_dir):
        input_file = os.path.join(input_dir, filename)
        output_ntfs_file = os.path.join(output_dir, '{}-database.zip'.format(datetime.datetime.now().strftime("%Y%m%d%H%M%S")))
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
            if os.path.isfile(calendar_file):
                # Merge
                _do_merge_calendar(calendar_file, input_file, output_ntfs_file)
                os.remove(input_file)
            else:
                shutil.move(input_file, output_ntfs_file)
        elif is_calendar_data(input_file):
            if not os.path.exists(calendar_dir):
                os.makedirs(calendar_dir)
            shutil.move(input_file, calendar_file)

            # Merge with last NTFS
            current_ntfs = _get_current_nfts_file(current_data_dir)
            if current_ntfs:
                _do_merge_calendar(calendar_file, current_ntfs, output_ntfs_file)
            else:
                logger.info("No NTFS file to compute the calendar data")
        elif input_file.endswith(".tmp"):
            pass
        else:
            shutil.move(input_file, output_file)
