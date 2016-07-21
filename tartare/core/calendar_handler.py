#coding: utf-8

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
from zipfile import ZipFile
from tartare import app


def handle_calendar(calendar_zip):
    with _last_ntfs_zip() as last_ntfs_zip:
        modified_ntfs = _merge_calendar(calendar_zip, last_ntfs_zip)

    return modified_ntfs


def _merge_calendar(calendar_zip, ntfs_zip):
    with calendar_zip.open('grid_rel_calendar_to_network_and_line.txt') as rel_file:
        print('CALENDAR ZIP FILES:')
        for line in rel_file:
            print(line)

    with ntfs_zip.open('lines.txt') as lines_file:
        print('NTFS LINES ZIP FILES:')
        for line in lines_file:
            print(line)


def _last_ntfs_zip():
    ntfs_filepath = os.path.join(app.config.get("CURRENT_DATA_DIR"), 'ntfs', 'ntfs.zip')
    return ZipFile(ntfs_filepath, 'r')
