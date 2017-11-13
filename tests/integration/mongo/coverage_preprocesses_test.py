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
import json

import mock

from tests.integration.test_mechanism import TartareFixture
from tests.utils import get_response


class TestFusioDataUpdatePreprocess(TartareFixture):
    def __init_contributor(self, contributor_id, data_source_id, url, data_prefix='AAA'):

        data_source = {
            "id": data_source_id,
            "name": "my_gtfs",
            "input": {
                "type": "url",
                "url": url
            }
        }
        contributor = {
            "id": contributor_id,
            "name": "name_test",
            "data_prefix": data_prefix,
            "data_sources": [data_source]
        }
        raw = self.post('/contributors', json.dumps(contributor))
        self.assert_sucessful_call(raw, 201)

    def __init_coverage(self, coverage_id, contributor_ids):
        coverage = {
            "id": coverage_id,
            "name": "name of the coverage jdr",
            "contributors": contributor_ids,
            "preprocesses": [
                {
                    "id": "fusio_dataupdate",
                    "type": "FusioDataUpdate",
                    "params": {
                        "url": "http://fusio_host/cgi-bin/fusio.dll/"
                    },
                    "sequence": 0
                }
            ]
        }
        raw = self.post('/coverages', json.dumps(coverage))
        self.assert_sucessful_call(raw, 201)

    @mock.patch('tartare.processes.fusio.Fusio.wait_for_action_terminated')
    @mock.patch('tartare.processes.fusio.Fusio.call')
    # Given I create a contributor with a data source
    # And   I create a coverage containing this contributor and a preprocess FusioDataUpdate
    # And   I do a contributor export on this contributor (which leads to a coverage export)
    # When  I update the data source (or the data set has changed)
    # And   I do a contributor export on this contributor (which leads to a coverage export)
    # Then  I can see that Fusio has been called 2 time(s) in total
    def test_data_update_called_if_data_source_updated(self, fusio_call, wait_for_action_terminated,
                                                       init_http_download_server):
        filename = 'gtfs-{number}.zip'

        url = self.format_url(ip=init_http_download_server.ip_addr,
                              filename=filename.format(number=1),
                              path='gtfs/historisation')

        self.__init_contributor("id_test", "my_gtfs",  url)
        self.__init_coverage("jdr", ["id_test"])

        content = """<?xml version="1.0" encoding="ISO-8859-1"?>
                    <serverfusio>
                        <ActionId>1607281547155684</ActionId>
                    </serverfusio>"""
        fusio_call.return_value = get_response(200, content)

        raw = self.post('/contributors/id_test/actions/export?current_date={}'.format("2017-08-10"))
        self.assert_sucessful_call(raw, 201)

        url = self.format_url(ip=init_http_download_server.ip_addr,
                              filename=filename.format(number=2),
                              path='gtfs/historisation')

        raw = self.patch('/contributors/id_test/data_sources/my_gtfs',
                         json.dumps({"input": {"url": url}}))
        self.assert_sucessful_call(raw)

        raw = self.post('/contributors/id_test/actions/export?current_date={}'.format("2017-08-10"))
        self.assert_sucessful_call(raw, 201)

        assert fusio_call.call_count == 2

    @mock.patch('tartare.processes.fusio.Fusio.wait_for_action_terminated')
    @mock.patch('tartare.processes.fusio.Fusio.call')
    # Given I create a contributor with a data source
    # And   I create a coverage containing this contributor and a preprocess FusioDataUpdate
    # And   I do a contributor export on this contributor (which leads to a coverage export)
    # When  I do a contributor export on this contributor (which leads to a coverage export)
    # Then  I can see that Fusio has been called 1 time(s) in total
    def test_data_update_called_if_data_source_not_updated(self, fusio_call, wait_for_action_terminated,
                                                           init_http_download_server):
        filename = 'gtfs-{number}.zip'
        url = self.format_url(ip=init_http_download_server.ip_addr,
                              filename=filename.format(number=1),
                              path='gtfs/historisation')
        self.__init_contributor("id_test", "my_gtfs",  url)
        self.__init_coverage("jdr", ["id_test"])

        content = """<?xml version="1.0" encoding="ISO-8859-1"?>
                        <serverfusio>
                            <ActionId>1607281547155684</ActionId>
                        </serverfusio>"""
        fusio_call.return_value = get_response(200, content)

        raw = self.post('/contributors/id_test/actions/export?current_date={}'.format("2017-08-10"))
        self.assert_sucessful_call(raw, 201)

        raw = self.post('/contributors/id_test/actions/export?current_date={}'.format("2017-08-10"))
        self.assert_sucessful_call(raw, 201)

        assert fusio_call.call_count == 1
