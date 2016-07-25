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
from io import StringIO
import csv
from zipfile import ZipFile
from tartare import app


def handle_calendar(calendar_zip):
    with _last_ntfs_zip() as last_ntfs_zip:
        modified_ntfs = _merge_calendar(calendar_zip, last_ntfs_zip)

    return modified_ntfs


def _merge_calendar(calendar_zip, ntfs_zip):
    grid_calendar_data = GridCalendarData()
    grid_calendar_data.load_zips(calendar_zip, ntfs_zip)
    grid_calendar_data.update_ntfs()
    grid_calendar_data.save_as_file()


def _last_ntfs_zip():
    ntfs_filepath = os.path.join(app.config.get("CURRENT_DATA_DIR"), 'ntfs', 'ntfs.zip')
    return ZipFile(ntfs_filepath, 'r')


def _write_csv(csv, pathfile):
    pass


class GridCalendarData:
    def __init__(self):
        self.grid_calendars_csv = []
        self.grid_periods_csv = []
        self.grid_rel_calendar_line_csv = []

    """
    Load zip and fill arrays,
    and join calendar lines
    """
    def load_zips(self, calendar_zip, ntfs_zip):
        calendar_lines = []
        lines = []
        grid_rel_calendar_line = []

        with calendar_zip.open('grid_rel_calendar_to_network_and_line.txt') as grid_calendar:
            for line in csv.DictReader(grid_calendar):
                calendar_lines.append(line)

        with ntfs_zip.open('lines.txt', 'r') as grid_lines:
            for line in csv.DictReader(grid_lines):
                lines.append(line)

        for calendar_line in calendar_lines:
            for line in lines:
                if calendar_line['network_id'] == line['network_id']:
                    if '' == calendar_line['line_code'] or line['line_code'] == calendar_line['line_code']:
                        grid_rel_calendar_line.append({
                            'grid_calendar_id': calendar_line['grid_calendar_id'],
                            'line_id': line['line_id'],
                        })


    """
    Replace calendar file in ntfs
    """
    def update_ntfs(self):
        pass


    """
    Save to updated ntfs file
    """
    def save_as_file(self):
        pass
