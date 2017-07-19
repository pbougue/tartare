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

from zipfile import ZipFile, is_zipfile
import logging
from datetime import datetime, timedelta, date
from typing import List, Tuple
from tartare.exceptions import InvalidFile
import tempfile
import numpy as np


class ValidityPeriodFinder(object):
    #TODO Management of case where the period exceeds one year
    def __init__(self, date_format='%Y%m%d'):
        self.start_date = date.max
        self.end_date = date.min
        self.date_format = date_format

    def start_date_valid(self):
        return self.start_date != date.max

    def end_date_valid(self):
        return self.end_date != date.min

    @property
    def calendar(self) -> str:
        return 'calendar.txt'

    @property
    def calendar_dates(self) -> str:
        return 'calendar_dates.txt'

    @staticmethod
    def _get_data(line: bytes) -> str:
        char_to_delete = ['\r', '\n']
        l = line.decode('utf-8')
        for c in char_to_delete:
            l = l.replace(c, '')

        return l.split(',')

    def _str_date(self, string_date: str) -> datetime:
        return datetime.strptime(string_date, self.date_format).date()

    def datetime64_to_date(self, datetime64: np.datetime64) -> datetime:
        return self._str_date(np.datetime_as_string(datetime64))

    def get_index(self, files_zip: ZipFile, filename: str, column: str) -> int:
        with files_zip.open(filename, 'r') as file:
            for line in file:
                data = self._get_data(line)
                try:
                    return data.index(column)
                except ValueError:
                    msg = 'column name {} is not exist in file {}'.format(column, filename)
                    logging.getLogger(__name__).error(msg)
                    raise InvalidFile(msg)

    def _parse_calendar(self, files_zip: ZipFile):
        header_start = self.get_index(files_zip, self.calendar, 'start_date')
        header_end = self.get_index(files_zip, self.calendar, 'end_date')
        with tempfile.TemporaryDirectory() as tmp_path:
            files_zip.extract(self.calendar, tmp_path)
            try:
                start_dates = np.loadtxt('{}/{}'.format(tmp_path, self.calendar),
                                         delimiter=',',
                                         skiprows=1,
                                         usecols=[header_start],
                                         dtype=np.datetime64)
                end_dates = np.loadtxt('{}/{}'.format(tmp_path, self.calendar),
                                       delimiter=',',
                                       skiprows=1,
                                       usecols=[header_end],
                                       dtype=np.datetime64)
                if not start_dates.size or not end_dates.size:
                    logging.getLogger(__name__).debug('Calendar is empty file')
                    return
            except ValueError as e:
                    msg = 'Impossible to parse file {}, {}'.format(self.calendar, str(e))
                    logging.getLogger(__name__).error(msg)
                    raise InvalidFile(msg)
            self.start_date = self.datetime64_to_date(start_dates.min())
            self.end_date = self.datetime64_to_date(end_dates.max())

    def add_dates(self, dates: np.ndarray, exception_type: np.ndarray):
        add_dates_idx = np.argwhere(exception_type == 1).flatten()
        add_dates = [dates[i] for i in add_dates_idx]
        add_dates.sort()
        for d in add_dates:
            current_date = self.datetime64_to_date(d)
            if self.start_date > current_date:
                self.start_date = current_date
            else:
                break

        for d in add_dates[::-1]:
            current_date = self.datetime64_to_date(d)
            if self.end_date < current_date:
                self.end_date = current_date
            else:
                break

    def remove_dates(self, dates: np.ndarray, exception_type: np.ndarray):
        """
        Removing dates extremities, google does not do it in transitfeed
        https://github.com/google/transitfeed/blob/master/transitfeed/serviceperiod.py#L80
        """
        remove_dates_idx = np.argwhere(exception_type == 2).flatten()

        remove_dates = [dates[i] for i in remove_dates_idx]
        remove_dates.sort()
        for d in remove_dates:
            current_date = self.datetime64_to_date(d)
            if self.start_date == current_date:
                self.start_date = self.start_date + timedelta(days=1)
            else:
                break

        for d in remove_dates[::-1]:
            current_date = self.datetime64_to_date(d)
            if self.end_date == current_date:
                self.end_date = self.end_date - timedelta(days=1)
            else:
                break

    def _parse_calendar_dates(self, files_zip: ZipFile):
        header_date = self.get_index(files_zip, self.calendar_dates, 'date')
        header_exception_type = self.get_index(files_zip, self.calendar_dates, 'exception_type')
        with tempfile.TemporaryDirectory() as tmp_path:
            files_zip.extract(self.calendar_dates, tmp_path)
            try:
                dates = np.loadtxt('{}/{}'.format(tmp_path, self.calendar_dates),
                                   delimiter=',', skiprows=1, usecols=[header_date], dtype=np.datetime64)

                if not dates.size:
                    logging.getLogger(__name__).debug('Calendar_dates is empty file')
                    return
                exception_type = np.loadtxt('{}/{}'.format(tmp_path, self.calendar_dates),
                                            delimiter=',', skiprows=1, usecols=[header_exception_type], dtype=np.int)
            except ValueError as e:
                    msg = 'Impossible to parse file {}, {}'.format(self.calendar_dates, str(e))
                    logging.getLogger(__name__).error(msg)
                    raise InvalidFile(msg)

            self.add_dates(dates, exception_type)
            self.remove_dates(dates, exception_type)

    def get_validity_period(self, file: str) -> Tuple[datetime, datetime]:

        if not is_zipfile(file):
            msg = '{} is not a zip file or not exist.'.format(file)
            logging.getLogger(__name__).error(msg)
            raise InvalidFile(msg)

        with ZipFile(file, 'r') as files_zip:
            if self.calendar not in files_zip.namelist():
                msg = 'file zip {} without calendar.txt'.format(file)
                logging.getLogger(__name__).error(msg)
                raise InvalidFile(msg)

            self._parse_calendar(files_zip)
            if self.calendar_dates in files_zip.namelist():
                self._parse_calendar_dates(files_zip)
        if not self.start_date_valid() or not self.end_date_valid():
            msg = 'Impossible to find validity period'
            logging.getLogger(__name__).error(msg)
            raise InvalidFile(msg)

        return self.start_date, self.end_date
