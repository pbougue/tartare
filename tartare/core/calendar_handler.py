# coding: utf-8

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

from io import StringIO, BytesIO
import csv
from zipfile import ZipFile, ZIP_DEFLATED
from typing import List, Optional, Dict, Iterable
from tartare.helper import get_dict_from_zip

GRID_CALENDARS = "grid_calendars.txt"
GRID_PERIODS = "grid_periods.txt"
GRID_CALENDAR_NETWORK_LINE = "grid_rel_calendar_to_network_and_line.txt"
GRID_CALENDAR_REL_LINE = "grid_rel_calendar_line.txt"


class GridCalendarData(object):
    def __init__(self) -> None:
        self.grid_calendars = []  # type: List[dict]
        self.grid_periods = []  # type: List[dict]
        self.grid_rel_calendar_line = []  # type: List[dict]

    def load_zips(self, calendar_zip: ZipFile, ntfs_zip: ZipFile) -> None:
        file_list = calendar_zip.namelist()
        if GRID_CALENDARS not in file_list \
                and GRID_PERIODS not in file_list \
                and (GRID_CALENDAR_NETWORK_LINE not in file_list or GRID_CALENDAR_REL_LINE not in file_list):
            return

        self.grid_calendars = get_dict_from_zip(calendar_zip, GRID_CALENDARS)
        self.grid_periods = get_dict_from_zip(calendar_zip, GRID_PERIODS)

        if GRID_CALENDAR_REL_LINE not in file_list:
            calendar_lines = get_dict_from_zip(calendar_zip, GRID_CALENDAR_NETWORK_LINE)
            lines = get_dict_from_zip(ntfs_zip, 'lines.txt')
            self.grid_rel_calendar_line = _join_calendar_lines(calendar_lines, lines)
        else:
            self.grid_rel_calendar_line = get_dict_from_zip(calendar_zip, GRID_CALENDAR_REL_LINE)


def dic_to_memory_csv(list_of_dict: List[Dict[str, str]], keys: Optional[Iterable[str]] = None) -> Optional[StringIO]:
    if len(list_of_dict) == 0:
        return None
    if not keys:
        keys = sorted(list_of_dict[0].keys())
    f = StringIO()
    w = csv.DictWriter(f, sorted(keys))
    w.writeheader()
    w.writerows(list_of_dict)
    return f


def _join_calendar_lines(calendar_lines: List[dict], lines: List[dict]) -> list:
    grid_rel_calendar_line = []

    for calendar_line in calendar_lines:
        for line in lines:
            if calendar_line['network_id'] == line['network_id']:
                if not calendar_line.get('line_code') or line['line_code'] == calendar_line['line_code']:
                    grid_rel_calendar_line.append({
                        'grid_calendar_id': calendar_line['grid_calendar_id'],
                        'line_id': line['line_id'],
                    })

    return grid_rel_calendar_line


def merge_calendars_ntfs(grid_calendar_data: GridCalendarData, ntfs_zip: ZipFile) -> ZipFile:
    file_list = [(s, ntfs_zip.read(s)) for s in ntfs_zip.namelist() if not s.startswith('grid_')]
    zip_out = ZipFile(BytesIO(), 'a', ZIP_DEFLATED, False)
    for file_name, content in file_list:
        zip_out.writestr(file_name, content)

    file = dic_to_memory_csv(grid_calendar_data.grid_calendars)
    if file:
        zip_out.writestr(GRID_CALENDARS, file.getvalue())

    file = dic_to_memory_csv(grid_calendar_data.grid_periods)
    if file:
        zip_out.writestr(GRID_PERIODS, file.getvalue())

    file = dic_to_memory_csv(grid_calendar_data.grid_rel_calendar_line)
    if file:
        zip_out.writestr(GRID_CALENDAR_REL_LINE, file.getvalue())

    return zip_out


def save_zip_as_file(zip: ZipFile, filepath: str) -> None:
    file_list = [(s, zip.read(s)) for s in zip.namelist()]
    zip_out = ZipFile(filepath, 'w', ZIP_DEFLATED, False)
    for file_name, content in file_list:
        zip_out.writestr(file_name, content)
    zip_out.close()
