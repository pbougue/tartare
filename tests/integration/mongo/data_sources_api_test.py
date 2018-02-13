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
import pytest
from mock import mock

import tartare
from tartare.core import models
from tartare.core.constants import DATA_FORMAT_VALUES, INPUT_TYPE_VALUES, DATA_FORMAT_DEFAULT, INPUT_TYPE_DEFAULT, \
    DATA_SOURCE_STATUS_NEVER_FETCHED, DATA_SOURCE_STATUS_UPDATED, DATA_SOURCE_STATUS_FAILED, \
    DATA_SOURCE_STATUS_UNCHANGED, DATA_FORMAT_BY_DATA_TYPE, DATA_TYPE_PUBLIC_TRANSPORT, DATA_FORMAT_OSM_FILE, \
    DATA_TYPE_GEOGRAPHIC, DATA_FORMAT_BANO_FILE, DATA_FORMAT_POLY_FILE
from tartare.exceptions import FetcherException
from tests.integration.test_mechanism import TartareFixture
from tartare import app, mongo


class TestDataSources(TartareFixture):
    def test_post_ds_one_data_source_without_id(self, contributor):
        """"
        using /data_sources endpoint
        """
        post_ds = {
            "name": "data_source_name",
            "input": {
                "type": "url",
                "url": "http://stif.com/od.zip"
            }
        }
        raw = self.post('/contributors/id_test/data_sources', self.dict_to_json(post_ds))
        assert raw.status_code == 201, print(self.json_to_dict(raw))

        raw = self.get('/contributors/id_test/data_sources')
        r = self.json_to_dict(raw)
        self.assert_sucessful_call(raw)
        assert len(r["data_sources"]) == 1

    def test_post_ds_one_data_source_with_id(self, contributor):
        """
        using /data_sources endpoint
        """
        post_ds = {
            "id": "data_source_id",
            "name": "data_source_name",
            "input": {
                "type": "url",
                "url": "http://stif.com/od.zip"
            }
        }
        raw = self.post('/contributors/id_test/data_sources', self.dict_to_json(post_ds))
        assert raw.status_code == 201, print(self.json_to_dict(raw))

        raw = self.get('/contributors/id_test/data_sources')
        r = self.json_to_dict(raw)
        self.assert_sucessful_call(raw)
        assert len(r["data_sources"]) == 1
        assert r["data_sources"][0]["id"] == 'data_source_id'

    def test_post_ds_one_data_source_with_data_format(self, contributor):
        """
        using /data_sources endpoint
        """
        post_ds = {
            "name": "data_source_name",
            "data_format": "gtfs",
            "input": {
                "type": "url",
                "url": "http://stif.com/od.zip"
            }
        }
        raw = self.post('/contributors/id_test/data_sources', self.dict_to_json(post_ds))
        assert raw.status_code == 201, print(self.json_to_dict(raw))

        raw = self.get('/contributors/id_test/data_sources')
        r = self.json_to_dict(raw)
        self.assert_sucessful_call(raw)
        assert len(r["data_sources"]) == 1
        assert r["data_sources"][0]["data_format"] == "gtfs"
        assert r["data_sources"][0]["input"]["type"] == "url"
        assert r["data_sources"][0]["input"]["url"] == "http://stif.com/od.zip"
        assert r["data_sources"][0]["service_id"] is None

    def test_post_ds_one_data_source_with_service_id(self, contributor):
        """
        using /data_sources endpoint
        """
        post_ds = {
            "name": "data_source_name",
            "data_format": "gtfs",
            "service_id": "Google-1",
            "input": {
                "type": "url",
                "url": "http://stif.com/od.zip"
            }
        }
        raw = self.post('/contributors/id_test/data_sources', self.dict_to_json(post_ds))
        assert raw.status_code == 201, print(self.json_to_dict(raw))

        raw = self.get('/contributors/id_test/data_sources')
        r = self.json_to_dict(raw)
        self.assert_sucessful_call(raw)
        assert len(r["data_sources"]) == 1
        assert r["data_sources"][0]["data_format"] == "gtfs"
        assert r["data_sources"][0]["input"]["type"] == "url"
        assert r["data_sources"][0]["input"]["url"] == "http://stif.com/od.zip"
        assert r["data_sources"][0]["service_id"] == "Google-1"

    def test_post_ds_two_data_source(self, contributor):
        """
        using /data_sources endpoint
        """
        post_ds = {
            "name": "data_source_name1",
            "input": {
                "type": "url",
                "url": "http://stif.com/od.zip"
            }
        }
        raw = self.post('/contributors/id_test/data_sources', self.dict_to_json(post_ds))
        assert raw.status_code == 201, print(self.json_to_dict(raw))
        post_ds = {
            "name": "data_source_name2",
            "input": {
                "type": "url",
                "url": "http://stif.com/od.zip"
            }
        }
        raw = self.post('/contributors/id_test/data_sources', self.dict_to_json(post_ds))
        assert raw.status_code == 201, print(self.json_to_dict(raw))

        raw = self.get('/contributors/id_test/data_sources')
        r = self.json_to_dict(raw)
        self.assert_sucessful_call(raw)
        assert len(r["data_sources"]) == 2
        assert r["data_sources"][0]["id"] != r["data_sources"][1]["id"]

    def test_post_ds_duplicate_two_data_source(self, contributor):
        """
        using /data_sources endpoint
        """
        post_ds = {
            "id": "duplicate_id",
            "name": "data_source_name1",
            "input": {
                "type": "url",
                "url": "http://stif.com/od.zip"
            }
        }
        raw = self.post('/contributors/id_test/data_sources', self.dict_to_json(post_ds))
        assert raw.status_code == 201, print(self.json_to_dict(raw))
        post_ds = {
            "id": "duplicate_id",
            "name": "data_source_name2",
            "input": {
                "type": "url",
                "url": "http://stif.com/od.zip"
            }
        }
        raw = self.post('/contributors/id_test/data_sources', self.dict_to_json(post_ds))
        payload = self.json_to_dict(raw)
        assert raw.status_code == 409, print(payload)
        assert payload['error'] == "duplicate data_source id 'duplicate_id' for contributor 'id_test'"

    def test_patch_ds_data_source_with_full_contributor(self, data_source):
        """
        using /data_sources endpoint
        """
        data_source["name"] = "name_modified"
        print("patching data with ", self.dict_to_json(data_source))
        raw = self.patch('/contributors/id_test/data_sources/{}'.format(data_source["id"]),
                         self.dict_to_json(data_source))
        r = self.json_to_dict(raw)
        self.assert_sucessful_call(raw)
        assert len(r["data_sources"]) == 1
        patched_data_source = r["data_sources"][0]
        assert patched_data_source["name"] == "name_modified"

    def test_patch_ds_data_source_name_only(self, data_source):
        """
        using /data_sources endpoint
        """
        modif_ds = {"name": "name_modified"}
        raw = self.patch('/contributors/id_test/data_sources/{}'.format(data_source["id"]), self.dict_to_json(modif_ds))
        r = self.json_to_dict(raw)
        self.assert_sucessful_call(raw)
        assert len(r["data_sources"]) == 1
        patched_data_source = r["data_sources"][0]
        assert patched_data_source["name"] == "name_modified"
        assert patched_data_source["data_format"] == "gtfs"

    def test_patch_ds_data_source_service_id(self, data_source):
        """
        using /data_sources endpoint
        """
        modif_ds = {"service_id": "Google-1"}
        raw = self.patch('/contributors/id_test/data_sources/{}'.format(data_source["id"]), self.dict_to_json(modif_ds))
        r = self.json_to_dict(raw)
        self.assert_sucessful_call(raw)
        assert len(r["data_sources"]) == 1
        patched_data_source = r["data_sources"][0]
        assert patched_data_source["service_id"] == "Google-1"

    def test_patch_data_source_id(self, data_source):
        modif_ds = {"id": "id_modified"}
        raw = self.patch('/contributors/id_test/data_sources/{}'.format(data_source["id"]), self.dict_to_json(modif_ds))
        r = self.json_to_dict(raw)
        assert raw.status_code == 400, print(r)
        assert r['message'] == 'Invalid arguments'
        assert r['error'] == 'the modification of the id is not possible'

    def test_patch_ds_one_data_source_name_of_two_and_add_one(self, contributor):
        """
        using /data_sources endpoint
        """
        post_ds = {
            "id": "ds1_id",
            "name": "data_source_name1",
            "data_format": "gtfs",
            "input": {
                "type": "url",
                "url": "http://stif.com/od.zip"
            }
        }
        raw = self.post('/contributors/id_test/data_sources', self.dict_to_json(post_ds))
        self.assert_sucessful_create(raw)

        post_ds = {
            "id": "ds2_id",
            "name": "data_source_name2",
            "data_format": "gtfs",
            "service_id": "Google-1",
            "input": {
                "type": "url",
                "url": "http://stif.com/od.zip"
            }
        }
        raw = self.post('/contributors/id_test/data_sources', self.dict_to_json(post_ds))
        self.assert_sucessful_create(raw)

        modif_ds = {
            "name": "name_modified",
            "data_format": "gtfs",
            "service_id": None,
            "input": {
                "type": "url",
                "url": "http://stif.com/od.zip"
            }
        }
        raw = self.patch('/contributors/id_test/data_sources/ds2_id', self.dict_to_json(modif_ds))
        self.assert_sucessful_call(raw)

        post_ds = {
            "id": "ds3_id",
            "name": "data_source_name3",
            "service_id": "Google-2",
            "input": {
                "type": "url",
                "url": "http://stif.com/od.zip"
            }
        }
        raw = self.post('/contributors/id_test/data_sources', self.dict_to_json(post_ds))
        self.assert_sucessful_create(raw)

        raw = self.get('/contributors/id_test/data_sources')
        r = self.json_to_dict(raw)
        self.assert_sucessful_call(raw)
        assert len(r["data_sources"]) == 3
        patched_data_sources = r["data_sources"]
        assert patched_data_sources[0]["data_format"] == "gtfs"
        assert patched_data_sources[1]["data_format"] == "gtfs"
        assert patched_data_sources[2]["data_format"] == "gtfs"
        assert patched_data_sources[0]["name"] == "data_source_name1"
        assert patched_data_sources[1]["name"] == "name_modified"
        assert patched_data_sources[2]["name"] == "data_source_name3"
        assert patched_data_sources[0]["service_id"] is None
        assert patched_data_sources[1]["service_id"] is None
        assert patched_data_sources[2]["service_id"] == "Google-2"

    @pytest.mark.parametrize("license_url,license_name,expected_status_code", [
        ('http://license.org/mycompany', 'my license', 201),
        ('http://license.org/othercompany', 'my license full name', 201),
        ('http://license.org/othercompany', None, 400),
        (None, 'my license full name', 400),
        (None, None, 201),
    ])
    def test_post_with_license(self, contributor, license_url, license_name, expected_status_code):

        data_source = {
            "input": {
                "type": "url",
                "url": "http://my.server/some_archive.zip"
            },
            "name": "inputHttpDemo"
        }
        if license_name or license_url:
            data_source['license'] = {
                "url": license_url,
                "name": license_name
            }
        response = self.post('/contributors/{}/data_sources'.format(contributor['id']), self.dict_to_json(data_source))
        assert response.status_code == expected_status_code, print(response)
        data_source_created = self.json_to_dict(response)
        if expected_status_code == 201:
            data_source_raw = self.get('/contributors/{cid}/data_sources/{dsid}'.format(cid=contributor['id'], dsid=
            data_source_created['data_sources'][0]['id']))
            data_source_from_api = self.json_to_dict(data_source_raw)['data_sources'][0]

            with tartare.app.app_context():
                expected_url = license_url if license_url else tartare.app.config.get('DEFAULT_LICENSE_URL')
                expected_name = license_name if license_name else tartare.app.config.get('DEFAULT_LICENSE_NAME')
                assert data_source_from_api['license']['url'] == expected_url
                assert data_source_from_api['license']['name'] == expected_name

    def test_post_data_source_wrong_data_format(self, contributor):
        data_source = {
            "data_format": "failed",
            "input": {'type': 'manual'},
            "name": "ds-name"
        }
        response = self.post('/contributors/{}/data_sources'.format(contributor['id']), self.dict_to_json(data_source))
        assert response.status_code == 400, print(response)
        response_payload = self.json_to_dict(response)
        assert 'error' in response_payload
        assert response_payload['error'] == 'choice "failed" not in possible values {}'.format(DATA_FORMAT_VALUES)

    def test_post_data_source_wrong_input_type(self, contributor):
        data_source = {
            "data_format": "gtfs",
            "input": {'type': 'wrong'},
            "name": "ds-name"
        }
        response = self.post('/contributors/{}/data_sources'.format(contributor['id']), self.dict_to_json(data_source))
        assert response.status_code == 400, print(response)
        response_payload = self.json_to_dict(response)
        assert {'error': {'input': {'type': [
            'choice "wrong" not in possible values (url, manual, computed).']}},
                   'message': 'Invalid arguments'} == response_payload, print(response_payload)

    def test_post_data_source_valid_data_format(self, contributor):
        for data_format in DATA_FORMAT_BY_DATA_TYPE[DATA_TYPE_PUBLIC_TRANSPORT]:
            data_source = {
                "data_format": data_format,
                "input": {'type': 'manual'},
                "name": "ds-name-" + data_format
            }
            response = self.post('/contributors/{}/data_sources'.format(contributor['id']),
                                 self.dict_to_json(data_source))
            assert response.status_code == 201, print(self.json_to_dict(response))

    def test_post_data_source_valid_input_type(self, contributor):
        for input_type in INPUT_TYPE_VALUES:
            data_source = {
                "data_format": 'gtfs',
                "input": {'type': input_type},
                "name": "ds-name-" + input_type
            }
            response = self.post('/contributors/{}/data_sources'.format(contributor['id']),
                                 self.dict_to_json(data_source))
            assert response.status_code == 201, print(self.json_to_dict(response))

    def test_data_source_data_format_default_value(self, contributor):
        data_source = {
            "input": {'type': 'manual'},
            "name": "ds-name"
        }
        response = self.post('/contributors/{}/data_sources'.format(contributor['id']),
                             self.dict_to_json(data_source))
        response_payload = self.json_to_dict(response)
        assert response.status_code == 201, print(response_payload)
        assert response_payload['data_sources'][0]['data_format'] == DATA_FORMAT_DEFAULT, print(response_payload)

    def test_data_source_input_type_default_value(self, contributor):
        data_source = {
            "data_format": "gtfs",
            "name": "ds-name"
        }
        response = self.post('/contributors/{}/data_sources'.format(contributor['id']),
                             self.dict_to_json(data_source))
        response_payload = self.json_to_dict(response)
        assert response.status_code == 201, print(response_payload)
        assert response_payload['data_sources'][0]['input']['type'] == INPUT_TYPE_DEFAULT, print(response_payload)

    def test_patch_with_invalid_data_format(self, contributor):
        data_source = {
            "id": "issues_257",
            "data_format": "gtfs",
            "name": "ds-name"
        }
        response = self.post('/contributors/{}/data_sources'.format(contributor['id']),
                             self.dict_to_json(data_source))
        response_payload = self.json_to_dict(response)
        assert response.status_code == 201, print(response_payload)
        assert response_payload['data_sources'][0]['input']['type'] == INPUT_TYPE_DEFAULT, print(response_payload)

        pacth = {
            "id": "issues_257",
            "data_format": "issues 257"
        }
        response = self.patch('/contributors/{}/data_sources/{}'.format(contributor['id'], data_source['id']),
                              self.dict_to_json(pacth))
        assert response.status_code == 400, print(response)
        response_payload = self.json_to_dict(response)
        assert 'error' in response_payload
        assert response_payload['error'] == 'choice "issues 257" not in possible values {}'.format(DATA_FORMAT_VALUES)

    def test_manage_data_source_expected_file_name(self, contributor):
        expected_file_name = 'config.json'
        data_source = {
            "input": {'type': 'url', 'expected_file_name': expected_file_name},
            "name": "ds-name"
        }
        response = self.post('/contributors/{}/data_sources'.format(contributor['id']),
                             self.dict_to_json(data_source))
        self.assert_sucessful_call(response, 201)
        data_source = self.json_to_dict(response)['data_sources'][0]
        assert data_source['input']['expected_file_name'] == expected_file_name, print(data_source)

        new_expected_file_name = 'config_new.json'
        data_source['input']['expected_file_name'] = new_expected_file_name
        response = self.patch('/contributors/{}/data_sources/{}'.format(contributor['id'], data_source['id']),
                              self.dict_to_json({'input': {'expected_file_name': new_expected_file_name}}))

        self.assert_sucessful_call(response)
        data_source = self.json_to_dict(response)['data_sources'][0]
        assert data_source['input']['expected_file_name'] == new_expected_file_name, print(data_source)

    def test_data_source_calculated_fields_values_after_posting(self, contributor):
        response = self.post('/contributors/{}/data_sources'.format(contributor['id']),
                             self.dict_to_json({"name": "ds-name"}))
        response_payload = self.json_to_dict(response)
        self.assert_sucessful_call(response, 201)
        ds = response_payload['data_sources'][0]
        assert ds['status'] == DATA_SOURCE_STATUS_NEVER_FETCHED
        assert ds['fetch_started_at'] is None
        assert ds['updated_at'] is None
        assert ds['validity_period'] is None

        # test that calculated fields are not persisted to database
        with app.app_context():
            raw = mongo.db[models.Contributor.mongo_collection].find_one({
                '_id': contributor['id'],
            })

            data_source = raw['data_sources'][0]
            assert 'status' not in data_source
            assert 'fetch_started_at' not in data_source
            assert 'updated_at' not in data_source
            assert 'validity_period' not in data_source

    def __init_ds_and_export(self, contributor, init_http_download_server, do_init=True):
        if do_init:
            url = self.format_url(ip=init_http_download_server.ip_addr, filename="some_archive.zip")
            response = self.post('/contributors/{}/data_sources'.format(contributor['id']),
                                 self.dict_to_json({"name": "ds-name", "input": {"type": "url", "url": url}}))
            self.assert_sucessful_call(response, 201)
        response = self.post('/contributors/{}/actions/export?current_date=2015-08-23'.format(contributor.get('id')))
        self.assert_sucessful_call(response, 201)

        job_details = self.get_job_details(self.json_to_dict(response)['job']['id'])
        response = self.get('/contributors/{}/data_sources'.format(contributor.get('id')))
        self.assert_sucessful_call(response)
        return job_details, self.json_to_dict(response)['data_sources'][0]

    def test_data_source_calculated_fields_values_after_export_ok(self, contributor, init_http_download_server):
        job_details, ds = self.__init_ds_and_export(contributor, init_http_download_server)
        assert job_details['step'] == 'save_contributor_export'
        assert job_details['state'] == 'done'
        assert ds['status'] == DATA_SOURCE_STATUS_UPDATED
        assert ds['fetch_started_at'] is not None
        assert ds['updated_at'] is not None
        assert ds['validity_period'] == {'start_date': '2015-03-25', 'end_date': '2015-08-26'}
        assert 'start_date' in ds['validity_period']
        assert 'end_date' in ds['validity_period']

    @mock.patch('tartare.core.fetcher.HttpFetcher.fetch', side_effect=FetcherException('my_message'))
    def test_data_source_calculated_fields_values_after_export_failed(self, fetch_mock, contributor,
                                                                      init_http_download_server):
        job_details, ds = self.__init_ds_and_export(contributor, init_http_download_server)
        assert job_details['step'] == 'fetching data'
        assert job_details['state'] == 'failed'
        assert job_details['error_message'] == 'my_message'
        assert ds['status'] == DATA_SOURCE_STATUS_FAILED
        assert ds['fetch_started_at'] is not None
        assert ds['updated_at'] is None
        assert ds['validity_period'] is None


    def test_data_source_calculated_fields_values_after_export_ok_then_unchanged(self, contributor,
                                                                                 init_http_download_server):
        job_details, ds = self.__init_ds_and_export(contributor, init_http_download_server)
        assert job_details['step'] == 'save_contributor_export'
        assert job_details['state'] == 'done'
        assert ds['status'] == DATA_SOURCE_STATUS_UPDATED
        assert ds['fetch_started_at'] is not None
        assert ds['updated_at'] is not None
        assert ds['validity_period'] is not None
        new_job_details, new_ds = self.__init_ds_and_export(contributor, init_http_download_server, do_init=False)
        assert new_job_details['step'] == 'save_contributor_export'
        assert new_job_details['state'] == 'done'
        assert new_ds['status'] == DATA_SOURCE_STATUS_UNCHANGED
        assert new_ds['fetch_started_at'] != ds['fetch_started_at']
        assert new_ds['updated_at'] == ds['updated_at']
        assert new_ds['validity_period'] == ds['validity_period']

    def test_data_source_calculated_fields_values_after_export_ok_then_failed(self, contributor,
                                                                              init_http_download_server):
        job_details, ds = self.__init_ds_and_export(contributor, init_http_download_server)
        assert job_details['step'] == 'save_contributor_export'
        assert job_details['state'] == 'done'
        assert ds['status'] == DATA_SOURCE_STATUS_UPDATED
        assert ds['fetch_started_at'] is not None
        assert ds['updated_at'] is not None
        assert ds['validity_period'] is not None
        response = self.patch('/contributors/{}/data_sources/{}'.format(contributor['id'], ds['id']),
                              self.dict_to_json({'input': {'url': 'plop'}}))
        self.assert_sucessful_call(response)
        new_job_details, new_ds = self.__init_ds_and_export(contributor, init_http_download_server, do_init=False)
        assert new_job_details['step'] == 'fetching data'
        assert new_job_details['state'] == 'failed'
        assert new_ds['status'] == DATA_SOURCE_STATUS_FAILED
        assert new_ds['fetch_started_at'] != ds['fetch_started_at']
        assert new_ds['updated_at'] == ds['updated_at']
        assert new_ds['validity_period'] == ds['validity_period']

    def test_data_source_calculated_fields_values_after_posting_one_contributor(self, contributor):
        for ds_name in ["ds-name1", "ds-name2"]:
            response = self.post('/contributors/{}/data_sources'.format(contributor['id']),
                                 self.dict_to_json({"name": ds_name}))
            response_payload = self.json_to_dict(response)
            self.assert_sucessful_call(response, 201)
            ds = response_payload['data_sources'][0]
            assert ds['status'] == DATA_SOURCE_STATUS_NEVER_FETCHED
            assert ds['fetch_started_at'] is None
            assert ds['updated_at'] is None
            assert ds['validity_period'] is None
        response = self.get('/contributors/{}'.format(contributor['id']))
        response_payload = self.json_to_dict(response)
        self.assert_sucessful_call(response, 200)
        for ds in response_payload['contributors'][0]['data_sources']:
            assert ds['status'] == DATA_SOURCE_STATUS_NEVER_FETCHED
            assert ds['fetch_started_at'] is None
            assert ds['updated_at'] is None
            assert ds['validity_period'] is None

    def test_data_source_calculated_fields_values_after_posting_multi_contributors(self):
        for contrib_id in ["contrib1", "contri2b"]:
            response = self.post('/contributors',
                                 self.dict_to_json({"id": contrib_id, "name": contrib_id, "data_prefix": contrib_id}))
            self.assert_sucessful_call(response, 201)
            response = self.post('/contributors/{}/data_sources'.format(contrib_id),
                                 self.dict_to_json({"name": "ds-" + contrib_id}))
            self.assert_sucessful_call(response, 201)
            response_payload = self.json_to_dict(response)
            ds = response_payload['data_sources'][0]
            assert ds['status'] == DATA_SOURCE_STATUS_NEVER_FETCHED
            assert ds['fetch_started_at'] is None
            assert ds['updated_at'] is None
            assert ds['validity_period'] is None
        response = self.get('/contributors')
        response_payload = self.json_to_dict(response)
        self.assert_sucessful_call(response, 200)
        for contrib in response_payload['contributors']:
            assert contrib['data_sources'][0]['status'] == DATA_SOURCE_STATUS_NEVER_FETCHED
            assert contrib['data_sources'][0]['fetch_started_at'] is None
            assert contrib['data_sources'][0]['updated_at'] is None
            assert contrib['data_sources'][0]['validity_period'] is None

    @pytest.mark.parametrize("data_format", [
        DATA_FORMAT_OSM_FILE,
        DATA_FORMAT_POLY_FILE
    ])
    def test_post_multi_data_sources_osm_or_poly_forbidden(self, data_format):
        contributor = {
            'id': 'id_test',
            'name': 'id_test',
            'data_prefix': 'id_test',
            'data_type': DATA_TYPE_GEOGRAPHIC,
        }
        raw = self.post('/contributors', self.dict_to_json(contributor))
        self.assert_sucessful_create(raw)
        data_sources = [
            {'id': 'id1', 'name': 'id1', 'data_format': data_format},
            {'id': 'id2', 'name': 'id2', 'data_format': data_format},
        ]
        raw = self.post('/contributors/id_test/data_sources', self.dict_to_json(data_sources[0]))
        self.assert_sucessful_create(raw)
        raw = self.post('/contributors/id_test/data_sources', self.dict_to_json(data_sources[1]))
        response = self.assert_failed_call(raw)
        assert response['error'] == 'contributor contains more than one {} data source'.format(data_format)
        assert response['message'] == 'Invalid arguments'

    @pytest.mark.parametrize("data_format", [
        DATA_FORMAT_OSM_FILE,
        DATA_FORMAT_POLY_FILE
    ])
    def test_patch_multi_data_sources_two_osm_or_poly_forbidden(self, data_format):
        data_sources = [
            {'id': 'id1', 'name': 'id1', 'data_format': data_format},
            {'id': 'id2', 'name': 'id2', 'data_format': DATA_FORMAT_BANO_FILE},
        ]
        contributor = {
            'id': 'id_test',
            'name': 'id_test',
            'data_prefix': 'id_test',
            'data_type': DATA_TYPE_GEOGRAPHIC,
            'data_sources': data_sources,
        }
        raw = self.post('/contributors', self.dict_to_json(contributor))
        self.assert_sucessful_create(raw)
        raw = self.patch('/contributors/id_test/data_sources/id2', self.dict_to_json({'data_format': data_format}))
        response = self.assert_failed_call(raw)
        assert response['error'] == 'contributor contains more than one {} data source'.format(data_format)
        assert response['message'] == 'Invalid arguments'

    @pytest.mark.parametrize("data_format", [
        DATA_FORMAT_OSM_FILE,
        DATA_FORMAT_POLY_FILE
    ])
    def test_patch_multi_data_sources_update_one_osm_or_poly_allowed(self, data_format):
        data_sources = [
            {'id': 'id1', 'name': 'id1', 'data_format': data_format},
            {'id': 'id2', 'name': 'id2', 'data_format': DATA_FORMAT_BANO_FILE},
        ]
        contributor = {
            'id': 'id_test',
            'name': 'id_test',
            'data_prefix': 'id_test',
            'data_type': DATA_TYPE_GEOGRAPHIC,
            'data_sources': data_sources,
        }
        raw = self.post('/contributors', self.dict_to_json(contributor))
        self.assert_sucessful_create(raw)
        raw = self.patch('/contributors/id_test/data_sources/id1', self.dict_to_json({'name': 'name-updated'}))
        self.assert_sucessful_call(raw)
