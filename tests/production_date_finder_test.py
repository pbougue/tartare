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
from tartare.exceptions import FileNotFound

current_path = os.path.dirname(os.path.dirname(__file__))


def test_zip_file_only_calendar():
    finder = ProductionDateFinder()
    file = os.path.join(current_path, 'tests/fixtures/gtfs/some_archive.zip')
    start_date, end_date = finder.get_production_date(file)
    assert start_date == date(2015, 3, 25)
    assert end_date == date(2015, 8, 26)


def test_get_production_date_zip_file_invalid():
    finder = ProductionDateFinder()
    file = os.path.join(current_path, 'tests/fixtures/gtfs/bob.zip')
    with pytest.raises(FileNotFound) as excinfo:
            finder.get_production_date(file)
    assert str(excinfo.value) == "File {} not found".format(file)


def test_get_production_date_not_zipfile():
    finder = ProductionDateFinder()
    file = os.path.join(current_path, 'tests/fixtures/ntfs/calendar.txt')
    with pytest.raises(Exception) as excinfo:
            finder.get_production_date(file)
    assert str(excinfo.value) == "{} is not a zip file".format(file)

