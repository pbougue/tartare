import os
from glob import glob
from shutil import copy
from zipfile import ZipFile, ZIP_DEFLATED
from tartare.tasks import handle_data
from tartare.core import calendar_handler


def test_handle_not_ntfs_data(tmpdir):
    """
    Test if a file which is not an ntfs file is moved to output_dir
    """
    input = tmpdir.mkdir('input')
    input_file = input.join('bob.txt')
    input_file.write("bob ?")
    output = tmpdir.mkdir('output')
    current_dir = tmpdir.mkdir('current_dir')

    handle_data(str(input), str(output), str(current_dir))
    files_in_output_dir = os.listdir(str(output))

    assert files_in_output_dir[0].endswith('bob.txt')


def test_handle_ntfs_data_without_calendar(tmpdir):
    """
    Test if a ntfs file is copied to current_dir
    and moved to output_dir when there is no calendar
    """
    input = tmpdir.mkdir('input')
    input_file = input.join('contributors.txt')
    input_file.write("bob ?")
    output = tmpdir.mkdir('output')
    current_dir = tmpdir.mkdir('current_dir')

    handle_data(str(input), str(output), str(current_dir))

    files_in_output_dir = os.listdir(str(output))

    assert files_in_output_dir[0].endswith('database.zip')
    assert os.path.isfile(str(current_dir.join('contributors.txt')))


def test_handle_ntfs_data_with_calendar(tmpdir):
    """
    Test if a ntfs file is copied to current_dir and merged
    with an existing calendar and moved to current_dir
    """
    input = tmpdir.mkdir('input')

    pwd = os.path.dirname(os.path.dirname(__file__))
    ntfs_path = os.path.join(pwd, 'fixtures/ntfs/*.txt')

    ntfs_zip = ZipFile(os.path.join(str(input), 'ntfs.zip'), 'a', ZIP_DEFLATED, False)
    for filename in glob(ntfs_path):
        ntfs_zip.write(filename, os.path.basename(filename))
    ntfs_zip.close()

    output = tmpdir.mkdir('output')
    current_dir = tmpdir.mkdir('current_dir')
    calendar_dir = current_dir.mkdir('grid_calendar')
    calendar_file = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                 'fixtures/gridcalendar/export_calendars.zip')
    copy(calendar_file, str(calendar_dir))

    handle_data(str(input), str(output), str(current_dir))

    files_in_output_dir = os.listdir(str(output))

    assert files_in_output_dir[0].endswith('database.zip')
    assert os.path.isfile(str(current_dir.join('ntfs.zip')))

    with ZipFile(str(output.join(files_in_output_dir[0]))) as new_ntfs_zip:
        files_in_zip = new_ntfs_zip.namelist()
        assert calendar_handler.GRID_CALENDARS in files_in_zip
        assert calendar_handler.GRID_PERIODS in files_in_zip
        assert calendar_handler.GRID_CALENDAR_REL_LINE in files_in_zip


def test_handle_calendar_data_without_ntfs(tmpdir):
    """
    Test if a calendar file is in input_dir and there is no ntfs file
    in current_dir.
    calendar is moved to current_dir/grid_calendar
    """
    input = tmpdir.mkdir('input')
    calendar_file = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                 'fixtures/gridcalendar/export_calendars.zip')
    copy(calendar_file, str(input))
    output = tmpdir.mkdir('output')
    current_dir = tmpdir.mkdir('current_dir')

    handle_data(str(input), str(output), str(current_dir))

    assert os.path.isfile(str(current_dir.join('grid_calendar').join('export_calendars.zip')))
    assert not os.path.isfile(str(output.join('export_calendars.zip')))


def test_handle_calendar_data_with_last_ntfs(tmpdir):
    """
    Test if a calendar file is in input_dir and there is a ntfs file
    in current_dir.llir/grid_calendar and merged with the ntfs file
    and the result is moved to output_dir
    """
    input = tmpdir.mkdir('input')
    calendar_file = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                 'fixtures/gridcalendar/export_calendars.zip')
    copy(calendar_file, str(input))
    output = tmpdir.mkdir('output')
    current_dir = tmpdir.mkdir('current_dir')
    pwd = os.path.dirname(os.path.dirname(__file__))
    ntfs_path = os.path.join(pwd, 'fixtures/ntfs/*.txt')

    ntfs_zip = ZipFile(os.path.join(str(current_dir), 'ntfs.zip'), 'a', ZIP_DEFLATED, False)
    for filename in glob(ntfs_path):
        ntfs_zip.write(filename, os.path.basename(filename))
    ntfs_zip.close()

    handle_data(str(input), str(output), str(current_dir))

    files_in_output_dir = os.listdir(str(output))

    assert files_in_output_dir[0].endswith('database.zip')
    assert os.path.isfile(str(current_dir.join('grid_calendar').join('export_calendars.zip')))

    with ZipFile(str(output.join(files_in_output_dir[0]))) as new_ntfs_zip:
        files_in_zip = new_ntfs_zip.namelist()
        assert calendar_handler.GRID_CALENDARS in files_in_zip
        assert calendar_handler.GRID_PERIODS in files_in_zip
        assert calendar_handler.GRID_CALENDAR_REL_LINE in files_in_zip
