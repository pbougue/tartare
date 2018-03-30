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

from tartare.core.constants import DATA_FORMAT_GTFS, DATA_FORMAT_TITAN, DATA_FORMAT_OBITI, DATA_FORMAT_NEPTUNE
from tartare.core.models import ValidityPeriod
from tartare.core.validity_period_computers import AbstractValidityPeriodComputer, GtfsValidityPeriodComputer, \
    TitanValidityPeriodComputer, ObitiValidityPeriodComputer, NeptuneValidityPeriodComputer
from tartare.exceptions import ValidityPeriodException, IntegrityException


class ValidityPeriodFinder:
    @classmethod
    def get_data_format_with_validity(cls) -> List[str]:
        return list(cls.get_computers_mapping().keys())

    @classmethod
    def get_computers_mapping(cls) -> dict:
        return {
            DATA_FORMAT_GTFS: GtfsValidityPeriodComputer(),
            DATA_FORMAT_TITAN: TitanValidityPeriodComputer(),
            DATA_FORMAT_OBITI: ObitiValidityPeriodComputer(),
            DATA_FORMAT_NEPTUNE: NeptuneValidityPeriodComputer(),
        }

    @classmethod
    def select_computer_from_data_format(cls, data_format: str) -> AbstractValidityPeriodComputer:
        computers_mapping = cls.get_computers_mapping()
        cls.get_data_format_with_validity()
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
