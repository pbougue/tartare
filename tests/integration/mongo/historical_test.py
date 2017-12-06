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

import pytest
from freezegun import freeze_time

import tartare
from tartare import app, mongo
from tartare.core import models
from tartare.core.constants import DATA_FORMAT_GTFS, DATA_FORMAT_DIRECTION_CONFIG
from tests.integration.test_mechanism import TartareFixture


class TestHistorical(TartareFixture):
    def __init_contributor_config(self):
        data_source_gtfs = {
            "id": "data_source_gtfs",
            "name": "data_source_gtfs",
            "input": {
                "type": "url",
                "url": ""
            }
        }
        data_source_config = {
            "id": "data_source_config",
            "name": "data_source_config",
            "data_format": "direction_config",
            "input": {
                "type": "url",
                "url": ""
            }
        }
        raw = self.post('/contributors/id_test/data_sources', json.dumps(data_source_gtfs))
        self.assert_sucessful_call(raw, 201)
        raw = self.post('/contributors/id_test/data_sources', json.dumps(data_source_config))
        self.assert_sucessful_call(raw, 201)

    def __init_coverage_config(self):
        coverage = {"id": "jdr", "name": "name of the coverage jdr", "contributors": ["id_test"]}
        raw = self.post('/coverages', json.dumps(coverage))
        self.assert_sucessful_call(raw, 201)

    @pytest.mark.parametrize("exports_number", [1, 2, 3, 4, 5])
    def test_historisation(self, contributor, init_http_download_server, exports_number):
        self.__init_contributor_config()
        self.__init_coverage_config()
        url_gtfs = self.format_url(ip=init_http_download_server.ip_addr, filename='historisation/gtfs-{number}.zip')
        url_config = self.format_url(ip=init_http_download_server.ip_addr,
                                     filename='historisation/config-{number}.json')

        for i in range(1, exports_number + 1):
            raw = self.patch('/contributors/id_test/data_sources/data_source_gtfs', json.dumps(
                {"input": {"url": url_gtfs.format(number=i)}}
            ))
            self.assert_sucessful_call(raw)
            raw = self.patch('/contributors/id_test/data_sources/data_source_config', json.dumps(
                {"input": {"url": url_config.format(number=i)}}
            ))
            self.assert_sucessful_call(raw)

            self.full_export('id_test', 'jdr')

        with app.app_context():
            self.assert_data_source_fetched_number('data_source_gtfs', exports_number)
            self.assert_data_source_fetched_number('data_source_config', exports_number)
            self.assert_contributor_exports_number(exports_number)
            self.assert_coverage_exports_number(exports_number)
            self.assert_files_number(exports_number)

    def assert_data_source_fetched_number(self, data_source_id, exports_number):
        raw = mongo.db[models.DataSourceFetched.mongo_collection].find({
            'contributor_id': 'id_test',
            'data_source_id': data_source_id
        })
        assert raw.count() == min(exports_number, tartare.app.config.get('HISTORICAL', 3))

    def assert_contributor_exports_number(self, exports_number):
        raw = mongo.db[models.ContributorExport.mongo_collection].find({
            'contributor_id': 'id_test'
        })
        assert raw.count() == min(exports_number, tartare.app.config.get('HISTORICAL', 3))

    def assert_coverage_exports_number(self, exports_number):
        raw = mongo.db[models.CoverageExport.mongo_collection].find({
            'coverage_id': 'jdr'
        })
        assert raw.count() == min(exports_number, tartare.app.config.get('HISTORICAL', 3))

    def assert_files_number(self, exports_number):
        raw = mongo.db['fs.files'].find({})
        assert raw.count() == min(tartare.app.config.get('HISTORICAL', 3), exports_number) * 5
