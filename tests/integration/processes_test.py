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

from tartare.processes.processes import PreProcess
from tartare.processes.contributor import *
from tartare.processes.coverage import *
from tartare.http_exceptions import InvalidArguments
import pytest
from tartare.core.context import Context


def test_ruspell_preprocess():
    assert isinstance(PreProcess.get_preprocess(Context('contributor'), 'Ruspell'), Ruspell)


def test_compute_directions_preprocess():
    assert isinstance(PreProcess.get_preprocess(Context('contributor'), 'ComputeDirections'), ComputeDirections)


def test_headsign_short_name_preprocess():
    assert isinstance(PreProcess.get_preprocess(Context('contributor'), 'HeadsignShortName'), HeadsignShortName)


def test_fusio_data_update_preprocess():
    assert isinstance(PreProcess.get_preprocess(Context('coverage'), 'FusioDataUpdate'), FusioDataUpdate)


def test_fusio_import_preprocess():
    assert isinstance(PreProcess.get_preprocess(Context('coverage'), 'FusioImport'), FusioImport)


def test_fusio_preprod_preprocess():
    assert isinstance(PreProcess.get_preprocess(Context('coverage'), 'FusioPreProd'), FusioPreProd)


def test_coverage_invalid_preprocess():
    with pytest.raises(InvalidArguments) as excinfo:
        isinstance(PreProcess.get_preprocess(Context('coverage'), 'AA'), FusioPreProd)
    assert str(excinfo.typename) == "InvalidArguments"


def test_contributor_invalid_preprocess():
    with pytest.raises(InvalidArguments) as excinfo:
        isinstance(PreProcess.get_preprocess(Context('contributor'), 'AA'), FusioPreProd)
    assert str(excinfo.typename) == "InvalidArguments"


def test_contributor_fusio_preprod_preprocess():
    with pytest.raises(InvalidArguments) as excinfo:
        isinstance(PreProcess.get_preprocess(Context('contributor'), 'FusioPreProd'), FusioPreProd)
    assert str(excinfo.typename) == "InvalidArguments"


def test_coverage_compute_directions_preprocess():
    with pytest.raises(InvalidArguments) as excinfo:
        isinstance(PreProcess.get_preprocess(Context('coverage'), 'ComputeDirections'), FusioPreProd)
    assert str(excinfo.typename) == "InvalidArguments"
