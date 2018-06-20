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


import json
from tests.integration.test_mechanism import TartareFixture
from tests.utils import assert_text_files_equals, _get_file_fixture_full_path

file_used = "some_archive.zip"
fixtures_file = _get_file_fixture_full_path('gtfs/{}'.format(file_used))


class TestGetFiles(TartareFixture):

    def test_get_files_invalid_file_id(self):
        resp = self.get('/files/aa/download', follow_redirects=True)
        assert resp.status_code == 400
        json_resp = self.json_to_dict(resp)
        assert json_resp.get('error') == 'invalid file id, you give aa'

    def test_get_files(self, init_http_download_server, init_ftp_upload_server, contributor):
        url = self.format_url(ip=init_http_download_server.ip_addr, filename=file_used)

        contributor['data_sources'].append({
            "id": "to_process",
            "name": "bobette",
            "data_format": "gtfs",
            "input": {
                "type": "auto",
                "url": url,
                "frequency": {
                    "type": "daily",
                    "hour_of_day": 20
                }
            }
        })
        self.put('/contributors/id_test', params=self.dict_to_json(contributor))

        coverage = {
            "input_data_source_ids": ['to_process'],
            "environments": {
                "production": {
                    "name": "production",
                    "sequence": 0,
                    "publication_platforms": [
                        {
                            "sequence": 0,
                            "type": "navitia",
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

        # Coverage added
        raw = self.post('/coverages', params=json.dumps(coverage))
        assert raw.status_code == 201
        json_coverage = self.json_to_dict(raw)
        assert len(json_coverage['coverages']) == 1

        self.contributor_export(contributor['id'])

        # Get file for contributor export
        raw = self.get('contributors/{contrib_id}/exports'.format(contrib_id=contributor['id']))
        assert raw.status_code == 200
        exports = self.json_to_dict(raw).get('exports')
        assert len(exports) == 1

        resp = self.get('/files/{gridfs_id}/download'.format(gridfs_id=exports[0]['data_sources'][0]['gridfs_id']), follow_redirects=True)
        assert resp.status_code == 200
        assert_text_files_equals(resp.data, fixtures_file)

        raw = self.post('/coverages/{}/actions/export?current_date=2015-08-10'.format(coverage['id']), {})
        assert raw.status_code == 201

        raw = self.get('coverages/{coverage_id}/exports'.format(coverage_id=coverage['id']))
        assert raw.status_code == 200
        exports = self.json_to_dict(raw).get('exports')
        assert len(exports) == 1

        resp = self.get('/files/{gridfs_id}/download'.format(gridfs_id=exports[0]['gridfs_id']), follow_redirects=True)
        assert resp.status_code == 200
        assert_text_files_equals(resp.data, fixtures_file)

        resp = self.get('/coverages/{coverage_id}'.format(coverage_id=coverage['id']))
        assert raw.status_code == 200
        coverages = self.json_to_dict(resp).get('coverages')
        assert len(exports) == 1
        environments = coverages[0]['environments']
        resp = self.get('/files/{gridfs_id}/download'.
                        format(gridfs_id=environments['production']['current_ntfs_id']), follow_redirects=True)
        assert resp.status_code == 200
        assert_text_files_equals(resp.data, fixtures_file)
