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
import calendar
import logging
import tempfile
from abc import ABCMeta, abstractmethod
from datetime import date, timedelta, datetime
from typing import List, Optional, Union, BinaryIO
from xml.etree import ElementTree
from zipfile import is_zipfile, ZipFile

import numpy as np
import pandas as pd
from pandas._libs.tslib import NaTType

from tartare.core.models import ValidityPeriod
from tartare.core.readers import CsvReader
from tartare.exceptions import InvalidFile


class AbstractValidityPeriodComputer(metaclass=ABCMeta):
    def __init__(self, date_format: str = '%Y%m%d') -> None:
        self.date_format = date_format

    @abstractmethod
    def compute(self, file_name: Union[str, BinaryIO]) -> ValidityPeriod:
        pass

    @classmethod
    def check_zip_file(cls, file_name: Union[str, BinaryIO]) -> None:
        if not is_zipfile(file_name):
            msg = '{} is not a zip file or not exist'.format(file_name)
            logging.getLogger(__name__).error(msg)
            raise InvalidFile(msg)


class ValidityPeriodFromCsvComputer(AbstractValidityPeriodComputer):
    def compute(self, file_name: Union[str, BinaryIO]) -> ValidityPeriod:
        pass

    def __init__(self, date_format: str = '%Y%m%d') -> None:
        super().__init__(date_format)
        self.reader = CsvReader()
        self.date_parser = lambda x: pd.to_datetime(x, format=date_format)


class GtfsValidityPeriodComputer(ValidityPeriodFromCsvComputer):
    feed_info_filename = 'feed_info.txt'
    calendar_file_name = 'calendar.txt'
    calendar_dates_file_name = 'calendar_dates.txt'

    def __init__(self) -> None:
        super().__init__()
        self.start_date = date.max
        self.end_date = date.min

    def compute(self, file_name: Union[str, BinaryIO]) -> ValidityPeriod:
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

    def _parse_calendar(self, files_zip: Union[str, BinaryIO]) -> None:
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

    def _parse_calendar_dates(self, files_zip: Union[str, BinaryIO]) -> None:
        self.reader.load_csv_data_from_zip_file(files_zip, self.calendar_dates_file_name,
                                                usecols=['date', 'exception_type'],
                                                parse_dates=['date'],
                                                date_parser=self.date_parser)

        dates = self.reader.data[(self.reader.data.exception_type == 1)].date.tolist()
        self.add_dates(dates)
        dates = self.reader.data[(self.reader.data.exception_type == 2)].date.tolist()
        self.remove_dates(dates)

    def _parse_feed_info(self, files_zip: Union[str, BinaryIO]) -> None:
        try:
            self.reader.load_csv_data_from_zip_file(files_zip, self.feed_info_filename,
                                                    usecols=['feed_start_date', 'feed_end_date'],
                                                    parse_dates=['feed_start_date', 'feed_end_date'],
                                                    date_parser=self.date_parser)
        except InvalidFile as exc:
            logging.getLogger(__name__).warning(str(exc))
            return

        if self.reader.count_rows() > 1:
            msg = 'impossible to find validity period, file {} has more than 1 row'.format(self.feed_info_filename)
            logging.getLogger(__name__).error(msg)
            raise InvalidFile(msg)

        start_date = self.reader.data.at[0, 'feed_start_date'].date()
        end_date = self.reader.data.at[0, 'feed_end_date'].date()
        # NaTType correspond to an empty column
        self.start_date = start_date if not isinstance(start_date, NaTType) else self.start_date
        self.end_date = end_date if not isinstance(end_date, NaTType) else self.end_date


class TitanValidityPeriodComputer(ValidityPeriodFromCsvComputer):
    calendar_file_name = 'CALENDRIER_VERSION_LIGNE.txt'

    def __init__(self) -> None:
        super().__init__()

    def compute(self, file_name: Union[str, BinaryIO]) -> ValidityPeriod:
        self.check_zip_file(file_name)
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


class ObitiValidityPeriodComputer(ValidityPeriodFromCsvComputer):
    vehicule_journey_file = 'vehiclejourney.csv'
    periode_file = 'periode.csv'
    validity_pattern_file = 'validitypattern.csv'
    separator = ';'

    def __init__(self) -> None:
        super().__init__('%d/%m/%Y')

    def __check_file_exists_and_return_right_case(self, zip_file: Union[str, BinaryIO], file_to_check: str) -> str:
        if not self.reader.file_in_zip_files(zip_file, file_to_check):
            if not self.reader.file_in_zip_files(zip_file, file_to_check.upper()):
                msg = 'file zip {} without {}'.format(zip_file, file_to_check)
                logging.getLogger(__name__).error(msg)
                raise InvalidFile(msg)
            else:
                file_to_check = file_to_check.upper()
        return file_to_check

    def compute(self, file_name: Union[str, BinaryIO]) -> ValidityPeriod:
        self.check_zip_file(file_name)
        vehicule_journey_file = self.__check_file_exists_and_return_right_case(file_name, self.vehicule_journey_file)

        self.reader.load_csv_data_from_zip_file(file_name, vehicule_journey_file, sep=self.separator, encoding='latin1')
        id_regime_list = [int(id_regime) for id_regime in set(self.reader.data['IDREGIME'].dropna().tolist()) if
                          id_regime != -1]
        id_periode_list = [int(id_periode) for id_periode in set(self.reader.data['IDPERIODE'].dropna().tolist()) if
                           id_periode != -1]
        validity_periods = []
        if id_periode_list:
            periode_file = self.__check_file_exists_and_return_right_case(file_name, self.periode_file)
            self.reader.load_csv_data_from_zip_file(file_name, periode_file, sep=self.separator, encoding='latin1',
                                                    parse_dates=['DDEBUT', 'DFIN'], date_parser=self.date_parser)
            self.reader.data = self.reader.data[self.reader.data['IDPERIODE'].isin(id_periode_list)]
            validity_periods.append(
                ValidityPeriod(self.reader.data['DDEBUT'].min().date(), self.reader.data['DFIN'].max().date()))
        if id_regime_list:
            validity_pattern_file = self.__check_file_exists_and_return_right_case(file_name,
                                                                                   self.validity_pattern_file)
            self.reader.load_csv_data_from_zip_file(file_name, validity_pattern_file, sep=self.separator,
                                                    parse_dates=['DDEBUT'], date_parser=self.date_parser,
                                                    encoding='latin1')
            self.reader.data = self.reader.data[self.reader.data['IDREGIME'].isin(id_regime_list)]
            for regime_row in self.reader.data.to_dict('records'):
                period_bits = regime_row['J_ACTIF1'] + regime_row['J_ACTIF2']
                try:
                    start_date = regime_row['DDEBUT'].date() + timedelta(days=period_bits.index('1'))
                    end_date = regime_row['DDEBUT'].date() + timedelta(days=period_bits.rindex('1'))
                    validity_periods.append(ValidityPeriod(start_date, end_date))
                except ValueError as err:
                    msg = 'skipping line: file {} for IDREGIME={} does not contain any bits set to 1, error: {}'.format(
                        validity_pattern_file, regime_row['IDREGIME'], err)
                    logging.getLogger(__name__).warning(msg)

        return ValidityPeriod.union(validity_periods)


class NeptuneValidityPeriodComputer(AbstractValidityPeriodComputer):
    def __init__(self) -> None:
        super().__init__('%Y-%m-%d')

    @classmethod
    def __change_day_until_weekday_reached(cls, period_date: date, weekdays: List[int], nb_days: int) -> date:
        while period_date.weekday() not in weekdays:
            period_date += timedelta(days=nb_days)
        return period_date

    def __parse_xml_file_into_unique_validity_period(self, xml_file_name: str) -> Optional[ValidityPeriod]:
        try:
            root = ElementTree.parse(xml_file_name).getroot()
            namespace = root.tag.replace('ChouettePTNetwork', '')
            validity_periods = []
            for time_table in root.iter('{}Timetable'.format(namespace)):
                for period in time_table.iter('{}period'.format(namespace)):
                    if period:
                        start_period = datetime.strptime(period.find('{}startOfPeriod'.format(namespace)).text,
                                                         self.date_format).date()
                        end_period = datetime.strptime(period.find('{}endOfPeriod'.format(namespace)).text,
                                                       self.date_format).date()
                        if start_period and end_period:
                            day_types = [list(calendar.day_name).index(day_type.text) for day_type in
                                         time_table.findall('{}dayType'.format(namespace))]
                            start_period = self.__change_day_until_weekday_reached(start_period, day_types, 1)
                            end_period = self.__change_day_until_weekday_reached(end_period, day_types, -1)
                            validity_periods.append(ValidityPeriod(start_period, end_period))
            return ValidityPeriod.union(validity_periods) if validity_periods else None
        except (ElementTree.ParseError, TypeError) as e:
            raise InvalidFile("invalid xml {}, error: {}".format(xml_file_name, str(e)))

    def compute(self, file_name: Union[str, BinaryIO]) -> ValidityPeriod:
        self.check_zip_file(file_name)
        validity_periods = []
        with ZipFile(file_name, 'r') as files_zip, tempfile.TemporaryDirectory() as tmp_path:
            if not any(one_file_in_zip.endswith('.xml') for one_file_in_zip in files_zip.namelist()):
                raise InvalidFile('file zip {} without at least one xml'.format(file_name))
            files_zip.extractall(tmp_path)
            for file_in_zip in files_zip.namelist():
                if file_in_zip.endswith('.xml'):
                    validity_period = self.__parse_xml_file_into_unique_validity_period(
                        '{}/{}'.format(tmp_path, file_in_zip))
                    if validity_period:
                        validity_periods.append(validity_period)
        return ValidityPeriod.union(validity_periods)
