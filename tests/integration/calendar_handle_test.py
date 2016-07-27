# coding=utf-8

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

import os
from glob import glob
from io import BytesIO
from tartare.core import calendar_handler
from zipfile import ZipFile, ZIP_DEFLATED
from tartare.core.calendar_handler import GridCalendarData


def get_ntfs_zip():
    pwd = os.path.dirname(os.path.dirname(__file__))

    ntfs_path = os.path.join(pwd, 'fixtures/ntfs/*.txt')

    ntfs_zip = ZipFile(BytesIO(), 'a', ZIP_DEFLATED, False)
    ntfs_zip.filename = 'ntfs.zip'
    for filename in glob(ntfs_path):
        with open(filename, 'r') as file:
            ntfs_zip.writestr(os.path.basename(filename), file.read())
    return ntfs_zip


def get_calendar_zip():
    pwd = os.path.dirname(os.path.dirname(__file__))
    calendar_path = os.path.join(pwd, 'fixtures/gridcalendar/export_calendars.zip')
    return ZipFile(calendar_path, 'r')


def test_merge_calendar_take_all_lines_if_no_line_code():
    calendar_lines = [
        {
            'grid_calendar_id': 1,
            'network_id': 'network:A',
            'line_code': 1,
        },
        {
            'grid_calendar_id': 2,
            'network_id': 'network:A',
            'line_code': '',
        }
    ]

    lines = [
        {
            'line_id': 'l1',
            'network_id': 'network:A',
            'line_code': 1,
        },
        {
            'line_id': 'l2',
            'network_id': 'network:A',
            'line_code': 2,
        },
        {
            'line_id': 'l3',
            'network_id': 'network:A',
            'line_code': 3,
        },
        {
            'line_id': 'l4',
            'network_id': 'network:B',
            'line_code': 4,
        }
    ]

    grid_rel_calendar_line = calendar_handler._join_calendar_lines(calendar_lines, lines)

    assert grid_rel_calendar_line == [
        {
            'grid_calendar_id': 1,
            'line_id': 'l1',
        },
        {
            'grid_calendar_id': 2,
            'line_id': 'l1',
        },
        {
            'grid_calendar_id': 2,
            'line_id': 'l2',
        },
        {
            'grid_calendar_id': 2,
            'line_id': 'l3',
        }
    ]


def test_merge_ntfs_calendar_file():
    ntfs_zip = get_ntfs_zip()
    calendars_zip = get_calendar_zip()
    grid_calendar_data = GridCalendarData()
    grid_calendar_data.load_zips(calendars_zip, ntfs_zip)
    new_ntfs_zip = calendar_handler.merge_calendars_ntfs(grid_calendar_data, ntfs_zip)

    assert calendar_handler.GRID_CALENDARS in new_ntfs_zip.namelist()
    assert calendar_handler.GRID_PERIODS in new_ntfs_zip.namelist()
    assert calendar_handler.GRID_CALENDAR_REL_LINE in new_ntfs_zip.namelist()

    new_ntfs_files = [s for s in new_ntfs_zip.namelist() if not s.startswith('grid_')]
    valid_ntfs = True
    for file in ntfs_zip.namelist():
        valid_ntfs = valid_ntfs and file in new_ntfs_files
    assert valid_ntfs


def test_merge_ntfs_without_calendar_file():
    ntfs_zip = get_ntfs_zip()
    grid_calendar_data = GridCalendarData()
    new_ntfs_zip = calendar_handler.merge_calendars_ntfs(grid_calendar_data, ntfs_zip)

    assert calendar_handler.GRID_CALENDARS not in new_ntfs_zip.namelist()
    assert calendar_handler.GRID_PERIODS not in new_ntfs_zip.namelist()
    assert calendar_handler.GRID_CALENDAR_REL_LINE not in new_ntfs_zip.namelist()

    new_ntfs_files = [s for s in new_ntfs_zip.namelist() if not s.startswith('grid_')]
    valid_ntfs = True
    for file in ntfs_zip.namelist():
        valid_ntfs = valid_ntfs and file in new_ntfs_files
    assert valid_ntfs


def test_merge_ntfs_no_calendar_file():
    ntfs_zip = get_ntfs_zip()
    calendars_zip = ZipFile(BytesIO(), 'a', ZIP_DEFLATED, False)
    calendars_zip.writestr('foo.txt', 'foo')
    grid_calendar_data = GridCalendarData()
    grid_calendar_data.load_zips(calendars_zip, ntfs_zip)
    new_ntfs_zip = calendar_handler.merge_calendars_ntfs(grid_calendar_data, ntfs_zip)

    assert calendar_handler.GRID_CALENDARS not in new_ntfs_zip.namelist()
    assert calendar_handler.GRID_PERIODS not in new_ntfs_zip.namelist()
    assert calendar_handler.GRID_CALENDAR_REL_LINE not in new_ntfs_zip.namelist()

    new_ntfs_files = [s for s in new_ntfs_zip.namelist() if not s.startswith('grid_')]
    valid_ntfs = True
    for file in ntfs_zip.namelist():
        valid_ntfs = valid_ntfs and file in new_ntfs_files
    assert valid_ntfs
