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
import tempfile

from tartare import app, mongo
from tartare.core import models
from tartare.core.gridfs_handler import GridFsHandler
from tests.integration.test_mechanism import TartareFixture
from tests.utils import _get_file_fixture_full_path, assert_files_equals

fixtures_path = _get_file_fixture_full_path('gtfs/some_archive.zip')


class TestDataSourceFetchAction(TartareFixture):
    def test_fetch_with_unknown_contributor(self):
        raw = self.post('/contributors/unknown/data_sources/unknown/actions/fetch')
        assert raw.status_code == 404
        r = self.json_to_dict(raw)
        assert r["error"] == "bad contributor unknown"

    def test_fetch_with_unknown_data_source(self, contributor):
        raw = self.post('/contributors/id_test/data_sources/unknown/actions/fetch')
        assert raw.status_code == 404
        r = self.json_to_dict(raw)
        assert r["error"] == "data source unknown not found for contributor id_test"

    def test_fetch_ok(self, init_http_download_server, contributor):
        ip = init_http_download_server.ip_addr
        url = self.format_url(ip, 'sample_1.zip')
        raw = self.post('/contributors/id_test/data_sources',
                        params='{"name": "bobette", "data_format": "gtfs", "input": {"type": "url", "url": "' + url + '"}}')
        assert raw.status_code == 201

        json_response = self.json_to_dict(raw)
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

        json_response = self.json_to_dict(raw)
        data_source_id = json_response['data_sources'][0]['id']

        response = self.post('/contributors/{}/data_sources/{}/actions/fetch'.format(contributor['id'], data_source_id))
        json_response = self.json_to_dict(response)

        assert response.status_code == 400, print(self.json_to_dict(response))
        assert json_response['error'] == 'data source type should be url'

    def test_fetch_invalid_url(self, init_http_download_server, contributor):
        url = self.format_url(init_http_download_server.ip_addr, 'unknown.zip', path='')
        params = {
            "name": "bobette",
            "data_format": "gtfs",
            "input": {
                "type": "url",
                "url": url
            }
        }
        raw = self.post('/contributors/id_test/data_sources', self.dict_to_json(params))
        self.assert_sucessful_create(raw)

        json_response = self.json_to_dict(raw)
        data_source_id = json_response['data_sources'][0]['id']

        response = self.post('/contributors/{}/data_sources/{}/actions/fetch'.format(contributor['id'], data_source_id))
        json_response = self.json_to_dict(response)

        assert response.status_code == 500, print(self.json_to_dict(response))
        assert json_response['error'].startswith('fetching {} failed:'.format(url))

    def test_fetch_authent_in_http_url_ok(self, init_http_download_authent_server):
        props = init_http_download_authent_server.properties
        url = "http://{user}:{password}@{ip}/{alias}gtfs/{filename}".format(
            user=props['USERNAME'],
            password=props['PASSWORD'],
            alias=props['ROOT'],
            ip=init_http_download_authent_server.ip_addr,
            filename='some_archive.zip'
        )
        self.init_contributor('cid', 'dsid', url)
        self.fetch_data_source('cid', 'dsid')

    def test_fetch_authent_in_http_url_unauthorized(self, init_http_download_authent_server):
        props = init_http_download_authent_server.properties
        contrib_cpt = 0
        for user, password in [('unknown', props['PASSWORD']), (props['USERNAME'], 'wrong_one'),
                               ('unknown', 'wrong_one')]:
            url = "http://{user}:{password}@{ip}/{alias}gtfss/{filename}".format(
                user=user,
                password=password,
                alias=props['ROOT'],
                ip=init_http_download_authent_server.ip_addr,
                filename='some_archive.zip'
            )
            cid = 'cid_{}'.format(contrib_cpt)
            dsid = 'dsid_{}'.format(contrib_cpt)
            self.init_contributor('cid_{}'.format(contrib_cpt), 'dsid_{}'.format(contrib_cpt), url)
            contrib_cpt += 1
            raw = self.fetch_data_source(cid, dsid, check_success=False)
            response_body = self.assert_failed_call(raw, 500)
            assert response_body == {
                'error': 'fetching {} failed: error during download of file: HTTP Error 401: Unauthorized'.format(url),
                'message': 'Internal Server Error'
            }

    def test_fetch_authent_in_http_url_not_found(self, init_http_download_authent_server):
        props = init_http_download_authent_server.properties
        url = "http://{user}:{password}@{ip}/{alias}gtfs/unknown.zip".format(
            user=props['USERNAME'],
            password=props['PASSWORD'],
            alias=props['ROOT'],
            ip=init_http_download_authent_server.ip_addr
        )
        cid = 'cid'
        dsid = 'dsid'
        self.init_contributor('{}'.format(cid), '{}'.format(dsid), url)
        raw = self.fetch_data_source(cid, dsid, check_success=False)
        response_body = self.assert_failed_call(raw, 500)
        assert response_body == {
            'error': 'fetching {} failed: error during download of file: HTTP Error 404: Not Found'.format(url),
            'message': 'Internal Server Error'
        }
