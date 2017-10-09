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
import copy
import ftplib
import json
import os
import tempfile
from zipfile import ZipFile

import mock
import pytest
from freezegun import freeze_time

from tests.integration.test_mechanism import TartareFixture
from tests.utils import mock_urlretrieve, mock_requests_post, assert_files_equals, get_response


class TestDataPublisher(TartareFixture):
    def test_publish_unknwon_coverage(self):
        resp = self.post("/coverages/default/environments/production/actions/publish")
        assert resp.status_code == 404
        r = self.to_json(resp)
        assert r[
                   'message'] == 'Object Not Found. You have requested this URI [/coverages/default/environments/production/actions/publish] but did you mean /coverages/<string:coverage_id>/environments/<string:environment_id>/actions/publish ?'
        assert r['error'] == 'Coverage not found: default'

    def test_publish_unknwon_environment(self, contributor):
        coverage = {
            "contributors": [
                "id_test"
            ],
            "environments": {
                "production": {
                    "name": "production",
                    "sequence": 0,
                    "publication_platforms": [
                        {
                            "sequence": 0,
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
        # Create Coverage
        resp = self.post("/coverages", json.dumps(coverage))
        assert resp.status_code == 201

        # Launch data update
        resp = self.post("/coverages/default/environments/bob/actions/publish")
        assert resp.status_code == 404
        r = self.to_json(resp)
        assert r[
                   'message'] == 'Object Not Found. You have requested this URI [/coverages/default/environments/bob/actions/publish] but did you mean /coverages/<string:coverage_id>/environments/<string:environment_id>/actions/publish ?'
        assert r['error'] == 'Environment not found: bob'

    def test_publish_coverage_without_export(self, contributor):
        coverage = {
            "contributors": [
                "id_test"
            ],
            "environments": {
                "production": {
                    "name": "production",
                    "sequence": 0,
                    "publication_platforms": [
                        {
                            "sequence": 0,
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
        # Create Coverage
        resp = self.post("/coverages", json.dumps(coverage))
        assert resp.status_code == 201

        # Launch data update
        resp = self.post("/coverages/default/environments/production/actions/publish")
        assert resp.status_code == 404
        r = self.to_json(resp)
        assert r[
                   'message'] == 'Object Not Found. You have requested this URI [/coverages/default/environments/production/actions/publish] but did you mean /coverages/<string:coverage_id>/environments/<string:environment_id>/actions/publish ?'
        assert r['error'] == 'Coverage default without export.'

    def _create_contributor(self, id, url='bob'):
        contributor = {
            "id": id,
            "name": "fr idf",
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
        return resp

    def _create_coverage(self, id, contributor_id, publication_platform, license=None):
        coverage = {
            "contributors": [
                contributor_id
            ],
            "environments": {
                "production": {
                    "name": "production",
                    "sequence": 0,
                    "publication_platforms": [
                        publication_platform
                    ]
                }
            },
            "id": id,
            "name": id
        }
        if license:
            coverage['license'] = license

        resp = self.post("/coverages", json.dumps(coverage))
        assert resp.status_code == 201
        return resp

    @freeze_time("2015-08-10")
    @mock.patch('urllib.request.urlretrieve', side_effect=mock_urlretrieve)
    def test_publish_ok(self, urlretrieve_func):
        contributor_id = 'fr-idf'
        coverage_id = 'default'
        publication_platform = {
            "sequence": 0,
            "type": "navitia",
            "protocol": "http",
            "url": "http://bob/v0/jobs"
        }
        self._create_contributor(contributor_id)
        self._create_coverage(coverage_id, contributor_id, publication_platform)

        # Launch contributor export
        with mock.patch('requests.post', mock_requests_post):
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

    @freeze_time("2015-08-10")
    def test_publish_ftp_ods(self, init_http_download_server, init_ftp_upload_server):
        contributor_id = 'fr-idf'
        coverage_id = 'default'
        filename = 'some_archive.zip'
        self._create_contributor(contributor_id, 'http://{ip_http_download}/{filename}'.format(
            ip_http_download=init_http_download_server.ip_addr, filename=filename))
        publication_platform = {
            "sequence": 0,
            "type": "ods",
            "protocol": "ftp",
            # url without ftp:// works as well
            "url": init_ftp_upload_server.ip_addr,
            "options": {
                "authent": {
                    "username": init_ftp_upload_server.user,
                    "password": init_ftp_upload_server.password
                }
            }
        }
        self._create_coverage(coverage_id, contributor_id, publication_platform)

        resp = self.post("/contributors/{}/actions/export".format(contributor_id))
        assert resp.status_code == 201

        # check if the file was successfully uploaded
        session = ftplib.FTP(init_ftp_upload_server.ip_addr, init_ftp_upload_server.user,
                             init_ftp_upload_server.password)
        directory_content = session.nlst()
        assert len(directory_content) == 1
        assert '{coverage_id}.zip'.format(coverage_id=coverage_id) in directory_content
        session.delete('{coverage_id}.zip'.format(coverage_id=coverage_id))
        session.quit()

    @freeze_time("2015-08-10")
    def test_publish_ftp_ods_with_directory(self, init_http_download_server, init_ftp_upload_server):
        contributor_id = 'fr-idf'
        coverage_id = 'default'
        ftp_username = 'tartare_user'
        ftp_password = 'tartare_password'
        filename = 'some_archive.zip'
        directory = "/ods"

        session = ftplib.FTP(init_ftp_upload_server.ip_addr, ftp_username, ftp_password)
        # Create a directory in the ftp
        session.mkd(directory)

        self._create_contributor(contributor_id, 'http://{ip_http_download}/{filename}'.format(
            ip_http_download=init_http_download_server.ip_addr, filename=filename))
        # see password : tests/fixtures/authent/ftp_upload_users/pureftpd.passwd
        publication_platform = {
            "sequence": 0,
            "type": "ods",
            "protocol": "ftp",
            "url": "ftp://" + init_ftp_upload_server.ip_addr,
            "options": {
                "authent": {
                    "username": ftp_username,
                    "password": ftp_password
                },
                "directory": directory
            }
        }
        self._create_coverage(coverage_id, contributor_id, publication_platform)

        resp = self.post("/contributors/{}/actions/export".format(contributor_id))
        assert resp.status_code == 201

        # check if the file was successfully uploaded
        directory_content = session.nlst(directory)
        assert len(directory_content) == 1
        assert '{coverage_id}.zip'.format(coverage_id=coverage_id) in directory_content
        session.delete('{directory}/{coverage_id}.zip'.format(directory=directory, coverage_id=coverage_id))
        session.rmd(directory)

    @pytest.mark.parametrize("license_url,license_name,sample_data,coverage_id", [
        ('http://license.org/mycompany', 'my license', 'some_archive.zip', 'fr-idf-test'),
        (None, None, 'sample_1.zip', 'my-coverage-id')
    ])
    @freeze_time("2015-08-10")
    def test_publish_ftp_ods_with_metadata(self, init_http_download_server, init_ftp_upload_server, fixture_dir,
                                           license_url, license_name, sample_data, coverage_id):
        contributor_id = 'whatever'
        self._create_contributor(contributor_id, 'http://{ip_http_download}/{filename}'.format(
            ip_http_download=init_http_download_server.ip_addr, filename=sample_data))
        publication_platform = {
            "sequence": 0,
            "type": "ods",
            "protocol": "ftp",
            "url": "ftp://" + init_ftp_upload_server.ip_addr,
            "options": {
                "authent": {
                    "username": init_ftp_upload_server.user,
                    "password": init_ftp_upload_server.password
                }
            }
        }
        license = {
            "name": license_name,
            "url": license_url
        } if license_name or license_url else None

        self._create_coverage(coverage_id, contributor_id, publication_platform, license)

        resp = self.post("/contributors/{}/actions/export".format(contributor_id))
        assert resp.status_code == 201
        # check if the file was successfully uploaded
        session = ftplib.FTP(init_ftp_upload_server.ip_addr, init_ftp_upload_server.user,
                             init_ftp_upload_server.password)
        directory_content = session.nlst()
        expected_filename = '{coverage_id}.zip'.format(coverage_id=coverage_id)
        assert len(directory_content) == 1
        assert expected_filename in directory_content
        # check that meta data from file on ftp server are correct
        with tempfile.TemporaryDirectory() as tmp_dirname:
            transfered_full_name = os.path.join(tmp_dirname, 'transfered_file.zip')
            with open(transfered_full_name, 'wb') as dest_file:
                session.retrbinary('RETR {expected_filename}'.format(expected_filename=expected_filename),
                                   dest_file.write)
                session.delete(expected_filename)
            with ZipFile(transfered_full_name, 'r') as ods_zip:
                metadata_file_name = '{coverage_id}.txt'.format(coverage_id=coverage_id)
                ods_zip.extract(metadata_file_name, tmp_dirname)
                fixture = os.path.join(fixture_dir, 'metadata', metadata_file_name)
                metadata = os.path.join(tmp_dirname, metadata_file_name)
                assert_files_equals(metadata, fixture)
        session.quit()

    def test_config_user_password(self, contributor):
        user_to_set = 'user'
        coverage_id = 'default'
        publication_platform = {
            "sequence": 0,
            "type": "ods",
            "protocol": "ftp",
            "url": "whatever.com",
            "options": {
                "authent": {
                    "username": user_to_set,
                    "password": 'my_password'
                }
            }
        }
        self._create_coverage(coverage_id, contributor['id'], publication_platform)
        resp = self.get('/coverages/{cov_id}'.format(cov_id=coverage_id))
        r = self.to_json(resp)['coverages'][0]
        pub_platform = r['environments']['production']['publication_platforms'][0]
        assert 'password' not in pub_platform['options']['authent']
        assert 'username' in pub_platform['options']['authent']
        assert user_to_set == pub_platform['options']['authent']['username']

    @freeze_time("2015-08-10")
    def test_publish_stops_to_ftp(self, init_http_download_server, init_ftp_upload_server):
        contributor_id = 'fr-idf'
        coverage_id = 'default'
        filename = 'some_archive.zip'
        self._create_contributor(contributor_id, 'http://{ip_http_download}/{filename}'.format(
            ip_http_download=init_http_download_server.ip_addr, filename=filename))
        publication_platform = {
            "sequence": 0,
            "type": "stop_area",
            "protocol": "ftp",
            "url": "ftp://" + init_ftp_upload_server.ip_addr,
            "options": {
                "authent": {
                    "username": init_ftp_upload_server.user,
                    "password": init_ftp_upload_server.password
                }
            }
        }
        self._create_coverage(coverage_id, contributor_id, publication_platform)

        resp = self.post("/contributors/{}/actions/export".format(contributor_id))
        assert resp.status_code == 201

        # check if the file was successfully uploaded
        session = ftplib.FTP(init_ftp_upload_server.ip_addr, init_ftp_upload_server.user,
                             init_ftp_upload_server.password)
        directory_content = session.nlst()
        assert len(directory_content) == 1
        assert '{coverage_id}_stops.txt'.format(coverage_id=coverage_id) in directory_content
        session.delete('{coverage_id}_stops.txt'.format(coverage_id=coverage_id))
        session.quit()

    @freeze_time("2015-08-10")
    @mock.patch('requests.post', side_effect=[get_response(200), get_response(200), get_response(200)])
    def test_publish_environment_respect_sequence_order(self, mock_post, init_http_download_server):
        contributor_id = 'contrib-seq'
        publication_envs = ['integration', 'production', 'preproduction']
        url = "http://whatever.{env}/v0/jobs/il"
        self._create_contributor(contributor_id, 'http://{ip_http_download}/{filename}'.format(
            ip_http_download=init_http_download_server.ip_addr, filename='sample_1.zip'))
        coverage = {
            "contributors": [
                contributor_id
            ],
            "environments": {},
            "id": 'cov-sequence',
            "name": 'cov-sequence'
        }
        publication_platform = {
            "sequence": 0,
            "type": "navitia",
            "protocol": "http",
            "url": url
        }
        for idx, environment in enumerate(publication_envs):
            temp_platform = copy.copy(publication_platform)
            temp_platform['url'] = temp_platform['url'].format(env=environment)
            coverage['environments'][environment] = {
                "name": environment,
                "sequence": idx,
                "publication_platforms": [
                    temp_platform
                ]
            }

        resp = self.post("/coverages", json.dumps(coverage))
        self.assert_sucessful_call(resp, 201)

        resp = self.post("/contributors/{}/actions/export".format(contributor_id))
        self.assert_sucessful_call(resp, 201)

        for idx, environment in enumerate(publication_envs):
            assert url.format(env=environment) == mock_post.call_args_list[idx][0][0]

    @freeze_time("2015-08-10")
    @mock.patch('requests.post', side_effect=[get_response(200),
                                              get_response(200),
                                              get_response(200),
                                              get_response(200),
                                              get_response(200),
                                              ])
    def test_publish_platform_respect_sequence_order(self, mock_post, init_http_download_server):
        contributor_id = 'contrib-seq'
        # we will create 5 platform for prod env with different sequences
        sequences = [4, 0, 3, 2, 1]
        url = "http://whatever.sequence.{seq}/v0/jobs/il"
        self._create_contributor(contributor_id, 'http://{ip_http_download}/{filename}'.format(
            ip_http_download=init_http_download_server.ip_addr, filename='sample_1.zip'))

        publication_platforms = []
        for idx in sequences:
            # trick: url of platform contains sequence number
            publication_platforms.append({
                "type": "navitia",
                "sequence": idx,
                "protocol": "http",
                "url": url.format(seq=idx)
            })
        coverage = {
            "contributors": [
                contributor_id
            ],
            "environments": {
                "production": {
                    "name": 'production',
                    "sequence": 0,
                    "publication_platforms": publication_platforms
                }
            },
            "id": 'cov-sequence',
            "name": 'cov-sequence'
        }
        resp = self.post("/coverages", json.dumps(coverage))
        self.assert_sucessful_call(resp, 201)

        resp = self.post("/contributors/{}/actions/export".format(contributor_id))
        self.assert_sucessful_call(resp, 201)

        # and check that the post on url is made in the sequence order (asc)
        for idx in range(5):
            assert url.format(seq=idx) == mock_post.call_args_list[idx][0][0]

    @freeze_time("2015-08-10")
    @mock.patch('requests.post', side_effect=[get_response(200), get_response(500)])
    def test_publish_platform_failed(self, mock_post, init_http_download_server):
        contributor_id = 'contrib-pub-failed'
        publication_envs = ['integration', 'preproduction']
        url = "http://whatever.fr/pub"
        self._create_contributor(contributor_id, 'http://{ip_http_download}/{filename}'.format(
            ip_http_download=init_http_download_server.ip_addr, filename='sample_1.zip'))
        coverage = {
            "contributors": [
                contributor_id
            ],
            "environments": {},
            "id": 'cov-sequence',
            "name": 'cov-sequence'
        }
        publication_platform = {
            "sequence": 0,
            "type": "navitia",
            "protocol": "http",
            "url": url
        }
        for idx, environment in enumerate(publication_envs):
            coverage['environments'][environment] = {
                "name": environment,
                "sequence": idx,
                "publication_platforms": [
                    publication_platform
                ]
            }

        resp = self.post("/coverages", json.dumps(coverage))
        self.assert_sucessful_call(resp, 201)

        resp = self.post("/contributors/{}/actions/export".format(contributor_id))
        self.assert_sucessful_call(resp, 201)

        resp = self.get("/jobs/{}".format(self.to_json(resp)['job']['id']))
        job = self.to_json(resp)['jobs'][0]
        assert job['step'] == 'publish_data preproduction navitia', print(job)
        assert job['error_message'] == 'error during publishing on http://whatever.fr/pub, status code => 500', print(
            job)
        assert job['state'] == 'failed'
