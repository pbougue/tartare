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
import tempfile
import numpy as np


class ProductionDateFinder(object):
    #TODO Management of case where the period exceeds one year
    def __init__(self, start_date=date.max, end_date=date.min, date_format='%Y%m%d'):
        self.start_date = start_date
        self.end_date = end_date
        self.date_format = date_format

    @property
    def calendar(self):
        return 'calendar.txt'

    @property
    def calendar_dates(self):
        return 'calendar_dates.txt'

    @staticmethod
    def _get_data(line):
        char_to_delate = ['\r', '\n']
        l = line.decode('utf-8')
        for c in char_to_delate:
            l = l.replace(c, '')

        return l.split(',')

    def _str_date(self, string_date):
        return datetime.strptime(string_date, self.date_format).date()

    def datetime64_to_date(self, datetime64):
        return self._str_date(np.datetime_as_string(datetime64))

    def get_index(self, files_zip, filename, column):
        with files_zip.open(filename, 'r') as file:
            for line in file:
                data = self._get_data(line)
                try:
                    return data.index(column)
                except Exception:
                    msg = 'column name {} is not exist in file {}'.format(column, filename)
                    logging.getLogger(__name__).error(msg)
                    raise InvalidFile(msg)

    def _parse_calendar(self, files_zip):
        header_start = self.get_index(files_zip, self.calendar, 'start_date')
        header_end = self.get_index(files_zip, self.calendar, 'end_date')
        with tempfile.TemporaryDirectory() as tmp_path:
            files_zip.extract(self.calendar, tmp_path)
            start_dates, end_dates = np.loadtxt('{}/{}'.format(tmp_path, self.calendar),
                                                delimiter=',',
                                                skiprows=1,
                                                usecols=[header_start, header_end],
                                                dtype=np.datetime64)

            self.start_date = self.datetime64_to_date(start_dates.min())
            self.end_date = self.datetime64_to_date(end_dates.max())

    def _parse_calendar_dates(self, files_zip):
        header_date = self.get_index(files_zip, self.calendar_dates, 'date')
        with tempfile.TemporaryDirectory() as tmp_path:
            files_zip.extract(self.calendar_dates, tmp_path)
            dates = np.loadtxt('{}/{}'.format(tmp_path, self.calendar_dates),
                               delimiter=',',
                               skiprows=1,
                               usecols=[header_date],
                               dtype=np.datetime64)

            if self.start_date > dates.min():
                self.start_date = dates.min()
            if self.end_date < dates.max():
                self.end_date = dates.min()

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
