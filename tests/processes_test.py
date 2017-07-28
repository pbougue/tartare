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
import requests
from freezegun import freeze_time
from mock import mock
from tartare.core.context import Context, ContributorContext
from tartare.core.models import ContributorExport, ValidityPeriod
from tartare.exceptions import IntegrityException, FusioException
from tartare.processes.coverage import FusioImport, FusioPreProd, FusioExport
from datetime import date
from tests.utils import get_response


class TestFusioProcesses:
    @freeze_time("2017-01-15")
    # /!\following patches are parameters reversed in function signature
    @mock.patch('tartare.processes.fusio.Fusio.call')
    @mock.patch('tartare.processes.fusio.Fusio.get_action_id')
    @mock.patch('tartare.processes.fusio.Fusio.wait_for_action_terminated')
    @pytest.mark.parametrize(
        "contributor_validity_period_dates,expected_data", [
            # one contributor
            ([(date(2017, 1, 20), date(2017, 7, 14))],
             {'DateDebut': '20/01/2017', 'DateFin': '14/07/2017', 'action': 'regionalimport'}),
            # one contributor more than one year now inside
            ([(date(2017, 1, 1), date(2018, 3, 15))],
             {'DateDebut': '15/01/2017', 'DateFin': '14/01/2018', 'action': 'regionalimport'}),
            # one contributor more than one year now outside
            ([(date(2018, 1, 15), date(2020, 1, 15))],
             {'DateDebut': '15/01/2018', 'DateFin': '14/01/2019', 'action': 'regionalimport'}),
            # cross
            ([(date(2017, 1, 1), date(2017, 7, 1)), (date(2017, 3, 1), date(2017, 9, 1))],
             {'DateDebut': '01/01/2017', 'DateFin': '01/09/2017', 'action': 'regionalimport'}),
            # next
            ([(date(2017, 1, 15), date(2017, 3, 1)), (date(2017, 7, 1), date(2017, 12, 11))],
             {'DateDebut': '15/01/2017', 'DateFin': '11/12/2017', 'action': 'regionalimport'}),
            # before
            ([(date(2017, 7, 1), date(2017, 9, 1)), (date(2017, 1, 9), date(2017, 3, 1))],
             {'DateDebut': '09/01/2017', 'DateFin': '01/09/2017', 'action': 'regionalimport'}),
            # included
            ([(date(2017, 1, 1), date(2017, 12, 1)), (date(2017, 3, 9), date(2017, 3, 6))],
             {'DateDebut': '01/01/2017', 'DateFin': '01/12/2017', 'action': 'regionalimport'}),
            # more than one year now inside
            ([(date(2017, 1, 1), date(2017, 7, 1)), (date(2018, 3, 1), date(2018, 9, 1))],
             {'DateDebut': '15/01/2017', 'DateFin': '14/01/2018', 'action': 'regionalimport'}),
            # more than one year now outside
            ([(date(2018, 1, 1), date(2018, 7, 1)), (date(2019, 3, 1), date(2019, 9, 1))],
             {'DateDebut': '01/01/2018', 'DateFin': '31/12/2018', 'action': 'regionalimport'}),
            # 3 contrib
            ([(date(2018, 1, 1), date(2018, 4, 1)), (date(2018, 10, 1), date(2018, 12, 11)),
              (date(2018, 8, 11), date(2018, 10, 13))],
             {'DateDebut': '01/01/2018', 'DateFin': '11/12/2018', 'action': 'regionalimport'}),
        ])
    def test_fusio_import_valid_dates(self, wait_for_action_terminated, fusio_get_action_id, fusio_call,
                                      contributor_validity_period_dates, expected_data):
        contributors_context = []
        for contrib_begin_date, contrib_end_date in contributor_validity_period_dates:
            contributors_context.append(
                ContributorContext(contributor=None,
                                   validity_period=ValidityPeriod(contrib_begin_date, contrib_end_date),
                                   data_source_contexts=None)
            )

        context = Context(contributors_context=contributors_context)

        keep_response_content = 'fusio_response'
        action_id = 42

        fusio_call.return_value = get_response(200, keep_response_content)
        fusio_get_action_id.return_value = action_id

        fusio_import = FusioImport(context, {"url": "whatever"})
        fusio_import.do()

        fusio_call.assert_called_with(requests.post, api="api", data=expected_data)
        fusio_get_action_id.assert_called_with(keep_response_content)
        wait_for_action_terminated.assert_called_with(action_id)

    @freeze_time("2017-01-15")
    @pytest.mark.parametrize(
        "contrib_begin_date,contrib_end_date,expected_message", [
            # one contributor
            (date(2015, 1, 20), date(2015, 7, 14),
             "bounds date from fusio import incorrect (end_date: 14/07/2015 < now: 15/01/2017)"),
            (date(2017, 1, 1), date(2017, 1, 14),
             "bounds date from fusio import incorrect (end_date: 14/01/2017 < now: 15/01/2017)"),
        ])
    def test_fusio_import_invalid_dates(self, contrib_begin_date, contrib_end_date, expected_message):
        with pytest.raises(IntegrityException) as excinfo:
            contributor_context = ContributorContext(contributor=None,
                                                     validity_period=ValidityPeriod(contrib_begin_date, contrib_end_date),
                                                     data_source_contexts=None)
            context = Context(contributors_context=[contributor_context])
            fusio_import = FusioImport(context, {"url": "whatever"})
            fusio_import.do()
        assert str(excinfo.value) == expected_message

    @mock.patch('tartare.processes.fusio.Fusio.wait_for_action_terminated')
    @mock.patch('tartare.processes.fusio.Fusio.call')
    def test_call_fusio_preprod(self, fusio_call, fusio_wait_for_action_terminated):
        content = """<?xml version="1.0" encoding="ISO-8859-1"?>
                <serverfusio>
                    <ActionId>1607281547155684</ActionId>
                </serverfusio>"""
        fusio_call.return_value = get_response(200, content)
        fusio_preprod = FusioPreProd(context=Context('coverage'), params={'url': 'http://fusio_host'})
        fusio_preprod.do()

        fusio_call.assert_called_with(requests.post, api='api', data={'action': 'settopreproduction'})
        fusio_wait_for_action_terminated.assert_called_with('1607281547155684')

    @mock.patch('tartare.processes.coverage.FusioExport.save_export')
    @mock.patch('tartare.processes.fusio.Fusio.get_export_url')
    @mock.patch('tartare.processes.fusio.Fusio.wait_for_action_terminated')
    @mock.patch('tartare.processes.fusio.Fusio.call')
    def test_call_fusio_export(self, fusio_call, fusio_wait_for_action_terminated, get_export_url, save_export):
        content = """<?xml version="1.0" encoding="ISO-8859-1"?>
                <serverfusio>
                    <ActionId>1607281547155684</ActionId>
                </serverfusio>"""
        fusio_call.return_value = get_response(200, content)
        get_export_url.return_value = 'abcd.zip'
        params={
            'url': 'http://fusio_host',
            "export_type": "Ntfs"
        }
        fusio_export = FusioExport(context=Context('coverage'), params=params)
        fusio_export.do()
        data = {
            'action': 'Export',
            "ExportType": 32,
            "Source": 4
        }
        fusio_call.assert_called_with(requests.post, api='api', data=data)
        fusio_wait_for_action_terminated.assert_called_with('1607281547155684')
        get_export_url.assert_called_with('1607281547155684')
        save_export.assert_called_with('abcd.zip')

    def test_call_fusio_export_unkown_export_type(self):
        params = {
            'url': 'http://fusio_host',
            "export_type": "bob"
        }
        fusio_export = FusioExport(context=Context('coverage'), params=params)
        with pytest.raises(FusioException) as excinfo:
                fusio_export.do()
        assert str(excinfo.value) == "export_type bob not found"

