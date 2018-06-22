# coding=utf-8

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
from tartare.core.constants import DATA_SOURCE_STATUS_NEVER_FETCHED, DATA_SOURCE_STATUS_UPDATED
from tests.integration.test_mechanism import TartareFixture
from tartare import app, mongo
from bson.objectid import ObjectId

from tests.utils import _get_file_fixture_full_path

fixtures_path = _get_file_fixture_full_path('gtfs/some_archive.zip')


class TestDatasetApi(TartareFixture):
    def test_post_dataset_of_unknown_contributor(self):
        raw = self.post('/contributors/unknown/data_sources/unknown/data_sets')
        assert raw.status_code == 404
        r = self.json_to_dict(raw)
        assert r["error"] == "contributor 'unknown' not found"

    def test_post_dataset_with_unknown_data_source(self, contributor):
        raw = self.post('/contributors/id_test/data_sources/unknown/data_sets')
        assert raw.status_code == 404
        r = self.json_to_dict(raw)
        assert r["error"] == "data source 'unknown' not found for contributor 'id_test'"

    def test_post_dataset_without_file(self, data_source):
        raw = self.post('/contributors/id_test/data_sources/{}/data_sets'.format(data_source.get('id')))
        assert raw.status_code == 400
        r = self.json_to_dict(raw)
        assert r["error"] == "no file provided"

    def test_post_dataset_with_bad_file_param(self, data_source):
        with open(fixtures_path, 'rb') as file:
            raw = self.post('/contributors/id_test/data_sources/{}/data_sets'.format(data_source.get('id')),
                            params={'bad_param': file},
                            headers={})
            assert raw.status_code == 400
            r = self.json_to_dict(raw)
            assert r["error"] == 'file provided with bad param ("file" param expected)'

    def test_post_dataset_on_unexisting_contributor(self):
        raw = self.post('/contributors/id_test/data_sources/toto/data_sets')
        self.assert_failed_call(raw, 404)
        resp = self.json_to_dict(raw)
        assert resp['error'] == "contributor 'id_test' not found"

    def test_post_dataset_on_unexisting_data_source(self, contributor):
        raw = self.post('/contributors/id_test/data_sources/toto/data_sets')
        self.assert_failed_call(raw, 404)
        resp = self.json_to_dict(raw)
        assert resp['error'] == "data source 'toto' not found for contributor 'id_test'"

    def test_post_dataset(self, data_source):
        raw = self.get('/contributors/id_test/data_sources/{}'.format(data_source.get('id')))
        self.assert_sucessful_call(raw)
        ds = self.json_to_dict(raw)['data_sources'][0]
        assert ds['status'] == DATA_SOURCE_STATUS_NEVER_FETCHED
        assert ds['fetch_started_at'] is None
        assert ds['updated_at'] is None
        assert ds['validity_period'] is None

        raw = self.post_manual_data_set('id_test', data_source.get('id'), 'gtfs/some_archive.zip')
        r = self.json_to_dict(raw)
        assert len(r["data_sets"]) == 1
        assert 'id' in r['data_sets'][0]

        with app.app_context():
            gridfs = mongo.db['fs.files'].find_one({'_id': ObjectId(r["data_sets"][0]["gridfs_id"])})
            assert gridfs["filename"] == "some_archive.zip"

        raw = self.get('/contributors/id_test/data_sources/{}'.format(data_source.get('id')))
        self.assert_sucessful_call(raw)
        ds = self.json_to_dict(raw)['data_sources'][0]
        assert 'id' in ds['data_sets'][0]
        assert ds['status'] == DATA_SOURCE_STATUS_UPDATED
        assert not ds['fetch_started_at']
        assert ds['updated_at']
        assert ds['validity_period']
