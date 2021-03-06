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

import tartare
from tartare.core import models
from tartare.core.constants import DATA_TYPE_GEOGRAPHIC, DATA_FORMAT_OSM_FILE
from tartare.core.models import Coverage
from tests.integration.test_mechanism import TartareFixture


class TestCoverageApi(TartareFixture):
    def test_get_coverage_empty_success(self):
        raw = self.get('/coverages')
        assert raw.status_code == 200
        raw = self.get('/coverages/')
        assert raw.status_code == 200
        r = self.json_to_dict(raw)
        assert len(r["coverages"]) == 0

    def test_get_coverage_non_exist(self):
        raw = self.get('/coverages/id_test')
        assert raw.status_code == 404
        r = self.json_to_dict(raw)
        assert 'message' in r

    def test_post_minimal_coverage_returns_success(self):
        raw = self.post('/coverages', '{"id": "id_test", "name":"name_test"}')
        assert raw.status_code == 201
        r = self.json_to_dict(raw)
        assert len(r["coverages"]) == 1
        assert isinstance(r["coverages"], list)
        coverage = r["coverages"][0]
        assert coverage["id"] == "id_test"
        assert coverage["name"] == "name_test"
        assert coverage["type"] == "other"
        assert coverage["short_description"] == ""
        assert coverage["comment"] == ""
        assert coverage['last_active_job'] is None
        assert coverage['input_data_source_ids'] == []

        raw = self.get('/coverages')
        r = self.json_to_dict(raw)
        assert len(r["coverages"]) == 1
        assert isinstance(r["coverages"], list)
        coverage = r["coverages"][0]
        assert coverage["id"] == "id_test"
        assert coverage["name"] == "name_test"
        assert coverage["type"] == "other"
        assert coverage["short_description"] == ""
        assert coverage["comment"] == ""
        assert coverage['last_active_job'] is None
        assert coverage['input_data_source_ids'] == []

        # test that we don't persist last_active_job in database
        with tartare.app.app_context():
            raw = tartare.mongo.db[models.Coverage.mongo_collection].find_one({
                '_id': 'id_test',
            })

            assert 'last_active_job' not in raw

    def test_post_coverage_no_id(self):
        raw = self.post('/coverages', '{"name": "name_test"}')
        r = self.json_to_dict(raw)
        assert 'error' in r
        assert raw.status_code == 400
        raw = self.get('/coverages')
        r = self.json_to_dict(raw)
        assert len(r["coverages"]) == 0

    def test_post_coverage_empty_id(self):
        raw = self.post('/coverages', '{"id": "", "name": "name_test"}')
        r = self.json_to_dict(raw)

        assert 'error' in r
        assert raw.status_code == 400
        assert r['error'] == {
            'id': ['field cannot be empty']
        }

    def test_post_coverage_no_name(self):
        raw = self.post('/coverages', '{"id": "id_test"}')
        r = self.json_to_dict(raw)
        assert 'error' in r
        assert raw.status_code == 400
        raw = self.get('/coverages')
        r = self.json_to_dict(raw)
        assert len(r["coverages"]) == 0

    def test_post_coverage_with_name(self):
        raw = self.post('/coverages',
                        '{"id": "id_test", "name": "name of the coverage"}')
        assert raw.status_code == 201
        raw = self.get('/coverages')
        r = self.json_to_dict(raw)
        assert len(r["coverages"]) == 1
        assert isinstance(r["coverages"], list)
        assert r["coverages"][0]["id"] == "id_test"
        assert r["coverages"][0]["name"] == "name of the coverage"

    def test_post_coverage_with_wrong_type(self):
        raw = self.post('/coverages',
                        '{"id": "id_test", "name": "name of the coverage", "type": "donotexist"}')
        assert raw.status_code == 400

        expected_result = {
            'error': {
                'type': ['choice "donotexist" not in possible values (navitia.io, keolis, regional, other).']
            },
            'message': 'Invalid arguments'
        }

        assert expected_result == self.json_to_dict(raw)

    @pytest.mark.parametrize("type", [
        'navitia.io',
        'keolis',
        'regional',
        'other',
    ])
    def test_post_coverage_with_good_type(self, type):
        raw = self.post('/coverages',
                        self.dict_to_json({"id": "id_test", "name": "name of the coverage", "type": type}))
        assert raw.status_code == 201
        raw = self.get('/coverages')
        r = self.json_to_dict(raw)
        assert len(r["coverages"]) == 1
        assert isinstance(r["coverages"], list)
        assert r["coverages"][0]["id"] == "id_test"
        assert r["coverages"][0]["name"] == "name of the coverage"
        assert r["coverages"][0]["type"] == type

    def test_post_coverage_with_short_description_and_comment(self):
        raw = self.post('/coverages',
                        self.dict_to_json({"id": "id_test", "name": "name of the coverage",
                                           "short_description": "super coverage", "comment": "a comment"}))
        assert raw.status_code == 201
        raw = self.get('/coverages')
        r = self.json_to_dict(raw)
        assert len(r["coverages"]) == 1
        assert isinstance(r["coverages"], list)
        assert r["coverages"][0]["id"] == "id_test"
        assert r["coverages"][0]["name"] == "name of the coverage"
        assert r["coverages"][0]["short_description"] == "super coverage"
        assert r["coverages"][0]["comment"] == "a comment"

    def test_post_coverage_with_pre_env(self):
        raw = self.post('/coverages',
                        '''{"id": "id_test", "name": "name of the coverage",
                        "environments" : {"preproduction": {"name": "pre", "sequence": 0}}}''')
        assert raw.status_code == 201
        raw = self.get('/coverages')
        r = self.json_to_dict(raw)
        assert len(r["coverages"]) == 1
        assert isinstance(r["coverages"], list)
        coverage = r["coverages"][0]
        assert coverage["id"] == "id_test"
        assert coverage["name"] == "name of the coverage"
        assert 'environments' in coverage
        assert 'production' not in coverage['environments']
        assert 'preproduction' in coverage['environments']
        assert coverage['environments']['preproduction']['name'] == 'pre'
        assert coverage['environments']['preproduction']['sequence'] == 0

    def test_post_coverage_with_no_env(self):
        raw = self.post('/coverages',
                        '''{"id": "id_test", "name": "name of the coverage",
                            "environments" : {"notvalidenv": {"name": "pre", "tyr_url": "http://foo.bar/"}}}''')

        assert raw.status_code == 400
        r = self.json_to_dict(raw)
        assert 'error' in r
        assert 'unknown field name notvalidenv' in r['error']['environments']['_schema']

    def test_post_coverage_with_all_env(self):
        raw = self.post('/coverages',
                        '''{"id": "id_test", "name": "name of the coverage",
                        "environments" : {
                        "preproduction": {"name": "pre", "sequence": 1},
                        "production": {"name": "prod", "sequence": 2},
                        "integration": {"name": "sim", "sequence": 0}
                        }}''')
        assert raw.status_code == 201
        raw = self.get('/coverages')
        r = self.json_to_dict(raw)
        assert len(r["coverages"]) == 1
        assert isinstance(r["coverages"], list)
        coverage = r["coverages"][0]
        assert coverage["id"] == "id_test"
        assert coverage["name"] == "name of the coverage"
        assert 'environments' in coverage
        assert 'production' in coverage['environments']
        assert 'preproduction' in coverage['environments']
        assert 'integration' in coverage['environments']
        assert coverage['environments']['preproduction']['name'] == 'pre'
        assert coverage['environments']['preproduction']['sequence'] == 1
        assert coverage['environments']['production']['name'] == 'prod'
        assert coverage['environments']['production']['sequence'] == 2
        assert coverage['environments']['integration']['name'] == 'sim'
        assert coverage['environments']['integration']['sequence'] == 0

    def test_post_coverage_with_invalid_platorm_protocol(self):
        post_data = {
            "id": "id_test",
            "name": "name_test",
            "environments": {
                "preproduction": {
                    "name": "preproduction",
                    "sequence": 0,
                    "publication_platforms": [
                        {
                            "protocol": "invalid_type",
                            "url": "ftp.ods.com",
                            "sequence": 0,
                            "options": {
                                "authent": {
                                    "username": "test"
                                },
                            },
                            "directory": "/"
                        }
                    ]
                }
            }
        }

        raw = self.post('/coverages', self.dict_to_json(post_data))
        assert raw.status_code == 400
        r = self.json_to_dict(raw)
        assert 'error' in r
        expected_error = {
            'error': {
                'environments': {
                    'preproduction': {
                        'publication_platforms': {
                            '0': {
                                'protocol': ['choice "invalid_type" not in possible values (http, ftp).']
                            }
                        }
                    }
                }
            },
            'message': 'Invalid arguments'
        }
        assert r == expected_error

    def test_post_coverage_with_valid_platorm_protocol(self):
        post_data = {
            "id": "id_test",
            "name": "name_test",
            "environments": {
                "preproduction": {
                    "name": "preproduction",
                    "sequence": 0,
                    "publication_platforms": [
                        {
                            "protocol": "ftp",
                            "url": "ftp.ods.com",
                            "sequence": 0,
                            "options": {
                                "authent": {
                                    "username": "test"
                                },
                            },
                            "directory": "/"
                        }
                    ]
                }
            }
        }

        raw = self.post('/coverages', self.dict_to_json(post_data))
        assert raw.status_code == 201
        r = self.json_to_dict(raw)
        assert len(r["coverages"]) == 1
        assert isinstance(r["coverages"], list)
        coverage = r["coverages"][0]
        assert coverage["id"] == "id_test"
        assert coverage["name"] == "name_test"
        assert 'environments' in coverage
        assert 'preproduction' in coverage['environments']
        assert len(coverage['processes']) == 0
        assert coverage['license'] == {'url': '', 'name': 'Private (unspecified)'}
        preprod_env = coverage['environments']['preproduction']
        assert preprod_env['name'] == 'preproduction'
        assert preprod_env['sequence'] == 0
        assert len(preprod_env['publication_platforms']) == 1
        platform = preprod_env['publication_platforms'][0]
        assert platform["sequence"] == 0
        assert platform["options"] == {'directory': None, 'authent': {'username': 'test', 'password': None}}
        assert platform["protocol"] == 'ftp'
        assert platform["url"] == 'ftp.ods.com'

    def test_delete_coverage_returns_success(self):
        raw = self.get('/coverages/id_test')
        assert raw.status_code == 404

        raw = self.post('/coverages', '{"id": "id_test", "name": "name_test"}')
        assert raw.status_code == 201
        raw = self.delete('/coverages/id_test')
        self.assert_sucessful_call(raw, 204)
        raw = self.get('/coverages/id_test')
        assert raw.status_code == 404

        raw = self.post('/coverages', '{"id": "id_test2", "name": "name_test2"}')
        assert raw.status_code == 201
        raw = self.get('/coverages')
        r = self.json_to_dict(raw)
        assert len(r["coverages"]) == 1

    @pytest.mark.parametrize("license_url,license_name,expected_status_code", [
        ('http://license.org/mycompany', 'my license', 201),
        ('http://license.org/othercompany', 'my license full name', 201),
        ('http://license.org/othercompany', None, 400),
        (None, 'my license full name', 400),
        (None, None, 201),
    ])
    def test_post_with_license(self, license_url, license_name, expected_status_code):
        coverage = {
            "id": "id_test",
            "name": "name_test"
        }
        if license_name or license_url:
            coverage['license'] = {
                "url": license_url,
                "name": license_name
            }
        response = self.post('/coverages', self.dict_to_json(coverage))
        assert response.status_code == expected_status_code, print(response)
        if expected_status_code == 201:
            coverage_raw = self.get('/coverages/{cid}'.format(cid=coverage['id']))
            coverage_from_api = self.json_to_dict(coverage_raw)['coverages'][0]

            with tartare.app.app_context():
                expected_url = license_url if license_url else tartare.app.config.get('DEFAULT_LICENSE_URL')
                expected_name = license_name if license_name else tartare.app.config.get('DEFAULT_LICENSE_NAME')
                assert coverage_from_api['license']['url'] == expected_url
                assert coverage_from_api['license']['name'] == expected_name

    def __assert_pub_platform_authent(self, pub_platform, user_to_set):
        assert 'password' not in pub_platform['options']['authent']
        assert 'username' in pub_platform['options']['authent']
        assert user_to_set == pub_platform['options']['authent']['username']

    def test_post_config_user_password_check_in_get(self):
        user_to_set = 'user'
        cov_id = 'cov'
        coverage = {
            "environments": {
                "production": {
                    "name": "production",
                    "sequence": 0,
                    "publication_platforms": [
                        {
                            "sequence": 0,
                            "protocol": "ftp",
                            "url": "whatever.com",
                            "options": {
                                "authent": {
                                    "username": user_to_set,
                                    "password": 'my_password'
                                }
                            }
                        }
                    ]
                }
            },
            "id": cov_id,
            "name": cov_id
        }
        raw = self.post("/coverages", self.dict_to_json(coverage))
        coverage = self.assert_sucessful_create(raw)['coverages'][0]
        r = self.json_to_dict(raw)['coverages'][0]
        self.__assert_pub_platform_authent(r['environments']['production']['publication_platforms'][0], user_to_set)

        coverage['name'] = 'toto'
        raw = self.put('/coverages/' + cov_id, self.dict_to_json(coverage))
        r = self.assert_sucessful_call(raw, 200)['coverages'][0]
        self.__assert_pub_platform_authent(r['environments']['production']['publication_platforms'][0], user_to_set)

        raw = self.get('/coverages/{cov_id}'.format(cov_id=cov_id))
        r = self.assert_sucessful_call(raw, 200)['coverages'][0]
        self.__assert_pub_platform_authent(r['environments']['production']['publication_platforms'][0], user_to_set)

    def __create_geo_contributor(self, id, data_source_id=None):
        post_data = {
            "id": id,
            "name": id,
            "data_type": DATA_TYPE_GEOGRAPHIC,
            "data_prefix": id
        }
        if data_source_id:
            post_data['data_sources'] = [
                {
                    "id": data_source_id,
                    "name": data_source_id,
                    "data_prefix": data_source_id[0:3],
                    "data_format": DATA_FORMAT_OSM_FILE
                }
            ]
        raw = self.post('/contributors', self.dict_to_json(post_data))
        self.assert_sucessful_create(raw)

    def test_post_coverage_with_input_data_source_ids_not_found(self):
        raw = self.post('/coverages',
                        self.dict_to_json({"id": "id_test", "name": "name of the coverage",
                                           "input_data_source_ids": ["123456"]}))
        r = self.assert_failed_call(raw)
        assert r == {'error': 'data source 123456 not found', 'message': 'Invalid arguments'}

    def test_post_coverage_with_one_existing_input_data_source_id(self, data_source):
        raw = self.post('/coverages',
                        self.dict_to_json({"id": "id_test", "name": "name of the coverage",
                                           "input_data_source_ids": ["ds_test"]}))
        r = self.get_coverage("id_test")
        assert r["input_data_source_ids"] == ["ds_test"]

    def test_post_coverage_with_two_same_existing_input_data_source_id(self, data_source):
        raw = self.post('/coverages',
                        self.dict_to_json({"id": "id_test", "name": "name of the coverage",
                                           "input_data_source_ids": ["ds_test", "ds_test"]}))
        r = self.get_coverage("id_test")
        assert r["input_data_source_ids"] == ["ds_test"]

    def test_post_coverage_with_2_input_data_source_ids_belonging_to_2_contributors_geographic(self):
        self.__create_geo_contributor('geo-1', 'foo')
        self.__create_geo_contributor('geo-2', 'bar')
        raw = self.post('/coverages',
                        self.dict_to_json({"id": "id_test", "name": "name of the coverage",
                                           "input_data_source_ids": ["foo", "bar"]}))
        r = self.assert_failed_call(raw)
        assert r == {
            'error': 'unable to have more than one data source from more than 2 contributors of type geographic by coverage',
            'message': 'Invalid arguments'
        }

    def test_put_coverage_id(self, coverage):
        coverage['id'] = 'changed'
        raw = self.put('/coverages/jdr', self.dict_to_json(coverage))
        self.assert_failed_call(raw)
        assert self.json_to_dict(raw) == {
            'error': 'the modification of the id is not possible',
            'message': 'Invalid arguments'
        }

    def test_put_invalid_coverage_missing_data_preserve_existing_one(self, coverage):
        del coverage['name']
        raw = self.put('/coverages/{}'.format(coverage['id']), self.dict_to_json(coverage))
        self.assert_failed_call(raw)
        assert self.json_to_dict(raw) == {
            'error': {'name': ['Missing data for required field.']},
            'message': 'Invalid arguments'
        }
        raw = self.get('/coverages/{}'.format(coverage['id']))
        self.assert_sucessful_call(raw)

    def test_put_invalid_coverage_added_data_preserve_existing_one(self, coverage):
        coverage['invalid'] = 'value'
        raw = self.put('/coverages/{}'.format(coverage['id']), self.dict_to_json(coverage))
        self.assert_failed_call(raw)
        assert self.json_to_dict(raw) == {
            'error': {'_schema': ['unknown field name invalid']},
            'message': 'Invalid arguments'
        }
        raw = self.get('/coverages/{}'.format(coverage['id']))
        self.assert_sucessful_call(raw)

    def test_put_coverage_simple(self, coverage, contributor):
        update = {
            'name': 'new_name',
            'license': {
                'name': 'public',
                'url': 'http://whatever.com'
            },
            'type': 'keolis',
            'short_description': 'a short description',
            'comment': 'a comment'
        }
        expected = {
            'coverages': [{
                'environments': {}, 'data_sources': [],
                'license': {'url': 'http://whatever.com', 'name': 'public'},
                'processes': [],
                'input_data_source_ids': [],
                'name': 'new_name', 'id': 'jdr',
                'last_active_job': None,
                'type': 'keolis',
                'short_description': 'a short description',
                'comment': 'a comment'
            }]
        }
        raw = self.put('coverages/{}'.format(coverage['id']), self.dict_to_json(update))
        self.assert_sucessful_call(raw)
        assert self.json_to_dict(raw) == expected
        assert self.get_coverage(coverage['id']) == expected['coverages'][0]

    def test_put_coverage_process(self):
        cov_id = 'my-cov'
        coverage = self.init_coverage(cov_id, [], [{
            "id": "process_old_id",
            "type": "FusioDataUpdate",
            "params": {
                "url": "http://fusio_host.old/cgi-bin/fusio.dll/api"
            },
            "sequence": 4
        }])
        coverage['processes'] = [
            {
                "id": "process_1",
                "type": "FusioDataUpdate",
                "params": {
                    "url": "http://fusio_host/cgi-bin/fusio.dll/api"
                },
                "sequence": 0
            },
            {
                "id": "process_2",
                "type": "FusioImport",
                "params": {
                    "url": "http://fusio_host/cgi-bin/fusio.dll/api",
                    "export_type": "gtfsv2"
                },
                "sequence": 1
            },
        ]
        expected = {
            'coverages': [{
                'name': 'my-cov',
                'type': 'other',
                'short_description': 'description of coverage my-cov',
                'comment': '',
                'processes': [
                    {'id': 'process_1', 'type': 'FusioDataUpdate',
                     'params': {'url': 'http://fusio_host/cgi-bin/fusio.dll/api'},
                     'data_source_ids': [], 'sequence': 0, 'enabled': True},
                    {'id': 'process_2', 'type': 'FusioImport',
                     'params': {'url': 'http://fusio_host/cgi-bin/fusio.dll/api',
                                'export_type': 'gtfsv2'}, 'data_source_ids': [],
                     'sequence': 1, 'enabled': True}
                ],
                'id': 'my-cov',
                'input_data_source_ids': [], 'license': {'url': '', 'name': 'Private (unspecified)'},
                'data_sources': [], 'environments': {}, 'last_active_job': None
            }]
        }

        raw = self.put('coverages/{}'.format(coverage['id']), self.dict_to_json(coverage))
        self.assert_sucessful_call(raw)
        assert self.json_to_dict(raw) == expected
        assert self.get_coverage(coverage['id']) == expected['coverages'][0]

    def test_put_coverage_publications(self):
        cov_id = 'my-cov'
        coverage = self.init_coverage(cov_id, environments={
            'production': {
                'name': 'production',
                'sequence': 0,
                "publication_platforms": [
                    {
                        "protocol": "ftp",
                        "url": "ftp.ods.com",
                        "sequence": 0
                    },
                    {
                        "protocol": "ftp",
                        "url": "ftp.ods.com.backup",
                        "sequence": 1
                    }
                ]
            }
        })
        coverage['environments'] = {
            'production': {
                'name': 'production',
                'sequence': 2,
                "publication_platforms": [
                    {
                        "protocol": "ftp",
                        "url": "ftp.ods.com.new",
                        "sequence": 0
                    }
                ]
            },
            'integration': {
                'name': 'integration',
                'sequence': 1,
                "publication_platforms": [
                    {
                        "protocol": "http",
                        "url": "http://tyr.integ/deploy",
                        "sequence": 1,
                        "input_data_source_ids": ['id-1']
                    },
                    {
                        "protocol": "ftp",
                        "url": "ftp.ods.com.integration",
                        "sequence": 2
                    }
                ]
            }
        }
        expected = {
            'coverages': [{
                'environments': {
                    'production': {
                        'sequence': 2, 'current_ntfs_id': None, 'publication_platforms': [
                            {'url': 'ftp.ods.com.new', 'sequence': 0, 'options': None, 'protocol': 'ftp',
                             'input_data_source_ids': [],
                             }], 'name': 'production'
                    },
                    'integration': {
                        'sequence': 1, 'current_ntfs_id': None,
                        'publication_platforms': [
                            {'url': 'http://tyr.integ/deploy', 'sequence': 1, 'options': None, 'protocol': 'http',
                             'input_data_source_ids': ['id-1']},
                            {'url': 'ftp.ods.com.integration', 'sequence': 2, 'options': None, 'protocol': 'ftp',
                             'input_data_source_ids': []}
                        ],
                        'name': 'integration'}
                },
                'license': {'url': '', 'name': 'Private (unspecified)'}, 'processes': [], 'id': 'my-cov',
                'name': 'my-cov', 'input_data_source_ids': [],
                'comment': '', 'type': 'other',
                'short_description': 'description of coverage my-cov', 'data_sources': [], 'last_active_job': None
            }]
        }

        raw = self.put('coverages/{}'.format(coverage['id']), self.dict_to_json(coverage))
        self.assert_sucessful_call(raw)
        assert self.json_to_dict(raw) == expected
        assert self.get_coverage(coverage['id']) == expected['coverages'][0]

    def test_post_coverage_publication_with_input_data_source_ids(self):
        cov_id = 'covid'
        self.init_coverage(cov_id, environments={
            'production': {
                'name': 'production',
                'sequence': 0,
                "publication_platforms": [
                    {
                        "protocol": "ftp",
                        "url": "ftp.ods.com",
                        "sequence": 0,
                        "input_data_source_ids": ['my-ds-id']
                    }
                ]
            }
        })
        ods_platform = self.get_coverage(cov_id)['environments']['production']['publication_platforms'][0]
        assert ods_platform['input_data_source_ids'] == ['my-ds-id']

    def test_put_coverage_with_input_data_source_ids(self, coverage, data_source):
        update = {
            'name': 'new_name',
            'input_data_source_ids': ['ds_test'],
        }
        raw = self.put('coverages/{}'.format(coverage['id']), self.dict_to_json(update))
        assert self.assert_sucessful_call(raw)['coverages'][0]["input_data_source_ids"] == ["ds_test"]

    def test_put_coverage_preserve_hidden_password_if_username_doesnt_change(self):
        cov_id = 'covid'
        password = "my_secret_password"
        self.init_coverage(cov_id, environments={
            'production': {
                'name': 'production',
                'sequence': 0,
                "publication_platforms": [
                    {
                        "protocol": "ftp",
                        "url": "ftp.ods.com",
                        "sequence": 0,
                        "options": {
                            "authent": {
                                "username": "my_user",
                                "password": password,
                            }
                        }
                    }
                ]
            }
        })
        coverage = self.get_coverage(cov_id)
        ods_platform = coverage['environments']['production']['publication_platforms'][0]
        assert 'authent' in ods_platform['options']
        assert 'username' in ods_platform['options']['authent']
        assert 'password' not in ods_platform['options']['authent']
        coverage['name'] = 'new_name'
        self.put('/coverages/{}'.format(cov_id), self.dict_to_json(coverage))
        with tartare.app.app_context():
            coverage = Coverage.get(cov_id)
            assert coverage.name == 'new_name'
            assert coverage.environments['production'].publication_platforms[0].options.authent.password == password

    def test_put_coverage_remove_password_if_username_change(self):
        cov_id = 'covid'
        self.init_coverage(cov_id, environments={
            'production': {
                'name': 'production',
                'sequence': 0,
                "publication_platforms": [
                    {
                        "protocol": "ftp",
                        "url": "ftp.ods.com",
                        "sequence": 0,
                        "options": {
                            "authent": {
                                "username": "my_user",
                                "password": "my_secret_password",
                            }
                        }
                    }
                ]
            }
        })
        coverage = self.get_coverage(cov_id)
        ods_platform = coverage['environments']['production']['publication_platforms'][0]
        assert 'authent' in ods_platform['options']
        assert 'username' in ods_platform['options']['authent']
        assert 'password' not in ods_platform['options']['authent']
        ods_platform['options']['authent']['username'] = 'new_user'
        self.put('/coverages/{}'.format(cov_id), self.dict_to_json(coverage))
        with tartare.app.app_context():
            coverage = Coverage.get(cov_id)
            assert coverage.environments['production'].publication_platforms[0].options.authent.password is None

    def test_post_coverage_with_data_source_and_password_hidden(self):
        username = 'my_user'
        password = 'my_secret_password'
        self.init_coverage('cid', data_sources=[
            {
                'id': 'dsid',
                'name': 'dsid',
                'input': {
                    'type': 'auto',
                    'url': 'whatever',
                    "frequency": {
                        "type": "daily",
                        "hour_of_day": 20
                    },
                    'options': {
                        'authent': {
                            'username': username,
                            'password': password,
                        }
                    }
                }
            }
        ])
        data_source = self.get_coverage('cid')['data_sources'][0]
        self.assert_data_source_has_username_and_password(data_source, username, password, Coverage)

    def test_put_coverage_with_data_source_and_password_hidden(self):
        username = 'my_user'
        password = 'my_secret_password'
        self.init_coverage('cid', data_sources=[
            {
                'id': 'dsid',
                'name': 'dsid',
                'input': {
                    'type': 'auto',
                    'url': 'whatever',
                    "frequency": {
                        "type": "daily",
                        "hour_of_day": 20
                    },
                    'options': {
                        'authent': {
                            'username': username,
                            'password': password,
                        }
                    }
                }
            }
        ])
        # update coverage preserve password
        coverage = self.get_coverage('cid')
        coverage['name'] = 'new_name'
        self.put('/coverages/cid', self.dict_to_json(coverage))
        coverage_updated = self.get_coverage('cid')
        assert coverage_updated['name'] == 'new_name'
        data_source = coverage_updated['data_sources'][0]
        self.assert_data_source_has_username_and_password(data_source, username, password, Coverage)

        # update password
        data_source['input']['options']['authent']['password'] = 'new_password'
        self.put('/coverages/cid', self.dict_to_json(coverage_updated))
        coverage_updated_password = self.get_coverage('cid')
        data_source_with_new_password = coverage_updated_password['data_sources'][0]
        self.assert_data_source_has_username_and_password(data_source_with_new_password, username, 'new_password',
                                                          Coverage)

        # update username
        data_source_with_new_password['input']['options']['authent']['username'] = 'new_user'
        self.put('/coverages/cid', self.dict_to_json(coverage_updated_password))
        final_coverage = self.get_coverage('cid')
        assert not final_coverage['data_sources'][0]['input']['options']['authent']['password']
        with tartare.app.app_context():
            coverage = Coverage.get('cid')
            assert not coverage.data_sources[0].input.options.authent.password

    def test_post_coverage_duplicate_data_source(self):
        raw = self.init_coverage('cid', data_sources=[
            {
                'id': 'dsid',
                'name': 'dsid',
                'input': {'type': 'manual'}
            },
            {
                'id': 'dsid',
                'name': 'dsid',
                'input': {'type': 'manual'}
            }
        ], check_success=False)
        r = self.assert_failed_call(raw, 409)
        assert r["error"] == "duplicate data source dsid"
        assert r["message"] == "Duplicate entry"

    def test_put_coverage_duplicate_data_source(self):
        coverage = self.init_coverage('cid', data_sources=[
            {
                'id': 'dsid',
                'name': 'dsid',
                'input': {'type': 'manual'}
            }
        ])
        coverage['data_sources'].append(
            {
                'id': 'dsid',
                'name': 'dsid',
                'input': {'type': 'manual'}
            }
        )
        raw = self.put('/coverages/cid', self.dict_to_json(coverage))
        r = self.assert_failed_call(raw, 409)
        assert r["error"] == "duplicate data source dsid"
        assert r["message"] == "Duplicate entry"

    def test_post_coverage_existing_data_source(self):
        self.init_coverage('cid', data_sources=[
            {
                'id': 'dsid',
                'name': 'dsid',
                'input': {'type': 'manual'}
            }
        ])
        raw = self.init_coverage('cid2', data_sources=[
            {
                'id': 'dsid',
                'name': 'dsid',
                'input': {'type': 'manual'}
            }
        ], check_success=False)
        r = self.assert_failed_call(raw, 409)
        assert r["error"].startswith("duplicate entry:")
        assert r["message"] == "Duplicate entry"

    def test_put_coverage_existing_data_source(self):
        self.init_coverage('cid', data_sources=[
            {
                'id': 'dsid',
                'name': 'dsid',
                'input': {'type': 'manual'}
            }
        ])
        coverage2 = self.init_coverage('cid2')
        coverage2['data_sources'].append({
            'id': 'dsid',
            'name': 'dsid',
            'input': {'type': 'manual'}
        })
        raw = self.put('/coverages/cid2', self.dict_to_json(coverage2))
        r = self.assert_failed_call(raw, 409)
        assert r["error"].startswith("duplicate entry:")
        assert r["message"] == "Duplicate entry"
