import os
from glob import glob
from shutil import copy
from zipfile import ZipFile, ZIP_DEFLATED
from tartare.tasks import handle_data, update_calendars, send_file
from tartare.core import calendar_handler, models
import requests_mock

def test_handle_not_ntfs_data(coverage_obj):
    """
    Test if a file which is not an ntfs file is moved to output_dir
    """
    with open(os.path.join(coverage_obj.technical_conf.input_dir, 'bob.txt'), 'a') as input_file:
        input_file.write("bob ?")

    handle_data(coverage_obj)
    files_in_output_dir = os.listdir(coverage_obj.technical_conf.output_dir)

    assert files_in_output_dir[0].endswith('bob.txt')


def test_handle_ntfs_data_without_calendar(coverage_obj):
    """
    Test if a ntfs file is copied to current_dir
    and moved to output_dir when there is no calendar
    """
    with open(os.path.join(coverage_obj.technical_conf.input_dir, 'contributors.txt'), 'a') as input_file:
        input_file.write("bob ?")
    handle_data(coverage_obj)

    files_in_output_dir = os.listdir(coverage_obj.technical_conf.output_dir)

    assert files_in_output_dir[0].endswith('database.zip')
    assert os.path.isfile(os.path.join(coverage_obj.technical_conf.current_data_dir, 'contributors.txt'))


def test_handle_ntfs_data_with_calendar(coverage_obj, fixture_dir):
    """
    Test if a ntfs file is copied to current_dir and merged
    with an existing calendar and moved to current_dir
    """
    ntfs_path = os.path.join(fixture_dir, 'ntfs/*.txt')

    ntfs_zip = ZipFile(os.path.join(coverage_obj.technical_conf.input_dir, 'ntfs.zip'), 'a', ZIP_DEFLATED, False)
    for filename in glob(ntfs_path):
        ntfs_zip.write(filename, os.path.basename(filename))
    ntfs_zip.close()

    calendar_file = os.path.join(fixture_dir, 'gridcalendar/export_calendars.zip')

    with open(calendar_file, 'rb') as f:
        coverage_obj.save_grid_calendars(f)
    handle_data(coverage_obj)

    files_in_output_dir = os.listdir(coverage_obj.technical_conf.output_dir)

    assert files_in_output_dir[0].endswith('database.zip')
    assert os.path.isfile(os.path.join(coverage_obj.technical_conf.current_data_dir, 'ntfs.zip'))

    with ZipFile(os.path.join(coverage_obj.technical_conf.output_dir, files_in_output_dir[0])) as new_ntfs_zip:
        files_in_zip = new_ntfs_zip.namelist()
        assert calendar_handler.GRID_CALENDARS in files_in_zip
        assert calendar_handler.GRID_PERIODS in files_in_zip
        assert calendar_handler.GRID_CALENDAR_REL_LINE in files_in_zip


def test_update_calendars_without_ntfs(coverage_obj, fixture_dir):
    """
    Test if a calendar file is in input_dir and there is no ntfs file
    in current_dir.
    calendar is moved to current_dir/grid_calendar
    """
    calendar_file = os.path.join(fixture_dir, 'gridcalendar/export_calendars.zip')

    with open(calendar_file, 'rb') as f:
        coverage_obj.save_grid_calendars(f)

    update_calendars(coverage_obj.id)

    #nothing happens we don't have base data
    assert os.listdir(coverage_obj.technical_conf.output_dir) == []


def test_update_calendar_data_with_last_ntfs(coverage_obj, fixture_dir):
    """
    Test if a calendar file is in input_dir and there is a ntfs file
    in current_dir.llir/grid_calendar and merged with the ntfs file
    and the result is moved to output_dir
    """
    calendar_file = os.path.join(fixture_dir, 'gridcalendar/export_calendars.zip')
    ntfs_path = os.path.join(fixture_dir, 'ntfs/*.txt')

    ntfs_zip = ZipFile(os.path.join(coverage_obj.technical_conf.current_data_dir, 'ntfs.zip'), 'a', ZIP_DEFLATED, False)
    for filename in glob(ntfs_path):
        ntfs_zip.write(filename, os.path.basename(filename))
    ntfs_zip.close()

    with open(calendar_file, 'rb') as f:
        coverage_obj.save_grid_calendars(f)
    update_calendars(coverage_obj.id)

    files_in_output_dir = os.listdir(coverage_obj.technical_conf.output_dir)

    assert files_in_output_dir[0].endswith('database.zip')

    with ZipFile(os.path.join(coverage_obj.technical_conf.output_dir, files_in_output_dir[0])) as new_ntfs_zip:
        files_in_zip = new_ntfs_zip.namelist()
        assert calendar_handler.GRID_CALENDARS in files_in_zip
        assert calendar_handler.GRID_PERIODS in files_in_zip
        assert calendar_handler.GRID_CALENDAR_REL_LINE in files_in_zip

def test_upload_file_ok(coverage_obj, fixture_dir):
    path = os.path.join(fixture_dir, 'geo_data/empty_pbf.osm.pbf')
    with open(path, 'rb') as f:
        file_id = models.save_file_in_gridfs(f, filename='test.osm.pbf')
    with requests_mock.Mocker() as m:
        m.post('http://tyr.prod/v0/instances/test', text='ok')
        send_file(coverage_obj.id, 'production', file_id)
        assert m.called
