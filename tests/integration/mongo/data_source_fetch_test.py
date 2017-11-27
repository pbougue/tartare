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
import tempfile

import os

from tartare.core import models
from tartare.core.gridfs_handler import GridFsHandler
from tests.integration.test_mechanism import TartareFixture
from tartare import app, mongo

from tests.utils import _get_file_fixture_full_path, assert_files_equals

fixtures_path = _get_file_fixture_full_path('gtfs/some_archive.zip')


class TestDataSourceFetchAction(TartareFixture):
    def test_fetch_with_unknown_contributor(self):
        raw = self.post('/contributors/unknown/data_sources/unknown/actions/fetch')
        assert raw.status_code == 404
        r = self.to_json(raw)
        assert r["error"] == "Bad contributor unknown"

    def test_fetch_with_unknown_data_source(self, contributor):
        raw = self.post('/contributors/id_test/data_sources/unknown/actions/fetch')
        assert raw.status_code == 404
        r = self.to_json(raw)
        assert r["error"] == "Data source unknown not found for contributor id_test."

    def test_fetch_ok(self, init_http_download_server, contributor):
        ip = init_http_download_server.ip_addr
        url = self.format_url(ip, 'sample_1.zip')
        raw = self.post('/contributors/id_test/data_sources',
                        params='{"name": "bobette", "data_format": "gtfs", "input": {"type": "url", "url": "' + url + '"}}')
        assert raw.status_code == 201

        json_response = self.to_json(raw)
        data_source_id = json_response['data_sources'][0]['id']

        raw = self.post('/contributors/{}/data_sources/{}/actions/fetch'.format(contributor['id'], data_source_id))

        self.assert_sucessful_call(raw, 204)

        with app.app_context():
            raw = mongo.db[models.DataSourceFetched.mongo_collection].find_one({
                'contributor_id': contributor['id'],
                'data_source_id': json_response['data_sources'][0]['id']
            })

            # Test that source file and saved file are the same
            gridout = GridFsHandler().get_file_from_gridfs(raw['gridfs_id'])
            expected_path = _get_file_fixture_full_path('gtfs/sample_1.zip')

            with tempfile.TemporaryDirectory() as path:
                gridout_path = os.path.join(path, gridout.filename)
                with open(gridout_path, 'wb+') as f:
                    f.write(gridout.read())
                    assert_files_equals(gridout_path, expected_path)

    def test_fetch_invalid_type(self, init_http_download_server, contributor):
        ip = init_http_download_server.ip_addr
        url = "http://{ip}/{filename}".format(ip=ip, filename='unknown.zip')
        raw = self.post('/contributors/id_test/data_sources',
                        params='{"name": "bobette", "data_format": "gtfs", "input": {"type": "manual", "url": "' + url + '"}}')
        assert raw.status_code == 201

        json_response = self.to_json(raw)
        data_source_id = json_response['data_sources'][0]['id']

        response = self.post('/contributors/{}/data_sources/{}/actions/fetch'.format(contributor['id'], data_source_id))
        json_response = self.to_json(response)

        assert response.status_code == 400, print(self.to_json(response))
        assert json_response['error'] == 'Data source type should be url.'

    def test_fetch_invalid_url(self, init_http_download_server, contributor):
        ip = init_http_download_server.ip_addr
        url = "http://{ip}/{filename}".format(ip=ip, filename='unknown.zip')
        raw = self.post('/contributors/id_test/data_sources',
                        params='{"name": "bobette", "data_format": "gtfs", "input": {"type": "url", "url": "' + url + '"}}')
        assert raw.status_code == 201

        json_response = self.to_json(raw)
        data_source_id = json_response['data_sources'][0]['id']

        response = self.post('/contributors/{}/data_sources/{}/actions/fetch'.format(contributor['id'], data_source_id))
        json_response = self.to_json(response)

        assert response.status_code == 500, print(self.to_json(response))
        assert json_response['error'].startswith('Fetching {} failed:'.format(url))
