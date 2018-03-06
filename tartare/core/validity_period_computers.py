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
import logging
from abc import ABCMeta, abstractmethod
from datetime import date, timedelta
from zipfile import is_zipfile

import numpy as np
import pandas as pd
from pandas._libs.tslib import NaTType

from tartare.core.models import ValidityPeriod
from tartare.core.readers import CsvReader
from tartare.exceptions import InvalidFile


class AbstractValidityPeriodComputer(metaclass=ABCMeta):
    @abstractmethod
    def compute(self, file_name: str) -> ValidityPeriod:
        pass

    @classmethod
    def check_zip_file(cls, file_name: str) -> None:
        if not is_zipfile(file_name):
            msg = '{} is not a zip file or not exist'.format(file_name)
            logging.getLogger(__name__).error(msg)
            raise InvalidFile(msg)


class GtfsValidityPeriodComputer(AbstractValidityPeriodComputer):
    feed_info_filename = 'feed_info.txt'
    calendar_file_name = 'calendar.txt'
    calendar_dates_file_name = 'calendar_dates.txt'

    def __init__(self, date_format: str = '%Y%m%d') -> None:
        self.start_date = date.max
        self.end_date = date.min
        self.date_format = date_format
        self.reader = CsvReader()
        self.date_parser = lambda x: pd.to_datetime(x, format=date_format)

    def compute(self, file_name: str) -> ValidityPeriod:
        self.check_zip_file(file_name)

        if not self.reader.file_in_zip_files(file_name, self.calendar_file_name) and \
                not self.reader.file_in_zip_files(file_name, self.calendar_dates_file_name):
            msg = 'file zip {} without at least one of {}'.format(file_name, ','.join(
                [self.calendar_file_name, self.calendar_dates_file_name]))
            logging.getLogger(__name__).error(msg)
            raise InvalidFile(msg)
        if self.reader.file_in_zip_files(file_name, self.feed_info_filename):
            self._parse_feed_info(file_name)
            if self.is_start_date_valid() and self.is_end_date_valid():
                return ValidityPeriod(self.start_date, self.end_date)

        if self.reader.file_in_zip_files(file_name, self.calendar_file_name):
            self._parse_calendar(file_name)

        if self.reader.file_in_zip_files(file_name, self.calendar_dates_file_name):
            self._parse_calendar_dates(file_name)

        if not self.is_start_date_valid() or not self.is_end_date_valid():
            msg = 'impossible to find validity period'
            logging.getLogger(__name__).error(msg)
            raise InvalidFile(msg)
        return ValidityPeriod(self.start_date, self.end_date)

    def is_start_date_valid(self) -> bool:
        return self.start_date != date.max

    def is_end_date_valid(self) -> bool:
        return self.end_date != date.min

    def _parse_calendar(self, files_zip: str) -> None:
        self.reader.load_csv_data_from_zip_file(files_zip, self.calendar_file_name,
                                                usecols=['start_date', 'end_date'],
                                                parse_dates=['start_date', 'end_date'],
                                                date_parser=self.date_parser)

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
        self.reader.load_csv_data_from_zip_file(files_zip, self.calendar_dates_file_name,
                                                usecols=['date', 'exception_type'],
                                                parse_dates=['date'],
                                                date_parser=self.date_parser)

        dates = self.reader.data[(self.reader.data.exception_type == 1)].date.tolist()
        self.add_dates(dates)
        dates = self.reader.data[(self.reader.data.exception_type == 2)].date.tolist()
        self.remove_dates(dates)

    def _parse_feed_info(self, files_zip: str) -> None:
        self.reader.load_csv_data_from_zip_file(files_zip, self.feed_info_filename,
                                                usecols=['feed_start_date', 'feed_end_date'],
                                                parse_dates=['feed_start_date', 'feed_end_date'],
                                                date_parser=self.date_parser)
        if self.reader.count_rows() > 1:
            msg = 'impossible to find validity period, invalid file {}'.format(self.feed_info_filename)
            logging.getLogger(__name__).error(msg)
            raise InvalidFile(msg)

        start_date = self.reader.data.at[0, 'feed_start_date'].date()
        end_date = self.reader.data.at[0, 'feed_end_date'].date()
        # NaTType correspond to an empty column
        self.start_date = start_date if not isinstance(start_date, NaTType) else self.start_date
        self.end_date = end_date if not isinstance(end_date, NaTType) else self.end_date


class TitanValidityPeriodComputer(AbstractValidityPeriodComputer):
    calendar_file_name = 'CALENDRIER_VERSION_LIGNE.txt'

    def __init__(self, date_format: str = '%Y%m%d') -> None:
        self.date_format = date_format
        self.reader = CsvReader()
        self.date_parser = lambda x: pd.to_datetime(x, format=date_format)

    def compute(self, file_name: str) -> ValidityPeriod:
        self.check_zip_file(file_name)
        self.reader = CsvReader()
        if not self.reader.file_in_zip_files(file_name, self.calendar_file_name):
            msg = 'file zip {} without {}'.format(file_name, self.calendar_file_name)
            logging.getLogger(__name__).error(msg)
            raise InvalidFile(msg)
        self.reader.load_csv_data_from_zip_file(file_name, 'CALENDRIER_VERSION_LIGNE.txt', sep=';', header=None,
                                                usecols=[1, 2], parse_dates=['begin_date', 'end_date'],
                                                names=['begin_date', 'end_date'], date_parser=self.date_parser)
        min_begin = self.reader.data['begin_date'].min().date()
        max_end = self.reader.data['end_date'].max().date()
        return ValidityPeriod(min_begin, max_end)
