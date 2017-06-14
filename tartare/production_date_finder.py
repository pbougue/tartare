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

from zipfile import ZipFile
from datetime import date
import logging
from datetime import datetime
import os
import zipfile
from tartare.exceptions import FileNotFound, InvalidFile


class ProductionDateFinder(object):
    #TODO Management of case where the period exceeds one year
    def __init__(self, date_format='%Y%m%d'):
        self.start_date = date.max
        self.end_date = date.min
        self.date_format = date_format

    @staticmethod
    def _get_data(line):
        char_to_delate = ['\r', '\n']
        l = line.decode('utf-8')
        for c in char_to_delate:
            l = l.replace(c, '')

        return l.split(',')

    def _str_date(self, string_date):
        return datetime.strptime(string_date, self.date_format).date()

    @staticmethod
    def get_index(filename, headers, column):
        try:
            return headers.index(column)
        except Exception as e:
            msg = 'column name {} is not exist in file {}'.format(column, filename)
            logging.getLogger(__name__).error(msg)
            raise InvalidFile(msg)

    def _parse_calendar(self, files_zip):
        filename = 'calendar.txt'
        with files_zip.open(filename, ) as file:
            header_start = None
            header_end = None
            for line in file:
                data = self._get_data(line)
                if not header_start:
                    header_start = self.get_index(filename, data, 'start_date')
                    header_end = self.get_index(filename, data, 'end_date')
                    continue
                if self.start_date > self._str_date(data[header_start]):
                    self.start_date = self._str_date(data[header_start])
                if self.end_date < self._str_date(data[header_end]):
                    self.end_date = self._str_date(data[header_end])

    def _parse_calendar_dates(self, files_zip):
        with files_zip.open('calendar_dates.txt', ) as file:
            header_date = None
            for line in file:
                data = self._get_data(line)
                if not header_date:
                    header_date = data.index('date')
                    continue
                if self.start_date > self._str_date(data[header_date]):
                    self.start_date = self._str_date(data[header_date])
                if self.end_date < self._str_date(data[header_date]):
                    self.end_date = self._str_date(data[header_date])

    @staticmethod
    def _check_zip_file(file):
        if not os.path.exists(file):
            msg = "File {} not found".format(file)
            logging.getLogger(__name__).error(msg)
            raise FileNotFound(msg)

        if not zipfile.is_zipfile(file):
            msg = '{} is not a zip file'.format(file)
            logging.getLogger(__name__).error(msg)
            raise InvalidFile(msg)

    def get_production_date(self, file):

        self._check_zip_file(file)
        map_file_func = {
            'calendar.txt': self._parse_calendar,
            'calendar_dates.txt': self._parse_calendar_dates
        }
        with ZipFile(file, 'r') as files_zip:
            file_list = [s for s in files_zip.namelist() if s.startswith('calendar')]
            if not file_list:
                msg = 'file zip {} without calendar.'.format(file)
                logging.getLogger(__name__).error(msg)
                raise InvalidFile(msg)
            for f in file_list:
                map_file_func.get(f)(files_zip)
        return self.start_date, self.end_date