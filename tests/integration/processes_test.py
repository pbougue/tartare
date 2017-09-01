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
from tartare import app
from tartare.core.models import PreProcess
from tartare.processes.contributor import ComputeDirections
from tartare.processes.coverage import FusioPreProd
from tartare.processes.processes import PreProcessManager
from tartare.processes import contributor
from tartare.processes import coverage
from tartare.http_exceptions import InvalidArguments
import pytest
from tartare.core.context import Context


def test_contributor_preprocess():
    map_test = {
        "Ruspell": contributor.Ruspell,
        "HeadsignShortName": contributor.HeadsignShortName,
        "GtfsAgencyFile": contributor.GtfsAgencyFile,
        "ComputeExternalSettings": contributor.ComputeExternalSettings,
        "ComputeDirections": contributor.ComputeDirections,
    }

    with app.app_context():
        # Contributor Preprocess
        for key, value in map_test.items():
            assert isinstance(PreProcessManager.get_preprocess(Context('contributor'), PreProcess(type=key)), value)
    # Coverage Preprocess
    for key in map_test.keys():
        with pytest.raises(InvalidArguments) as excinfo:
            PreProcessManager.get_preprocess(Context('coverage'), PreProcess(type=key))
        assert str(excinfo.typename) == "InvalidArguments"


def test_compute_directions_preprocess():
    with app.app_context():
        assert isinstance(PreProcessManager.get_preprocess(Context('contributor'),
                                                           PreProcess(type='ComputeDirections')), ComputeDirections)


def test_coverage_preprocess():
    map_test = {
        "FusioDataUpdate": coverage.FusioDataUpdate,
        "FusioImport": coverage.FusioImport,
        "FusioPreProd": coverage.FusioPreProd,
        "FusioExport": coverage.FusioExport,
        "FusioSendPtExternalSettings": coverage.FusioSendPtExternalSettings,
    }

    # Coverage Preprocess
    for key, value in map_test.items():
        assert isinstance(PreProcessManager.get_preprocess(Context('coverage'), PreProcess(type=key, params={'url': 'http://fusio.com'})), value)
    # Contributor Preprocess
    for key in map_test.keys():
        with pytest.raises(InvalidArguments) as excinfo:
            PreProcessManager.get_preprocess(Context('contributor'), PreProcess(type=key))
        assert str(excinfo.typename) == "InvalidArguments"


def test_coverage_invalid_preprocess():
    with pytest.raises(InvalidArguments) as excinfo:
        isinstance(PreProcessManager.get_preprocess(Context('coverage'), PreProcess(type='AA')), FusioPreProd)
    assert str(excinfo.typename) == "InvalidArguments"


def test_contributor_invalid_preprocess():
    with pytest.raises(InvalidArguments) as excinfo:
        isinstance(PreProcessManager.get_preprocess(Context('contributor'), PreProcess(type='AA')), FusioPreProd)
    assert str(excinfo.typename) == "InvalidArguments"


def test_preprocess_invalid_instance():
    with pytest.raises(InvalidArguments) as excinfo:
        PreProcessManager.get_preprocess(Context('bob'), PreProcess(type='FusioPreProd'))
    assert str(excinfo.typename) == "InvalidArguments"
