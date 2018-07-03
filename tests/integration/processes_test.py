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
from tartare.core.context import Context, ContributorExportContext, CoverageExportContext
from tartare.core.models import Process, Job
from tartare.http_exceptions import InvalidArguments
from tartare.processes import contributor
from tartare.processes import coverage
from tartare.processes.coverage import FusioPreProd
from tartare.processes.processes import ProcessManager
from tartare.tasks import launch


def test_contributor_process():
    map_test = {
        "Ruspell": contributor.Ruspell,
        "HeadsignShortName": contributor.HeadsignShortName,
        "GtfsAgencyFile": contributor.GtfsAgencyFile,
        "ComputeExternalSettings": contributor.ComputeExternalSettings,
        "ComputeDirections": contributor.ComputeDirections,
    }

    with app.app_context():
        # Contributor Process
        for key, value in map_test.items():
            assert isinstance(ProcessManager.get_process(
                ContributorExportContext(Job(ACTION_TYPE_CONTRIBUTOR_EXPORT)), Process(type=key)), value)
    # Coverage Process
    for key in map_test.keys():
        with pytest.raises(InvalidArguments) as excinfo:
            ProcessManager.get_process(CoverageExportContext(Job(ACTION_TYPE_COVERAGE_EXPORT)),
                                          Process(type=key))
        assert str(excinfo.typename) == "InvalidArguments"


def test_coverage_process():
    map_test = {
        "FusioDataUpdate": coverage.FusioDataUpdate,
        "FusioImport": coverage.FusioImport,
        "FusioPreProd": coverage.FusioPreProd,
        "FusioExport": coverage.FusioExport,
        "FusioSendPtExternalSettings": coverage.FusioSendPtExternalSettings,
    }

    # Coverage Process
    for key, value in map_test.items():
        assert isinstance(ProcessManager.get_process(CoverageExportContext(Job(ACTION_TYPE_COVERAGE_EXPORT)),
                                                        Process(type=key, params={'url': 'http://fusio.com'})),
                          value)
    # Contributor Process
    for key in map_test.keys():
        with pytest.raises(InvalidArguments) as excinfo:
            ProcessManager.get_process(ContributorExportContext(Job(ACTION_TYPE_CONTRIBUTOR_EXPORT)),
                                          Process(type=key))
        assert str(excinfo.typename) == "InvalidArguments"


def test_coverage_invalid_process():
    with pytest.raises(InvalidArguments) as excinfo:
        isinstance(ProcessManager.get_process(CoverageExportContext(Job(ACTION_TYPE_COVERAGE_EXPORT)),
                                                 Process(type='AA')), FusioPreProd)
    assert str(excinfo.typename) == "InvalidArguments"


def test_contributor_invalid_process():
    with pytest.raises(InvalidArguments) as excinfo:
        isinstance(ProcessManager.get_process(ContributorExportContext(Job(ACTION_TYPE_CONTRIBUTOR_EXPORT)),
                                                 Process(type='AA')), FusioPreProd)
    assert str(excinfo.typename) == "InvalidArguments"


@mock.patch('tartare.tasks.run_process.s')
def test_launch_in_sequence(mock_run_process):
    processes = [Process(id='bob', sequence=1), Process(id='toto', sequence=0),
                    Process(id='tata', sequence=2)]
    launch(processes, ContributorExportContext(Job(ACTION_TYPE_CONTRIBUTOR_EXPORT)))
    calls = mock_run_process.call_args_list
    assert 'toto' == calls[0][0][1].id
    assert 'bob' == calls[1][0][0].id
    assert 'tata' == calls[2][0][0].id

@mock.patch('tartare.tasks.run_process.s')
def test_launch_enabled(mock_run_process):
    processes = [Process(id='bob', sequence=1, enabled=False), Process(id='toto', sequence=0, enabled=True),
                    Process(id='tata', sequence=2, enabled=True)]
    launch(processes, ContributorExportContext(Job(ACTION_TYPE_CONTRIBUTOR_EXPORT)))
    calls = mock_run_process.call_args_list
    assert mock_run_process.call_count == 2
    assert calls[0][0][1].id == 'toto'
    assert calls[1][0][0].id == 'tata'
