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
from freezegun import freeze_time

import tempfile
import os
import json
from tests.integration.test_mechanism import TartareFixture
from tartare.helper import get_md5_content_file

file_used = "some_archive.zip"
fixtures_file = os.path.realpath('tests/fixtures/gtfs/{}'.format(file_used))


class TestGetFiles(TartareFixture):

    def _assert_files(self, file):
        with tempfile.TemporaryDirectory() as path_tmp:
            dest_zip = '{}/gtfs.zip'.format(path_tmp)
            f = open(dest_zip, 'wb')
            f.write(file)
            f.close()
            assert get_md5_content_file(dest_zip) == get_md5_content_file(fixtures_file)

    def test_get_files_invalid_file_id(self):
        resp = self.get('/contributors/AA/exports/BB/files/aa', follow_redirects=True)
        assert resp.status_code == 400
        json_resp = self.to_json(resp)
        assert json_resp.get('error') == 'Invalid file id, you give aa'

    def test_get_files_invalid_export_id(self):
        resp = self.get('/contributors/AA/exports/BB/files/7ffab2293d484eeaaa2c22f8', follow_redirects=True)
        assert resp.status_code == 400
        json_resp = self.to_json(resp)
        assert json_resp.get('error') == 'Invalid export id, you give BB'

    def test_get_files_contributor_not_found(self):
        resp = self.get('/contributors/AA/exports/7ffab229-3d48-4eea-aa2c-22f8680230b6/'
                        'files/7ffab2293d484eeaaa2c22f8', follow_redirects=True)
        assert resp.status_code == 404
        json_resp = self.to_json(resp)
        assert json_resp.get('error') == 'Contributor export not found.'

    def test_get_files_coverage_not_found(self):
        resp = self.get('/coverages/AA/exports/7ffab229-3d48-4eea-aa2c-22f8680230b6/'
                        'files/7ffab2293d484eeaaa2c22f8', follow_redirects=True)
        assert resp.status_code == 404
        json_resp = self.to_json(resp)
        assert json_resp.get('error') == 'Coverage not found.'

    @freeze_time("2015-08-10")
    def test_get_files(self, init_http_download_server, init_ftp_upload_server, contributor):
        ip = init_http_download_server.ip_addr
        url = "http://{ip}/{filename}".format(ip=ip, filename=file_used)

        coverage = {
            "contributors": [contributor['id']],
            "environments": {
                "production": {
                    "name": "production",
                    "sequence": 0,
                    "publication_platforms": [
                        {
                            "sequence": 0,
                            "type": "ods",
                            "protocol": "ftp",
                            "url": init_ftp_upload_server.ip_addr,
                            "options": {
                                "authent": {
                                    "username": init_ftp_upload_server.user,
                                    "password": init_ftp_upload_server.password
                                }
                            }
                        }
                    ]
                }
            },
            "id": "default",
            "name": "default"
        }
        # Data sources added
        raw = self.post('/contributors/id_test/data_sources',
                        params='{"id": "to_process", "name": "bobette", '
                               '"data_format": "gtfs", "input": {"type": "url", "url": "' + url + '"}}')
        assert raw.status_code == 201


        # Coverage added
        raw = self.post('/coverages', params=json.dumps(coverage))
        assert raw.status_code == 201
        json_coverage = self.to_json(raw)
        assert len(json_coverage['coverages']) == 1


        raw = self.post('/contributors/{}/actions/export'.format(contributor['id']), {})
        assert raw.status_code == 201
        job = self.to_json(raw).get('job')

        raw_job = self.get('contributors/{contrib_id}/jobs/{job_id}'.
                           format(contrib_id=contributor['id'], job_id=job['id']))

        job = self.to_json(raw_job)['jobs'][0]
        assert job['state'] == 'done', print(job)


        raw = self.get('contributors/{contrib_id}/exports'.format(contrib_id=contributor['id']))
        assert raw.status_code == 200
        exports = self.to_json(raw).get('exports')
        assert len(exports) == 1


        resp = self.get('/contributors/{contrib_id}/exports/{export_id}/files/{gridfs_id}'.
                        format(contrib_id=contributor['id'], export_id=exports[0]['id'],
                               gridfs_id=exports[0]['gridfs_id']), follow_redirects=True)
        assert resp.status_code == 200

        self._assert_files(resp.data)

        # Get file for contributor export
        raw = self.get('contributors/{contrib_id}/exports'.format(contrib_id=contributor['id']))
        assert raw.status_code == 200
        exports = self.to_json(raw).get('exports')
        assert len(exports) == 1


        resp = self.get('/contributors/{contrib_id}/exports/{export_id}/files/{gridfs_id}'.
                        format(contrib_id=contributor['id'], export_id=exports[0]['id'],
                               gridfs_id=exports[0]['gridfs_id']), follow_redirects=True)
        assert resp.status_code == 200
        self._assert_files(resp.data)


        raw = self.get('coverages/{coverage_id}/exports'.format(coverage_id=coverage['id']))
        assert raw.status_code == 200
        exports = self.to_json(raw).get('exports')
        assert len(exports) == 1


        resp = self.get('/coverages/{coverage_id}/exports/{export_id}/files/{gridfs_id}'.
                        format(coverage_id=coverage['id'], export_id=exports[0]['id'],
                               gridfs_id=exports[0]['gridfs_id']), follow_redirects=True)
        assert resp.status_code == 200
        self._assert_files(resp.data)

        resp = self.get('/coverages/{coverage_id}'.format(coverage_id=coverage['id']))
        assert raw.status_code == 200
        coverages = self.to_json(resp).get('coverages')
        assert len(exports) == 1
        environments = coverages[0]['environments']
        resp = self.get('/coverages/{coverage_id}/environments/{environment_id}/files/{gridfs_id}'.
                        format(coverage_id=coverage['id'], environment_id='production',
                               gridfs_id=environments['production']['current_ntfs_id']), follow_redirects=True)
        assert resp.status_code == 200
        self._assert_files(resp.data)
