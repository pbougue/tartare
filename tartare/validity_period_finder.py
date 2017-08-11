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

from zipfile import is_zipfile
import logging
from datetime import timedelta, date
from typing import Tuple
from tartare.exceptions import InvalidFile
import numpy as np
from tartare.core.csv_reader import CsvReader
import pandas as pd


class ValidityPeriodFinder(object):
    feed_info_filename = 'feed_info.txt'
    calendar_filename = 'calendar.txt'
    calendar_dates_filename = 'calendar_dates.txt'

    # TODO Management of case where the period exceeds one year
    def __init__(self, date_format: str='%Y%m%d') -> None:
        self.start_date = date.max
        self.end_date = date.min
        self.date_format = date_format
        self.reader = CsvReader()

    def is_start_date_valid(self) -> bool:
        return self.start_date != date.max

    def is_end_date_valid(self) -> bool:
        return self.end_date != date.min

    def _parse_calendar(self, files_zip: str) -> None:
        self.reader.load_data(files_zip, self.calendar_filename,
                              usecols=['start_date', 'end_date'], parse_dates=['start_date', 'end_date'],
                              date_parser=lambda x: pd.to_datetime(x, format='%Y%m%d'))

        if self.reader.count_rows():
            self.start_date = self.reader.get_min('start_date').date()
            self.end_date = self.reader.get_max('end_date').date()

    def add_dates(self, dates: np.ndarray) -> None:
        dates.sort()
        for d in dates:
            current_date = d.date()
            if self.start_date > current_date:
                self.start_date = current_date
            else:
                break

        for d in dates[::-1]:
            current_date = d.date()
            if self.end_date < current_date:
                self.end_date = current_date
            else:
                break

    def remove_dates(self, dates: np.ndarray) -> None:
        """
        Removing dates extremities, google does not do it in transitfeed
        https://github.com/google/transitfeed/blob/master/transitfeed/serviceperiod.py#L80
        """
        dates.sort()
        for d in dates:
            current_date = d.date()
            if self.start_date == current_date:
                self.start_date = self.start_date + timedelta(days=1)
            else:
                break

        for d in dates[::-1]:
            current_date = d.date()
            if self.end_date == current_date:
                self.end_date = self.end_date - timedelta(days=1)
            else:
                break

    def _parse_calendar_dates(self, files_zip: str) -> None:
        self.reader.load_data(files_zip, self.calendar_dates_filename,
                              usecols=['date', 'exception_type'],
                              parse_dates=['date'],
                              date_parser=lambda x: pd.to_datetime(x, format='%Y%m%d'))

        dates = self.reader.data[(self.reader.data.exception_type == 1)].date.tolist()
        self.add_dates(dates)
        dates = self.reader.data[(self.reader.data.exception_type == 2)].date.tolist()
        self.remove_dates(dates)

    def get_validity_period(self, file: str) -> Tuple[date, date]:

        if not is_zipfile(file):
            msg = '{} is not a zip file or not exist.'.format(file)
            logging.getLogger(__name__).error(msg)
            raise InvalidFile(msg)

        if not self.reader.file_in_zip_files(file, self.calendar_filename) and \
                not self.reader.file_in_zip_files(file, self.calendar_dates_filename):
                msg = 'file zip {} without at least one of {}'.format(file, ','.join(
                    [self.calendar_filename, self.calendar_dates_filename]))
                logging.getLogger(__name__).error(msg)
                raise InvalidFile(msg)
        if self.reader.file_in_zip_files(file, self.feed_info_filename):
            try:
                self._parse_feed_info(file)
                if self.is_start_date_valid() and self.is_end_date_valid():
                    return self.start_date, self.end_date
            except (ValueError, InvalidFile):
                pass

        if self.reader.file_in_zip_files(file, self.calendar_filename):
            self._parse_calendar(file)

        if self.reader.file_in_zip_files(file, self.calendar_dates_filename):
            self._parse_calendar_dates(file)

        if not self.is_start_date_valid() or not self.is_end_date_valid():
            msg = 'Impossible to find validity period'
            logging.getLogger(__name__).error(msg)
            raise InvalidFile(msg)
        return self.start_date, self.end_date

    def _parse_feed_info(self, files_zip: str) -> None:
        self.reader.load_data(files_zip, self.feed_info_filename,
                              usecols=['feed_start_date', 'feed_end_date'],
                              parse_dates=['feed_start_date', 'feed_end_date'],
                              date_parser=lambda x: pd.to_datetime(x, format='%Y%m%d'))

        self.start_date = self.reader.data.at[0, 'feed_start_date'].date()
        self.end_date = self.reader.data.at[0, 'feed_end_date'].date()
