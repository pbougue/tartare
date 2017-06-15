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
import mock
import pytest
import ftplib
from tests.utils import mock_urlretrieve, mock_requests_post
from tests.integration.test_mechanism import TartareFixture
import json


class TestDataPublisher(TartareFixture):
    def test_publish_unknwon_coverage(self):
        resp = self.post("/coverages/default/environments/production/actions/publish")
        assert resp.status_code == 404
        r = self.to_json(resp)
        assert r['message'] == 'Object Not Found'
        assert r['error'] == 'Coverage not found: default'

    def test_publish_unknwon_environment(self):
        coverage = {
            "contributors": [
                "fr-idf"
            ],
            "environments": {
                "production": {
                    "name": "production",
                    "publication_platforms": [
                        {
                            "type": "navitia",
                            "protocol": "http",
                            "url": "http://bob/v0/jobs"
                        }
                    ]
                }
            },
            "id": "default",
            "name": "default"
        }
        #Create Coverage
        resp = self.post("/coverages", json.dumps(coverage))
        assert resp.status_code == 201

        #Launch data update
        resp = self.post("/coverages/default/environments/bob/actions/publish")
        assert resp.status_code == 404
        r = self.to_json(resp)
        assert r['message'] == 'Object Not Found'
        assert r['error'] == 'Environment not found: bob'

    def test_publish_coverage_without_export(self):
        coverage = {
            "contributors": [
                "fr-idf"
            ],
            "environments": {
                "production": {
                    "name": "production",
                    "publication_platforms": [
                        {
                            "type": "navitia",
                            "protocol": "http",
                            "url": "http://bob/v0/jobs"
                        }
                    ]
                }
            },
            "id": "default",
            "name": "default"
        }
        #Create Coverage
        resp = self.post("/coverages", json.dumps(coverage))
        assert resp.status_code == 201

        #Launch data update
        resp = self.post("/coverages/default/environments/production/actions/publish")
        assert resp.status_code == 404
        r = self.to_json(resp)
        assert r['message'] == 'Object Not Found'
        assert r['error'] == 'Coverage default without export.'

    def _create_contributor(self, id, url = 'bob'):
        contributor = {
            "id": id,
            "name": id,
            "data_prefix": "AAA",
            "data_sources": [
                {
                    "name": "gtfs data",
                    "data_format": "gtfs",
                    "input": {
                        "type": "url",
                        "url": url
                    }
                }
            ]
        }
        resp = self.post("/contributors", json.dumps(contributor))
        assert resp.status_code == 201

    def _create_coverage(self, id, contributor_id, publication_platform):
        coverage = {
            "contributors": [
                contributor_id
            ],
            "environments": {
                "production": {
                    "name": "production",
                    "publication_platforms": [
                        publication_platform
                    ]
                }
            },
            "id": id,
            "name": id
        }

        resp = self.post("/coverages", json.dumps(coverage))
        assert resp.status_code == 201

    @mock.patch('urllib.request.urlretrieve', side_effect=mock_urlretrieve)
    def test_publish_ok(self, urlretrieve_func):
        contributor_id = 'fr-idf'
        coverage_id = 'default'
        publication_platform = {
                            "type": "navitia",
                            "protocol": "http",
                            "url": "http://bob/v0/jobs"
                        }
        self._create_contributor(contributor_id)
        self._create_coverage(coverage_id, contributor_id, publication_platform)

        # Launch contributor export
        resp = self.post("/contributors/{}/actions/export".format(contributor_id))
        assert resp.status_code == 201

        # List contributor export
        r = self.to_json(self.get("/contributors/fr-idf/exports"))
        exports = r["exports"]
        assert len(exports) == 1
        assert exports[0]["validity_period"]["start_date"] == "2015-03-25"
        assert exports[0]["validity_period"]["end_date"] == "2015-08-26"

        assert exports[0]["gridfs_id"]
        data_sources = exports[0]["data_sources"]
        assert len(data_sources) == 1
        assert data_sources[0]["validity_period"]

        #Launch coverage export
        resp = self.post("/coverages/default/actions/export")
        # Launch coverage export
        resp = self.post("/coverages/{}/actions/export".format(coverage_id))
        assert resp.status_code == 201

        # List coverage export
        r = self.to_json(self.get("/coverages/default/exports"))
        exports = r["exports"]
        assert len(exports) == 1
        assert exports[0]["validity_period"]["start_date"] == "2015-03-25"
        assert exports[0]["validity_period"]["end_date"] == "2015-08-26"
        assert exports[0]["gridfs_id"]
        contributors = exports[0]["contributors"]
        assert len(contributors) == 1
        assert contributors[0]["validity_period"]
        assert len(contributors[0]["data_sources"]) == 1
        assert contributors[0]["data_sources"][0]["validity_period"]

        #Launch data update
        # Launch data update
        with mock.patch('requests.post', mock_requests_post):
            resp = self.post("/coverages/default/environments/production/actions/publish")
            assert resp.status_code == 200

    def test_publish_ftp_ods(self, init_http_download_server, init_ftp_upload_server):
        contributor_id = 'fr-idf'
        coverage_id = 'default'
        ftp_username = 'tartare_user'
        ftp_password = 'tartare_password'
        filename = 'some_archive.zip'
        self._create_contributor(contributor_id, 'http://{ip_http_download}/{filename}'.format(ip_http_download=init_http_download_server.ip_addr, filename=filename))
        # see password : tests/fixtures/authent/ftp_upload_users/pureftpd.passwd
        publication_platform = {
            "name": "ods",
            "type": "ftp",
            "url": init_ftp_upload_server.ip_addr,
            "authent": {
                "username": ftp_username,
                "password": ftp_password
            }
        }
        self._create_coverage(coverage_id, contributor_id, publication_platform)

        resp = self.post("/contributors/{}/actions/export".format(contributor_id))
        assert resp.status_code == 201

        resp = self.post("/coverages/{}/actions/export".format(coverage_id))
        assert resp.status_code == 201

        resp = self.post("/coverages/{}/environments/production/actions/publish".format(coverage_id))
        assert resp.status_code == 200
        # check if the file was successfully uploaded
        session = ftplib.FTP(init_ftp_upload_server.ip_addr, ftp_username, ftp_password)
        try:
            files = session.nlst()
            print(files)
        except ftplib.error_perm as resp:
            if str(resp) == "550 No files found":
                pytest.fail('uploaded file was not found on ftp server')
            else:
                raise
        session.quit()
