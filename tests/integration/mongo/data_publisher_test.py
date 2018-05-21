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

import mock
import pytest
from freezegun import freeze_time

from tartare.core.constants import DATA_FORMAT_OSM_FILE, DATA_TYPE_PUBLIC_TRANSPORT, DATA_TYPE_GEOGRAPHIC, \
    DATA_FORMAT_POLY_FILE, DATA_FORMAT_GTFS, DATA_FORMAT_NTFS
from tests.integration.test_mechanism import TartareFixture
from tests.utils import mock_requests_post, get_response, \
    _get_file_fixture_full_path


class TestDataPublisher(TartareFixture):
    def _create_contributor(self, id, url='http://canaltp.fr/gtfs.zip', data_format="gtfs",
                            data_type=DATA_TYPE_PUBLIC_TRANSPORT):
        contributor = {
            "data_type": data_type,
            "id": id,
            "name": id,
            "data_prefix": id,
            "data_sources": [
                {
                    "name": 'ds' + data_format,
                    "data_format": data_format,
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
        contributor_ids = contributor_id if type(contributor_id) == list else [contributor_id]
        coverage = {
            "contributors_ids": contributor_ids,
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
    def test_publish_ok(self, init_http_download_server):
        url = self.format_url(ip=init_http_download_server.ip_addr, filename='sample_1.zip')
        contributor_id = 'fr-idf'
        coverage_id = 'default'
        publication_platform = {
            "sequence": 0,
            "type": "navitia",
            "protocol": "http",
            "url": "http://bob/v0/jobs"
        }
        self._create_contributor(contributor_id, url=url)
        self._create_coverage(coverage_id, contributor_id, publication_platform)

        # Launch contributor export
        with mock.patch('requests.post', mock_requests_post):
            resp = self.full_export(contributor_id, coverage_id)
            self.assert_sucessful_call(resp, 201)

        # List contributor export
        r = self.json_to_dict(self.get("/contributors/fr-idf/exports"))
        exports = r["exports"]
        assert len(exports) == 1
        assert exports[0]["validity_period"]["start_date"] == "2015-02-16"
        assert exports[0]["validity_period"]["end_date"] == "2017-01-15"

        assert exports[0]['data_sources'][0]["gridfs_id"]
        data_sources = exports[0]["data_sources"]
        assert len(data_sources) == 1
        assert data_sources[0]["validity_period"]

        # List coverage export
        r = self.json_to_dict(self.get("/coverages/default/exports"))
        exports = r["exports"]
        assert len(exports) == 1
        assert exports[0]["validity_period"]["start_date"] == "2015-02-16"
        assert exports[0]["validity_period"]["end_date"] == "2017-01-15"
        assert exports[0]["gridfs_id"]
        contributors = exports[0]["contributors"]
        assert len(contributors) == 1
        assert contributors[0]["validity_period"]
        assert len(contributors[0]["data_sources"]) == 1
        assert contributors[0]["data_sources"][0]["validity_period"]

    def test_publish_ftp(self, init_http_download_server, init_ftp_upload_server):
        contributor_id = 'fr-idf'
        coverage_id = 'default'
        filename = 'some_archive.zip'
        url = self.format_url(ip=init_http_download_server.ip_addr, filename=filename)
        self._create_contributor(contributor_id, url)
        publication_platform = {
            "sequence": 0,
            "type": "navitia",
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

        self.full_export(contributor_id, coverage_id, '2015-08-10')

        # check if the file was successfully uploaded
        session = ftplib.FTP(init_ftp_upload_server.ip_addr, init_ftp_upload_server.user,
                             init_ftp_upload_server.password)
        directory_content = session.nlst()
        assert len(directory_content) == 1
        assert '{coverage_id}.zip'.format(coverage_id=coverage_id) in directory_content
        session.delete('{coverage_id}.zip'.format(coverage_id=coverage_id))
        session.quit()

    @freeze_time("2015-08-10")
    def test_publish_ftp_with_directory(self, init_http_download_server, init_ftp_upload_server):
        contributor_id = 'fr-idf'
        coverage_id = 'default'
        ftp_username = 'tartare_user'
        ftp_password = 'tartare_password'
        filename = 'some_archive.zip'
        directory = "/ods"

        session = ftplib.FTP(init_ftp_upload_server.ip_addr, ftp_username, ftp_password)
        # Create a directory in the ftp
        session.mkd(directory)

        url = self.format_url(ip=init_http_download_server.ip_addr, filename=filename)
        self._create_contributor(contributor_id, url)
        # see password : tests/fixtures/authent/ftp_upload_users/pureftpd.passwd
        publication_platform = {
            "sequence": 0,
            "type": "navitia",
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

        self.full_export(contributor_id, coverage_id)

        # check if the file was successfully uploaded
        directory_content = session.nlst(directory)
        assert len(directory_content) == 1
        assert '{coverage_id}.zip'.format(coverage_id=coverage_id) in directory_content
        session.delete('{directory}/{coverage_id}.zip'.format(directory=directory, coverage_id=coverage_id))
        session.rmd(directory)

    @mock.patch('tartare.processes.fusio.Fusio.replace_url_hostname_from_url')
    @mock.patch('tartare.processes.fusio.Fusio.wait_for_action_terminated')
    @mock.patch('requests.post')
    @mock.patch('requests.get')
    @freeze_time("2018-05-14")
    def test_publish_ftp_ods_with_metadata(self, fusio_get, fusio_post, wait_for_action_terminated,
                                           replace_url_hostname_from_url, init_http_download_server,
                                           init_ftp_upload_server):
        contributor_id = 'id_test'
        coverage_id = 'my-coverage-id'
        sample_data = 'some_archive.zip'
        url = self.format_url(ip=init_http_download_server.ip_addr,
                              filename=sample_data,
                              path='gtfs')
        self.init_contributor(contributor_id, "my_gtfs", url)
        fusio_end_point = 'http://fusio_host/cgi-bin/fusio.dll/'
        preprocesses = []
        input_data_source_ids = []
        for target_data_format in [DATA_FORMAT_GTFS, DATA_FORMAT_NTFS]:
            target_id = 'my_{}_data_source'.format(target_data_format)
            input_data_source_ids.append(target_id)
            preprocesses.append({
                "id": "fusio_export",
                "type": "FusioExport",
                "params": {
                    "url": fusio_end_point,
                    "target_data_source_id": target_id,
                    "export_type": target_data_format
                },
                "sequence": 0
            })
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
            },
            "input_data_source_ids": input_data_source_ids
        }
        environments = {
            'production': {
                'sequence': 0,
                'name': 'production',
                'publication_platforms': [publication_platform]
            }
        }
        license = {
            "name": 'my license',
            "url": 'http://license.org/mycompany'
        }
        self.init_coverage(coverage_id, [contributor_id], preprocesses, environments, license)

        fetch_url_gtfs = self.format_url(ip=init_http_download_server.ip_addr, filename=sample_data)
        fetch_url_ntfs = self.format_url(ip=init_http_download_server.ip_addr, path='', filename='ntfs.zip')

        replace_url_hostname_from_url.side_effect = [fetch_url_gtfs, fetch_url_ntfs]
        fusio_post.side_effect = [
            get_response(200, self.get_fusio_response_from_action_id('gtfs-action-id')),
            get_response(200, self.get_fusio_response_from_action_id('ntfs-action-id'))
        ]
        fusio_get.side_effect = [
            get_response(200, self.get_fusio_export_url_response_from_action_id('gtfs-action-id',
                                                                                "http://fusio/whatever")),
            get_response(200, self.get_fusio_export_url_response_from_action_id('ntfs-action-id',
                                                                                "http://fusio/whatever"))
        ]
        self.full_export(contributor_id, coverage_id)
        self.assert_ods_uploaded_ok(init_ftp_upload_server, coverage_id)

    def test_publish_stops_to_ftp(self, init_http_download_server, init_ftp_upload_server):
        contributor_id = 'fr-idf'
        coverage_id = 'default'
        filename = 'some_archive.zip'
        url = self.format_url(ip=init_http_download_server.ip_addr, filename=filename)
        self._create_contributor(contributor_id, url)
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

        self.full_export(contributor_id, coverage_id, '2015-08-10')

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
        cov_id = 'cov-sequence'
        publication_envs = ['integration', 'production', 'preproduction']
        url = "http://whatever.{env}/v0/jobs/il"

        self._create_contributor(contributor_id, self.format_url(ip=init_http_download_server.ip_addr,
                                                                 filename='sample_1.zip'))
        coverage = {
            "contributors_ids": [
                contributor_id
            ],
            "environments": {},
            "id": cov_id,
            "name": cov_id
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

        self.full_export(contributor_id, cov_id)

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
        cov_id = 'cov-sequence'
        # we will create 5 platform for prod env with different sequences
        sequences = [4, 0, 3, 2, 1]
        url = "http://whatever.sequence.{seq}/v0/jobs/il"

        self._create_contributor(contributor_id, self.format_url(ip=init_http_download_server.ip_addr,
                                                                 filename='sample_1.zip'))

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
            "contributors_ids": [
                contributor_id
            ],
            "environments": {
                "production": {
                    "name": 'production',
                    "sequence": 0,
                    "publication_platforms": publication_platforms
                }
            },
            "id": cov_id,
            "name": cov_id
        }
        resp = self.post("/coverages", json.dumps(coverage))
        self.assert_sucessful_call(resp, 201)

        self.full_export(contributor_id, cov_id)

        # and check that the post on url is made in the sequence order (asc)
        for idx in range(5):
            assert url.format(seq=idx) == mock_post.call_args_list[idx][0][0]

    @freeze_time("2015-08-10")
    @mock.patch('requests.post', side_effect=[get_response(200), get_response(500)])
    def test_publish_platform_failed(self, mock_post, init_http_download_server):
        contributor_id = 'contrib-pub-failed'
        cov_id = 'cov-sequence'
        publication_envs = ['integration', 'preproduction']
        url = "http://whatever.fr/pub"
        self._create_contributor(contributor_id, self.format_url(ip=init_http_download_server.ip_addr,
                                                                 filename='sample_1.zip'))
        coverage = {
            "contributors_ids": [
                contributor_id
            ],
            "environments": {},
            "id": cov_id,
            "name": cov_id
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

        resp = self.full_export(contributor_id, cov_id)

        resp = self.get("/jobs/{}".format(self.json_to_dict(resp)['job']['id']))
        job = self.json_to_dict(resp)['jobs'][0]
        assert job['step'].startswith('publish_data preproduction navitia on '), print(job)
        assert job['error_message'] == 'error during publishing on http://whatever.fr/pub, status code => 500', print(
            job)
        assert job['state'] == 'failed'

    @mock.patch('requests.post', side_effect=[get_response(200)])
    def test_publish_navitia(self, post_mock, init_http_download_server):
        publish_url = "http://tyr.whatever.com"
        contributor_id = 'fr-idf'
        coverage_id = 'default'
        filename = 'some_archive.zip'
        fetch_url = self.format_url(ip=init_http_download_server.ip_addr, filename=filename)
        self._create_contributor(contributor_id, fetch_url)
        publication_platform = {
            "sequence": 0,
            "type": "navitia",
            "protocol": "http",
            "url": publish_url,
        }
        self._create_coverage(coverage_id, contributor_id, publication_platform)

        resp = self.full_export(contributor_id, coverage_id, '2015-08-10')

        post_mock.assert_called_once()

        resp = self.get("/jobs/{}".format(self.json_to_dict(resp)['job']['id']))
        job = self.json_to_dict(resp)['jobs'][0]
        assert job['step'].startswith('publish_data production navitia on '), print(job)
        assert job['error_message'] == '', print(job)
        assert job['state'] == 'done', print(job)

    @mock.patch('requests.post', side_effect=[get_response(200), get_response(200)])
    @pytest.mark.parametrize("data_format,file_name", [
        (DATA_FORMAT_OSM_FILE, 'empty_pbf.osm.pbf'),
        (DATA_FORMAT_POLY_FILE, 'ile-de-france.poly')
    ])
    def test_publish_navitia_with_osm_or_poly(self, post_mock, init_http_download_server, data_format, file_name):
        publish_url = "http://tyr.whatever.com"
        contributor_id = 'fr-idf'
        coverage_id = 'default'
        filename = 'some_archive.zip'
        contributor_geo = 'geo'
        fetch_url = self.format_url(ip=init_http_download_server.ip_addr, filename=filename)
        self._create_contributor(contributor_id, fetch_url)
        fetch_url = self.format_url(ip=init_http_download_server.ip_addr, path='geo_data', filename=file_name)
        self._create_contributor(contributor_geo, fetch_url, data_format=data_format,
                                 data_type=DATA_TYPE_GEOGRAPHIC)
        publication_platform = {
            "sequence": 0,
            "type": "navitia",
            "protocol": "http",
            "url": publish_url,
        }
        self._create_coverage(coverage_id, [contributor_id, contributor_geo], publication_platform)

        self.contributor_export(contributor_id)
        self.contributor_export(contributor_geo)
        resp = self.coverage_export(coverage_id)

        assert post_mock.call_count == 2

        resp = self.get("/jobs/{}".format(self.json_to_dict(resp)['job']['id']))
        job = self.json_to_dict(resp)['jobs'][0]
        assert job['step'].startswith('publish_data production navitia on '), print(job)
        assert job['error_message'] == '', print(job)
        assert job['state'] == 'done', print(job)

    @mock.patch('requests.post', side_effect=[get_response(200), get_response(200), get_response(200)])
    def test_publish_navitia_with_osm_and_poly(self, post_mock, init_http_download_server):
        publish_url = "http://tyr.whatever.com"
        contributor_id = 'fr-idf'
        coverage_id = 'default'
        filename = 'some_archive.zip'
        contributor_geo = 'geo'
        fetch_url = self.format_url(ip=init_http_download_server.ip_addr, filename=filename)
        self.init_contributor(contributor_id, 'gtfs_ds_id', fetch_url)
        fetch_url = self.format_url(ip=init_http_download_server.ip_addr, path='geo_data', filename='empty_pbf.osm.pbf')
        self.init_contributor(contributor_geo, 'osm_ds_id', fetch_url, data_format=DATA_FORMAT_OSM_FILE,
                              data_type=DATA_TYPE_GEOGRAPHIC)
        fetch_url = self.format_url(ip=init_http_download_server.ip_addr, path='geo_data',
                                    filename='ile-de-france.poly')
        self.add_data_source_to_contributor(contributor_geo, 'poly_ds_id', fetch_url, data_format=DATA_FORMAT_POLY_FILE)
        publication_platform = {
            "sequence": 0,
            "type": "navitia",
            "protocol": "http",
            "url": publish_url,
        }
        self._create_coverage(coverage_id, [contributor_id, contributor_geo], publication_platform)

        self.contributor_export(contributor_id)
        self.contributor_export(contributor_geo)
        resp = self.coverage_export(coverage_id)

        assert post_mock.call_count == 3

        resp = self.get("/jobs/{}".format(self.json_to_dict(resp)['job']['id']))
        job = self.json_to_dict(resp)['jobs'][0]
        assert job['step'].startswith('publish_data production navitia on '), print(job)
        assert job['error_message'] == '', print(job)
        assert job['state'] == 'done', print(job)

    @mock.patch('requests.post')
    @pytest.mark.parametrize("data_format,file_name", [
        (DATA_FORMAT_OSM_FILE, 'empty_pbf.osm.pbf'),
        (DATA_FORMAT_POLY_FILE, 'ile-de-france.poly')
    ])
    def test_publish_only_osm_or_poly(self, post_mock, init_http_download_server, data_format, file_name):
        publish_url = "http://tyr.whatever.com"
        coverage_id = 'default'
        contributor_geo = 'geo'
        fetch_url = self.format_url(ip=init_http_download_server.ip_addr, path='geo_data', filename=file_name)
        self._create_contributor(contributor_geo, fetch_url, data_format=data_format,
                                 data_type=DATA_TYPE_GEOGRAPHIC)
        publication_platform = {
            "sequence": 0,
            "type": "navitia",
            "protocol": "http",
            "url": publish_url,
        }
        self._create_coverage(coverage_id, contributor_geo, publication_platform)

        resp = self.full_export(contributor_geo, coverage_id, '2015-08-10')

        assert post_mock.call_count == 0

        resp = self.get("/jobs/{}".format(self.json_to_dict(resp)['job']['id']))
        job = self.json_to_dict(resp)['jobs'][0]
        assert job['step'] == 'merge', print(job)
        assert job[
                   'error_message'] == 'coverage default does not contains any Fusio export preprocess and fallback computation cannot find any gtfs data source', print(
            job)
        assert job['state'] == 'failed', print(job)
