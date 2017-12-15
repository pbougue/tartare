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
import pytest
from mock import mock

from tartare import app
from tartare.core.constants import ACTION_TYPE_CONTRIBUTOR_EXPORT, ACTION_TYPE_COVERAGE_EXPORT
from tartare.core.context import Context
from tartare.core.models import PreProcess, Job
from tartare.http_exceptions import InvalidArguments
from tartare.processes import contributor
from tartare.processes import coverage
from tartare.processes.coverage import FusioPreProd
from tartare.processes.processes import PreProcessManager
from tartare.tasks import launch


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
            assert isinstance(PreProcessManager.get_preprocess(
                Context('contributor', Job(ACTION_TYPE_CONTRIBUTOR_EXPORT)), PreProcess(type=key)), value)
    # Coverage Preprocess
    for key in map_test.keys():
        with pytest.raises(InvalidArguments) as excinfo:
            PreProcessManager.get_preprocess(Context('coverage', Job(ACTION_TYPE_COVERAGE_EXPORT)),
                                             PreProcess(type=key))
        assert str(excinfo.typename) == "InvalidArguments"


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
        assert isinstance(PreProcessManager.get_preprocess(Context('coverage', Job(ACTION_TYPE_COVERAGE_EXPORT)),
                                                           PreProcess(type=key, params={'url': 'http://fusio.com'})),
                          value)
    # Contributor Preprocess
    for key in map_test.keys():
        with pytest.raises(InvalidArguments) as excinfo:
            PreProcessManager.get_preprocess(Context('contributor', Job(ACTION_TYPE_CONTRIBUTOR_EXPORT)),
                                             PreProcess(type=key))
        assert str(excinfo.typename) == "InvalidArguments"


def test_coverage_invalid_preprocess():
    with pytest.raises(InvalidArguments) as excinfo:
        isinstance(PreProcessManager.get_preprocess(Context('coverage', Job(ACTION_TYPE_COVERAGE_EXPORT)),
                                                    PreProcess(type='AA')), FusioPreProd)
    assert str(excinfo.typename) == "InvalidArguments"


def test_contributor_invalid_preprocess():
    with pytest.raises(InvalidArguments) as excinfo:
        isinstance(PreProcessManager.get_preprocess(Context('contributor', Job(ACTION_TYPE_CONTRIBUTOR_EXPORT)),
                                                    PreProcess(type='AA')), FusioPreProd)
    assert str(excinfo.typename) == "InvalidArguments"


def test_preprocess_invalid_instance():
    with pytest.raises(InvalidArguments) as excinfo:
        PreProcessManager.get_preprocess(Context('bob', Job(ACTION_TYPE_CONTRIBUTOR_EXPORT)),
                                         PreProcess(type='FusioPreProd'))
    assert str(excinfo.typename) == "InvalidArguments"


@mock.patch('tartare.tasks.run_contributor_preprocess.s')
def test_launch_in_sequence(mock_run_contributor_preprocess):
    preprocesses = [PreProcess(id='bob', sequence=1), PreProcess(id='toto', sequence=0),
                    PreProcess(id='tata', sequence=2)]
    launch(preprocesses, Context('contributor', Job(ACTION_TYPE_CONTRIBUTOR_EXPORT)))
    calls = mock_run_contributor_preprocess.call_args_list
    assert 'toto' == calls[0][0][1].id
    assert 'bob' == calls[1][0][0].id
    assert 'tata' == calls[2][0][0].id
