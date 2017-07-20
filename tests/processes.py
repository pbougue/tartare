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
from tartare.core.context import Context
from tartare.core.models import ContributorExport, ValidityPeriod
from tartare.processes.coverage import FusioImport
from datetime import date
from tests.utils import get_response


class TestFusioProcesses:
    @freeze_time("2017-01-15")
    # /!\following patches are parameters reversed in function signature
    @mock.patch('tartare.processes.fusio.Fusio.call')
    @mock.patch('tartare.processes.fusio.Fusio.get_action_id')
    @mock.patch('tartare.processes.fusio.Fusio.wait_for_action_terminated')
    @pytest.mark.parametrize(
        "begin_date_validity1,end_date_validity1,begin_date_validity2,end_date_validity2,expected_data", [
            # cross
            (date(2015, 1, 1), date(2015, 7, 1), date(2015, 3, 1), date(2015, 9, 1),
             {'DateDebut': '01/01/2015', 'DateFin': '01/09/2015', 'action': 'regionalimport'}),
            # next
            (date(2015, 1, 15), date(2015, 3, 1), date(2015, 7, 1), date(2015, 12, 11),
             {'DateDebut': '15/01/2015', 'DateFin': '11/12/2015', 'action': 'regionalimport'}),
            # before
            (date(2015, 7, 1), date(2015, 9, 1), date(2015, 1, 9), date(2015, 3, 1),
             {'DateDebut': '09/01/2015', 'DateFin': '01/09/2015', 'action': 'regionalimport'}),
            # included
            (date(2015, 1, 1), date(2015, 12, 1), date(2015, 3, 9), date(2015, 3, 6),
             {'DateDebut': '01/01/2015', 'DateFin': '01/12/2015', 'action': 'regionalimport'}),
            # more than one year now inside
            (date(2017, 1, 1), date(2017, 7, 1), date(2018, 3, 1), date(2018, 9, 1),
             {'DateDebut': '15/01/2017', 'DateFin': '14/01/2018', 'action': 'regionalimport'}),
            # more than one year now outside
            (date(2018, 1, 1), date(2018, 7, 1), date(2019, 3, 1), date(2019, 9, 1),
             {'DateDebut': '01/01/2018', 'DateFin': '31/12/2018', 'action': 'regionalimport'}),
        ])
    def test_fusio_import_valid_dates(self, wait_for_action_terminated, fusio_get_action_id, fusio_call,
                                      begin_date_validity1, end_date_validity1,
                                      begin_date_validity2, end_date_validity2, expected_data):
        contrib_export1 = ContributorExport('', '',
                                            validity_period=ValidityPeriod(begin_date_validity1, end_date_validity1))
        contrib_export2 = ContributorExport('', '',
                                            validity_period=ValidityPeriod(begin_date_validity2, end_date_validity2))
        context = Context(contributor_exports=[contrib_export1, contrib_export2])

        keep_response_content = 'fusio_response'
        action_id = 42

        fusio_call.return_value = get_response(200, keep_response_content)
        fusio_get_action_id.return_value = action_id

        fusio_import = FusioImport(context, {"url": "whatever"})
        fusio_import.do()

        fusio_call.assert_called_with(requests.post, api="api", data=expected_data)
        fusio_get_action_id.assert_called_with(keep_response_content)
        wait_for_action_terminated.assert_called_with(action_id)
