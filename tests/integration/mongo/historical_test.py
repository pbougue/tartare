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
        self.assert_sucessful_create(raw)
        raw = self.post('/contributors/id_test/data_sources', json.dumps(data_source_config))
        self.assert_sucessful_create(raw)

    def __init_coverage_config(self):
        coverage = {"id": "jdr", "name": "name of the coverage jdr", "contributors": ["id_test"]}
        raw = self.post('/coverages', json.dumps(coverage))
        self.assert_sucessful_create(raw)

    # HISTORICAL value is 2 in tests/testing_settings.py
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
            self.assert_data_source_fetched_number(contributor['id'], 'data_source_gtfs', exports_number)
            self.assert_data_source_fetched_number(contributor['id'], 'data_source_config', exports_number)
            self.assert_contributor_exports_number(exports_number)
            self.assert_coverage_exports_number(exports_number)
            self.assert_files_number(exports_number)

    def assert_data_source_fetched_number(self, contributor_id, data_source_id, exports_number):
        data_sources = DataSource.get_one(contributor_id, data_source_id)
        assert len(data_sources.data_sets) == exports_number

    def assert_contributor_exports_number(self, exports_number):
        raw = mongo.db[models.ContributorExport.mongo_collection].find({
            'contributor_id': 'id_test'
        })
        assert raw.count() == min(exports_number, tartare.app.config.get('HISTORICAL'))

    def assert_coverage_exports_number(self, exports_number):
        raw = mongo.db[models.CoverageExport.mongo_collection].find({
            'coverage_id': 'jdr'
        })
        assert raw.count() == min(exports_number, tartare.app.config.get('HISTORICAL'))

    def assert_files_number(self, exports_number):
        raw = mongo.db['fs.files'].find({})
        #                                       === historized parts ===                      +  === data_sets parts ===
        assert raw.count() == (min(tartare.app.config.get('HISTORICAL'), exports_number) * 5) + (exports_number * 2)

    # HISTORICAL value is 2 in tests/testing_settings.py
    def test_data_sets_histo_and_cleaning(self, init_http_download_server):
        cid = 'cid'
        dsid = 'dsid'
        url_gtfs = self.format_url(ip=init_http_download_server.ip_addr, filename='historisation/gtfs-{number}.zip')
        self.init_contributor(cid, dsid, url_gtfs.format(number=1))
        self.contributor_export(cid)  # -> updated
        self.contributor_export(cid)  # -> unchanged
        self.update_data_source_url(cid, dsid, url_gtfs.format(number=2))
        self.contributor_export(cid)  # -> updated and purge last unchanged
        self.update_data_source_url(cid, dsid, 'fail-url')
        self.contributor_export(cid, check_done=False)  # -> failed
        self.update_data_source_url(cid, dsid, url_gtfs.format(number=3))
        self.contributor_export(cid)  # -> updated and purge last failed and 1st updated
        self.contributor_export(cid)  # -> unchanged
        self.update_data_source_url(cid, dsid, 'fail-url')  # -> failed
        self.contributor_export(cid, check_done=False)
        # there should remain 3 DataSet: 3 updated, 2 unchanged happened after last update and
        # 1 failed happened after last update
        with app.app_context():
            data_sets = DataSource.get_one(cid, dsid).data_sets
            assert len(data_sets) == 3
            raw = mongo.db['fs.files'].find({})
            assert raw.count() == 5

    def test_historization_does_not_break_contributor_coverage_export_references(self, init_http_download_server):
        url_gtfs = self.format_url(ip=init_http_download_server.ip_addr, filename='historisation/gtfs-1.zip')
        self.init_contributor('cid', 'dsid', url_gtfs)
        self.contributor_export('cid')
        self.init_coverage('covid', ['cid'])
        self.coverage_export('covid')
        self.coverage_export('covid')
        self.coverage_export('covid')
        with app.app_context():
            raw = mongo.db[models.ContributorExport.mongo_collection].find({
                'contributor_id': 'cid'
            })
            cont_ex = MongoContributorExportSchema(many=True, strict=True).load(raw).data
            gridfs_referenced = cont_ex[0].data_sources[0].gridfs_id
            raw = mongo.db['fs.files'].find({'_id': ObjectId(gridfs_referenced)})
            assert raw.count() == 1
