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

import os
from tests.integration.test_mechanism import TartareFixture
from tartare import app, mongo
from bson.objectid import ObjectId

fixtures_path = os.path.realpath('tests/fixtures/gtfs/some_archive.zip')


class TestDatasetApi(TartareFixture):
    def test_post_dataset_of_unknown_contributor(self):
        raw = self.post('/contributors/unknown/data_sources/unknown/datasets')
        assert raw.status_code == 404
        r = self.to_json(raw)
        assert r["error"] == "Bad contributor unknown"

    def test_post_dataset_with_unknown_data_source(self, contributor):
        raw = self.post('/contributors/{}/data_sources/unknown/datasets'.format(contributor.get('id')))
        assert raw.status_code == 404
        r = self.to_json(raw)
        assert r["error"] == "Data source unknown not found."

    def test_post_dataset_without_file(self, data_source):
        raw = self.post('/contributors/id_test/data_sources/{}/datasets'.format(data_source.get('id')))
        assert raw.status_code == 400
        r = self.to_json(raw)
        assert r["error"] == "No file provided."

    def test_post_dataset_with_bad_file_param(self, data_source):
        with open(fixtures_path, 'rb') as file:
            raw = self.post('/contributors/id_test/data_sources/{}/datasets'.format(data_source.get('id')),
                            params={'bad_param': file},
                            headers={})
            assert raw.status_code == 400
            r = self.to_json(raw)
            assert r["error"] == 'File provided with bad param ("file" param expected).'

    def test_post_dataset(self,  data_source):
        with open(fixtures_path, 'rb') as file:
            raw = self.post('/contributors/id_test/data_sources/{}/datasets'.format(data_source.get('id')),
                            params={'file': file},
                            headers={})
            assert raw.status_code == 200
            r = self.to_json(raw)
            assert len(r["datasets"]) == 1

            with app.app_context():
                gridfs = mongo.db['fs.files'].find_one({'_id': ObjectId(r["datasets"][0]["gridfs_id"])})
                assert gridfs["filename"] == "some_archive.zip"
