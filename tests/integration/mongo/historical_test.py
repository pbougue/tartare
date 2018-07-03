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
from bson import ObjectId

import tartare
from tartare import app, mongo
from tartare.core import models
from tartare.core.models import MongoContributorExportSchema, DataSource
from tests.integration.test_mechanism import TartareFixture


class TestHistorical(TartareFixture):
    def __init_contributor_config(self, contributor):
        data_source_gtfs = {
            "id": "data_source_gtfs",
            "name": "data_source_gtfs",
            "input": {
                "type": "auto",
                "url": "",
                "frequency": {
                    "type": "daily",
                    "hour_of_day": 20
                }
            }
        }
        data_source_config = {
            "id": "data_source_config",
            "name": "data_source_config",
            "data_format": "direction_config",
            "input": {
                "type": "auto",
                "url": "",
                "frequency": {
                    "type": "daily",
                    "hour_of_day": 20
                }
            }
        }
        contributor['data_sources'] = [
            data_source_gtfs,
            data_source_config
        ]
        raw = self.put('/contributors/id_test', self.dict_to_json(contributor))
        return self.assert_sucessful_call(raw)['contributors'][0]

    def __init_coverage_config(self):
        coverage = {"id": "jdr", "name": "name of the coverage jdr", "input_data_source_ids": ["data_source_gtfs"]}
        raw = self.post('/coverages', json.dumps(coverage))
        self.assert_sucessful_create(raw)

    # HISTORICAL value is 2 in tests/testing_settings.py
    @pytest.mark.parametrize("exports_number", [1, 2, 3, 4, 5])
    def test_historisation(self, contributor, init_http_download_server, exports_number):
        contributor = self.__init_contributor_config(contributor)
        self.__init_coverage_config()
        url_gtfs = self.format_url(ip=init_http_download_server.ip_addr, filename='historisation/gtfs-{number}.zip')
        url_config = self.format_url(ip=init_http_download_server.ip_addr,
                                     filename='historisation/config-{number}.json')

        for i in range(1, exports_number + 1):
            contributor['data_sources'][0]['input']["url"] = url_gtfs.format(number=i)
            contributor['data_sources'][1]['input']["url"] = url_config.format(number=i)
            self.put('/contributors/id_test', self.dict_to_json(contributor))
            self.full_export('id_test', 'jdr')
            raw = self.get('/contributors/id_test')
            contributor = self.assert_sucessful_call(raw)['contributors'][0]

        with app.app_context():
            self.assert_data_set_number('data_source_gtfs', exports_number)
            self.assert_data_set_number('data_source_config', exports_number)
            self.assert_coverage_exports_number(exports_number)
            self.assert_files_number(exports_number)

    def assert_data_set_number(self, data_source_id, exports_number):
        data_sources = DataSource.get_one(data_source_id)
        assert len(data_sources.data_sets) == min(exports_number, tartare.app.config.get('HISTORICAL'))

    def assert_coverage_exports_number(self, exports_number):
        raw = mongo.db[models.CoverageExport.mongo_collection].find({
            'coverage_id': 'jdr'
        })
        assert raw.count() == min(exports_number, tartare.app.config.get('HISTORICAL'))

    def assert_files_number(self, exports_number):
        raw = mongo.db['fs.files'].find({})
        assert raw.count() == (min(tartare.app.config.get('HISTORICAL'), exports_number) * 3)
