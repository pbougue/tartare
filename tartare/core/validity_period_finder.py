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
from datetime import timedelta, date
from typing import List

from tartare.core.constants import DATA_FORMAT_GTFS, DATA_FORMAT_TITAN
from tartare.core.models import ValidityPeriod
from tartare.core.validity_period_computers import AbstractValidityPeriodComputer, GtfsValidityPeriodComputer, \
    TitanValidityPeriodComputer
from tartare.exceptions import ValidityPeriodException, IntegrityException


class ValidityPeriodFinder:
    @classmethod
    def select_computer_from_data_format(cls, data_format: str) -> AbstractValidityPeriodComputer:
        computers_mapping = {
            DATA_FORMAT_GTFS: GtfsValidityPeriodComputer(),
            DATA_FORMAT_TITAN: TitanValidityPeriodComputer(),
        }
        if data_format not in computers_mapping:
            raise IntegrityException('cannot determine validity period computer for data format {}'.format(data_format))
        return computers_mapping[data_format]

    @classmethod
    def select_computer_and_find(cls, file_name: str, data_format: str = DATA_FORMAT_GTFS) -> ValidityPeriod:
        try:
            computer = cls.select_computer_from_data_format(data_format)
            return computer.compute(file_name)
        except IntegrityException:
            return None

    @classmethod
    def get_validity_period_union(cls, validity_period_list: List[ValidityPeriod],
                                  current_date: date = None) -> ValidityPeriod:
        if not validity_period_list:
            raise ValidityPeriodException('empty validity period list given to calculate union')

        begin_date = min([d.start_date for d in validity_period_list])
        end_date = max([d.end_date for d in validity_period_list])
        now_date = current_date if current_date else date.today()
        if end_date < now_date:
            raise ValidityPeriodException(
                'calculating validity period union on past periods (end_date: {end} < now: {now})'.format(
                    end=end_date.strftime('%d/%m/%Y'), now=current_date.strftime('%d/%m/%Y')))
        if abs(begin_date - end_date).days > 365:
            logging.getLogger(__name__).warning(
                'period bounds for union of validity periods exceed one year')
            begin_date = max(begin_date, now_date - timedelta(days=7))
            end_date = min(begin_date + timedelta(days=364), end_date)
        return ValidityPeriod(begin_date, end_date)
