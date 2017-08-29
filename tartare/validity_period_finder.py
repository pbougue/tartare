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
from datetime import timedelta, date, datetime
from typing import Tuple, List
import numpy as np
from pandas._libs.tslib import NaTType

from tartare.core.csv_reader import CsvReader
import pandas as pd

from tartare.core.models import ValidityPeriod, ValidityPeriodContainer
from tartare.exceptions import InvalidFile, ValidityPeriodException

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
        self.reader.load_csv_data_from_zip_file(files_zip, self.calendar_filename,
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
        self.reader.load_csv_data_from_zip_file(files_zip, self.calendar_dates_filename,
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
            self._parse_feed_info(file)
            if self.is_start_date_valid() and self.is_end_date_valid():
                return self.start_date, self.end_date

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
        self.reader.load_csv_data_from_zip_file(files_zip, self.feed_info_filename,
                              usecols=['feed_start_date', 'feed_end_date'],
                              parse_dates=['feed_start_date', 'feed_end_date'],
                              date_parser=lambda x: pd.to_datetime(x, format='%Y%m%d'))
        if self.reader.count_rows() > 1:
            msg = 'Impossible to find validity period, invalid file {}.'.format(self.feed_info_filename)
            logging.getLogger(__name__).error(msg)
            raise InvalidFile(msg)

        start_date = self.reader.data.at[0, 'feed_start_date'].date()
        end_date = self.reader.data.at[0, 'feed_end_date'].date()
        # NaTType correspond to an empty column
        self.start_date = start_date if not isinstance(start_date, NaTType) else self.start_date
        self.end_date = end_date if not isinstance(end_date, NaTType) else self.end_date

    @classmethod
    def get_validity_period_union(self,
                                  validity_period_container_list: List[ValidityPeriodContainer]) -> ValidityPeriod:
        if not validity_period_container_list:
            raise ValidityPeriodException('empty validity period list given to calculate union')
        container_with_min_start_date = min(validity_period_container_list,
                                            key=lambda container: container.validity_period.start_date)

        container_with_max_end_date = max(validity_period_container_list,
                                          key=lambda container: container.validity_period.end_date)
        begin_date = container_with_min_start_date.validity_period.start_date
        end_date = container_with_max_end_date.validity_period.end_date
        now_date = datetime.now().date()
        if end_date < now_date:
            raise ValidityPeriodException(
                'calculating validity period union on past periods (end_date: {end} < now: {now})'.format(
                    end=end_date.strftime('%d/%m/%Y'), now=now_date.strftime('%d/%m/%Y')))
        if abs(begin_date - end_date).days > 365:
            logging.getLogger(__name__).warning(
                'period bounds for union of validity periods exceed one year')
            begin_date = max(begin_date, now_date)
            end_date = min(begin_date + timedelta(days=364), end_date)
        return ValidityPeriod(begin_date, end_date)
