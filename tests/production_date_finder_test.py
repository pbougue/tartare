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

from tartare.production_date_finder import ProductionDateFinder
import os
from datetime import date
import pytest
from tartare.exceptions import FileNotFound, InvalidFile


current_path = '{}/{}/'.format(os.path.dirname(os.path.dirname(__file__)), 'tests/fixtures')


def test_zip_file_only_calendar():
    finder = ProductionDateFinder()
    file = '{}/{}'.format(current_path, '/gtfs/some_archive.zip')
    start_date, end_date = finder.get_production_date(file)
    assert start_date == date(2015, 3, 25)
    assert end_date == date(2015, 8, 26)


def test_get_production_date_zip_file_invalid():
    finder = ProductionDateFinder()
    file = '{}/{}'.format(current_path, '/gtfs/bob.zip')
    with pytest.raises(FileNotFound) as excinfo:
            finder.get_production_date(file)
    assert str(excinfo.value) == "File {} not found".format(file)


def test_get_production_date_not_zipfile():
    finder = ProductionDateFinder()
    file = '{}/{}'.format(current_path, '/ntfs/calendar.txt')
    with pytest.raises(InvalidFile) as excinfo:
            finder.get_production_date(file)
    assert str(excinfo.value) == "{} is not a zip file".format(file)


def test_calendar_without_end_date_column():
    finder = ProductionDateFinder()
    file = '{}/{}'.format(current_path, '/production_date/calendar_without_end_date.zip')
    with pytest.raises(InvalidFile) as excinfo:
            finder.get_production_date(file)
    assert str(excinfo.value) == "column name end_date is not exist in file calendar.txt".format(file)


def test_calendar_without_start_date_column():
    finder = ProductionDateFinder()
    file = '{}/{}'.format(current_path, '/production_date/calendar_without_start_date.zip')
    with pytest.raises(InvalidFile) as excinfo:
            finder.get_production_date(file)
    assert str(excinfo.value) == "column name start_date is not exist in file calendar.txt".format(file)


def test_gtfs_without_calendar():
    finder = ProductionDateFinder()
    file = '{}/{}'.format(current_path, '/production_date/gtfs_without_calendar.zip')
    with pytest.raises(InvalidFile) as excinfo:
            finder.get_production_date(file)
    assert str(excinfo.value) == "file zip {} without calendar.txt".format(file)


def test_calendar_with_not_date():
    finder = ProductionDateFinder()
    file = '{}/{}'.format(current_path, '/production_date/calendar_invalid_end_date.zip')
    with pytest.raises(InvalidFile) as excinfo:
            finder.get_production_date(file)
    assert str(excinfo.value) == 'Impossible to parse file calendar.txt, Error ' \
                                 'parsing datetime string "AAAA" at position 0'


def test_calendar_dates_without_exception_type():
    finder = ProductionDateFinder()
    file = '{}/{}'.format(current_path, '/production_date/calendar_dates_without_exception_type.zip')
    with pytest.raises(InvalidFile) as excinfo:
            finder.get_production_date(file)
    assert str(excinfo.value) == 'column name exception_type is not exist in file calendar_dates.txt'


def test_calendar_dates_without_exception_type():
    finder = ProductionDateFinder()
    file = '{}/{}'.format(current_path, '/production_date/calendar_dates_without_dates.zip')
    with pytest.raises(InvalidFile) as excinfo:
            finder.get_production_date(file)
    assert str(excinfo.value) == 'column name date is not exist in file calendar_dates.txt'


def test_add_dates():
    """
        calendar.txt   :     20170102                    20170131
                                *--------------------------*
        calendar_dates :
                add dates : 20170101 and 20170215

                production date : 20170101 to 20170215
    """
    finder = ProductionDateFinder()
    file = '{}/{}'.format(current_path, '/production_date/add_dates.zip')
    start_date, end_date = finder.get_production_date(file)
    assert start_date == date(2017, 1, 1)
    assert end_date == date(2017, 2, 15)



def test_remove_dates():
    """
        calendar.txt   :     20170102                    20170131
                                *--------------------------*
        calendar_dates :
                remove dates : 20170102, 20170103, 20170115 and 20170131

                production date : 20170104 to 20170130
    """
    finder = ProductionDateFinder()
    file = '{}/{}'.format(current_path, '/production_date/remove_dates.zip')
    start_date, end_date = finder.get_production_date(file)
    assert start_date == date(2017, 1, 4)
    assert end_date == date(2017, 1, 30)
