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
from datetime import date

import pytest
import requests
from mock import mock

from tartare.core.constants import ACTION_TYPE_COVERAGE_EXPORT
from tartare.core.context import CoverageExportContext
from tartare.core.models import ValidityPeriod, PreProcess, Job
from tartare.exceptions import IntegrityException, FusioException, ValidityPeriodException
from tartare.processes.coverage import FusioImport, FusioPreProd, FusioExport
from tests.utils import get_response


class TestFusioProcesses:
    # /!\following patches are parameters reversed in function signature
    @mock.patch('tartare.core.models.ValidityPeriod.to_valid')
    @mock.patch('tartare.core.models.ValidityPeriod.union')
    @mock.patch('tartare.processes.fusio.Fusio.call')
    @mock.patch('tartare.processes.fusio.Fusio.get_action_id')
    @mock.patch('tartare.processes.fusio.Fusio.wait_for_action_terminated')
    def test_fusio_import_valid_dates(self, wait_for_action_terminated, fusio_get_action_id, fusio_call,
                                      get_validity_period_union, get_validity_period_valid):
        begin_date = date(1986, 1, 15)
        end_date = date(2017, 1, 15)
        expected_period = ValidityPeriod(begin_date, end_date)
        get_validity_period_union.return_value = expected_period
        get_validity_period_valid.return_value = expected_period
        context = CoverageExportContext(Job(ACTION_TYPE_COVERAGE_EXPORT))
        keep_response_content = 'fusio_response'
        action_id = 42

        fusio_call.return_value = get_response(200, keep_response_content)
        fusio_get_action_id.return_value = action_id

        fusio_import = FusioImport(context, PreProcess(params={"url": "whatever"}))
        fusio_import.do()

        fusio_call.assert_called_with(requests.post, api="api",
                                      data={'DateDebut': '15/01/1986', 'DateFin': '15/01/2017',
                                            'action': 'regionalimport'})
        fusio_get_action_id.assert_called_with(keep_response_content)
        wait_for_action_terminated.assert_called_with(action_id)

    @mock.patch('tartare.core.models.ValidityPeriod.to_valid')
    @mock.patch('tartare.core.models.ValidityPeriod.union')
    def test_fusio_invalid_or_empty_dates(self, get_validity_period_union, get_validity_period_valid):
        with pytest.raises(IntegrityException) as excinfo:
            subcall_details = 'sub call details'
            get_validity_period_union.return_value = ValidityPeriod(date(2018, 1, 1), date(2018, 3, 1))
            get_validity_period_valid.side_effect = ValidityPeriodException(subcall_details)
            fusio_import = FusioImport(CoverageExportContext(Job(ACTION_TYPE_COVERAGE_EXPORT)),
                                       PreProcess(params={"url": "whatever"}))
            fusio_import.do()
        assert str(excinfo.value) == 'bounds date for fusio import incorrect: {details}'.format(details=subcall_details)

    @mock.patch('tartare.processes.fusio.Fusio.wait_for_action_terminated')
    @mock.patch('tartare.processes.fusio.Fusio.call')
    def test_call_fusio_preprod(self, fusio_call, fusio_wait_for_action_terminated):
        content = """<?xml version="1.0" encoding="ISO-8859-1"?>
                <serverfusio>
                    <ActionId>1607281547155684</ActionId>
                </serverfusio>"""
        fusio_call.return_value = get_response(200, content)
        fusio_preprod = FusioPreProd(context=CoverageExportContext(Job(ACTION_TYPE_COVERAGE_EXPORT)),
                                     preprocess=PreProcess(params={'url': 'http://fusio_host'}))
        fusio_preprod.do()

        fusio_call.assert_called_with(requests.post, api='api', data={'action': 'settopreproduction'})
        fusio_wait_for_action_terminated.assert_called_with('1607281547155684')
