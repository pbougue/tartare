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
from io import BytesIO, StringIO
from tartare.core import calendar_handler
from zipfile import ZipFile, ZIP_DEFLATED


def mock_grid_calendar():
    response = [
        {'grid_calendar_id': 1,
         'name': 'Calendar1',
         'monday': 1,
         'tuesday': 1,
         'wednesday:': 1,
         'thursday': 1,
         'friday': 1,
         'saturday': 1,
         'sunday': 0
         },
        {'grid_calendar_id': 2,
         'name': 'Calendar2',
         'monday': 0,
         'tuesday': 0,
         'wednesday:': 0,
         'thursday': 0,
         'friday': 0,
         'saturday': 1,
         'sunday': 0
         }
    ]
    return response

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
            'network_id': 'network:B',
            'line_code': 3,
        }
    ]

def get_ntfs_zip():
    pwd = os.path.dirname(os.path.dirname(__file__))

    ntfs_path = os.path.join(pwd, 'fixtures/ntfs/*.txt')

    ntfs_zip = ZipFile(BytesIO(), 'a', ZIP_DEFLATED, False)
    ntfs_zip.filename = 'ntfs.zip'
    for filename in glob(ntfs_path):
        with open(filename, 'r') as file:
            ntfs_zip.writestr(os.path.basename(filename), file.read())
    return ntfs_zip

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
