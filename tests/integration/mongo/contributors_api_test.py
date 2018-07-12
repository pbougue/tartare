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

import pytest

import tartare
from tartare.core.constants import DATA_TYPE_VALUES, DATA_FORMAT_BY_DATA_TYPE, DATA_FORMAT_VALUES, DATA_FORMAT_OSM_FILE, \
    DATA_TYPE_GEOGRAPHIC, DATA_FORMAT_BANO_FILE, DATA_FORMAT_POLY_FILE, DATA_TYPE_PUBLIC_TRANSPORT, \
    DATA_FORMAT_PT_EXTERNAL_SETTINGS, INPUT_TYPE_COMPUTED, DATA_FORMAT_OBITI, DATA_FORMAT_DIRECTION_CONFIG
from tartare.core.models import Contributor
from tests.integration.test_mechanism import TartareFixture


class TestContributors(TartareFixture):
    def test_get_contributors_empty_success(self):
        raw = self.get('/contributors')
        assert raw.status_code == 200
        raw = self.get('/contributors/')
        assert raw.status_code == 200
        r = self.json_to_dict(raw)
        assert len(r["contributors"]) == 0

    def test_get_contributors_non_exist(self):
        raw = self.get('/contributors/id_test')
        assert raw.status_code == 404
        r = self.json_to_dict(raw)
        assert 'message' in r

    def test_add_contributor_without_id(self):
        raw = self.post('/contributors', '{"name":"whatever", "data_prefix":"any_prefix"}')
        assert raw.status_code == 201
        r = self.json_to_dict(raw)
        assert len(r["contributors"]) == 1

    def test_add_contributor_empty_id(self):
        raw = self.post('/contributors', '{"id": "", "name":"whatever", "data_prefix":"any_prefix"}')
        r = self.json_to_dict(raw)

        assert 'error' in r
        assert raw.status_code == 400
        assert r['error'] == {
            'id': ['field cannot be empty']
        }

    def test_add_contributor_without_data_prefix(self):
        raw = self.post('/contributors', '{"id": "id_test", "name":"whatever"}')
        assert raw.status_code == 400
        r = self.json_to_dict(raw)
        assert 'error' in r
        assert r['error'] == "contributor data_prefix must be specified"

    def test_add_contributor_returns_success(self):
        raw = self.post('/contributors', '{"id": "id_test", "name":"name_test", "data_prefix":"AAA"}')
        assert raw.status_code == 201
        raw = self.get('/contributors')
        r = self.json_to_dict(raw)

        assert len(r["contributors"]) == 1
        assert isinstance(r["contributors"], list)
        assert r["contributors"][0]["id"] == "id_test"
        assert r["contributors"][0]["name"] == "name_test"
        assert r["contributors"][0]["data_prefix"] == "AAA"
        assert r["contributors"][0]["data_type"] == "public_transport"

    def test_add_contributor_with_data_type_geographic(self):
        raw = self.post('/contributors', '{"id": "id_test", "name":"name_test", '
                                         '"data_prefix":"AAA", "data_type": "geographic"}')
        assert raw.status_code == 201
        raw = self.get('/contributors')
        r = self.json_to_dict(raw)

        assert len(r["contributors"]) == 1
        assert isinstance(r["contributors"], list)
        assert r["contributors"][0]["id"] == "id_test"
        assert r["contributors"][0]["name"] == "name_test"
        assert r["contributors"][0]["data_prefix"] == "AAA"
        assert r["contributors"][0]["data_type"] == "geographic"

    def test_add_contributor_with_invalid_data_type(self):
        raw = self.post('/contributors', '{"id": "id_test", "name":"name_test", '
                                         '"data_prefix":"AAA", "data_type": "bob"}')
        assert raw.status_code == 400
        r = self.json_to_dict(raw)
        assert 'error' in r
        assert r['error'] == {
            'data_type': ['choice "bob" not in possible values (geographic, public_transport).']}

    def test_add_contributors_no_id(self):
        raw = self.post('/contributors', '{"name": "name_test"}')
        r = self.json_to_dict(raw)
        assert 'error' in r
        assert raw.status_code == 400
        raw = self.get('/contributors')
        r = self.json_to_dict(raw)
        assert len(r["contributors"]) == 0

    def test_add_coverage_no_name(self):
        raw = self.post('/contributors', '{"id": "id_test"}')
        r = self.json_to_dict(raw)
        assert 'error' in r
        assert raw.status_code == 400
        raw = self.get('/contributors')
        r = self.json_to_dict(raw)
        assert len(r["contributors"]) == 0

    def test_add_coverage_no_prefix(self):
        raw = self.post('/contributors', '{"id": "id_test", "name":"name_test"}')
        r = self.json_to_dict(raw)
        assert 'error' in r
        assert raw.status_code == 400
        raw = self.get('/contributors')
        r = self.json_to_dict(raw)
        assert len(r["contributors"]) == 0

    def test_add_contributors_unique_data_suffix_ok(self):
        raw = self.post('/contributors', '{"id": "id_test1", "name":"name_test1", "data_prefix":"AAA"}')
        assert raw.status_code == 201
        raw = self.post('/contributors', '{"id": "id_test2", "name":"name_test2", "data_prefix":"AAB"}')
        assert raw.status_code == 201
        raw = self.get('/contributors')
        r = self.json_to_dict(raw)
        assert len(r["contributors"]) == 2

    def test_add_contributors_unique_data_suffix_error(self):
        raw = self.post('/contributors', '{"id": "id_test1", "name":"name_test1", "data_prefix":"AAA"}')
        assert raw.status_code == 201
        raw = self.post('/contributors', '{"id": "id_test2", "name":"name_test2", "data_prefix":"AAA"}')
        assert raw.status_code == 409
        raw = self.get('/contributors')
        r = self.json_to_dict(raw)
        assert len(r["contributors"]) == 1

    def test_post_contrib_no_data_source(self):
        raw = self.post('/contributors', '{"id": "id_test", "name":"name_test", "data_prefix":"AAA"}')
        assert raw.status_code == 201
        raw = self.get('/contributors/id_test/')
        r = self.json_to_dict(raw)
        print(r)
        assert raw.status_code == 200
        assert len(r["contributors"][0]["data_sources"]) == 0

    def test_post_contrib_with_existing_id(self, contributor):
        post_data = {
            "id": "id_test",
            "name": "name_test",
            "data_prefix": "OOO",
        }
        raw = self.post('/contributors', json.dumps(post_data))
        assert raw.status_code == 409
        r = self.json_to_dict(raw)
        assert r["error"].startswith("duplicate entry:")
        assert "id" in r["error"]
        assert r["message"] == "Duplicate entry"

    def test_post_contrib_with_existing_data_prefix(self, contributor):
        post_data = {
            "id": "stif",
            "name": "stif",
            "data_prefix": "AAA",
        }
        raw = self.post('/contributors', json.dumps(post_data))
        assert raw.status_code == 409
        r = self.json_to_dict(raw)
        assert r["error"].startswith("duplicate entry:")
        assert "data_prefix" in r["error"]
        assert r["message"] == "Duplicate entry"

    def test_post_contrib_with_existing_data_source_id(self, contributor, data_source):
        post_data = {
            "id": "stif",
            "name": "stif",
            "data_prefix": "BBB",
            "data_sources": [
                {
                    "id": data_source["id"],
                    "name": "data_source_name",
                    "input": {
                        "type": "auto",
                        "url": "http://stif.com/od.zip",
                        "frequency": {
                            "type": "daily",
                            "hour_of_day": 20
                        }
                    }
                },
            ]
        }

        raw = self.post('/contributors', json.dumps(post_data))
        assert raw.status_code == 409
        r = self.json_to_dict(raw)
        assert r["error"].startswith("duplicate entry:")
        assert "data_sources.id" in r["error"]
        assert r["message"] == "Duplicate entry"

    def test_post_contrib_with_two_data_sources_with_same_ids(self):
        post_data = {
            "id": "stif",
            "name": "stif",
            "data_prefix": "BBB",
            "data_sources": [
                {
                    "id": "ds_id",
                    "name": "data_source_name",
                    "input": {
                        "type": "manual"
                    }
                },
                {
                    "id": "ds_id",
                    "name": "data_source_name",
                    "input": {
                        "type": "manual"
                    }
                }
            ]
        }

        raw = self.post('/contributors', json.dumps(post_data))
        assert raw.status_code == 409
        r = self.json_to_dict(raw)
        assert r["error"] == "duplicate data source ds_id"
        assert r["message"] == "Duplicate entry"

    def test_delete_contributors_returns_success(self):
        raw = self.get('/contributors/id_test')
        assert raw.status_code == 404

        raw = self.post('/contributors', '{"id": "id_test", "name": "name_test", "data_prefix":"AAA"}')
        assert raw.status_code == 201
        raw = self.delete('/contributors/id_test')
        self.assert_sucessful_call(raw, 204)
        raw = self.get('/contributors/id_test')
        assert raw.status_code == 404

        raw = self.post('/contributors', '{"id": "id_test2", "name": "name_test2", "data_prefix":"AAA"}')
        assert raw.status_code == 201
        raw = self.get('/contributors')
        r = self.json_to_dict(raw)
        assert len(r["contributors"]) == 1

    def test_update_contributor_name(self, contributor):
        contributor['name'] = 'new_name_test'
        raw = self.put('/contributors/id_test', self.dict_to_json(contributor))
        r = self.assert_sucessful_call(raw)
        assert r["contributors"][0]['id'] == "id_test"
        assert r["contributors"][0]['name'] == "new_name_test"

    def test_update_contributor_data_prefix(self, contributor):
        contributor['data_prefix'] = 'BBB'
        raw = self.put('/contributors/id_test', self.dict_to_json(contributor))
        r = self.assert_sucessful_call(raw)
        assert r["contributors"][0]['id'] == "id_test"
        assert r["contributors"][0]['data_prefix'] == "BBB"

    def test_update_unknown_contributor(self):
        raw = self.put('/contributors/unknown', '{"data_prefix": "toto", "name": "new_name_test"}')
        self.assert_failed_call(raw, 404)

    def test_update_contributor_id_impossible(self, contributor):
        contributor['id'] = 'bob'
        raw = self.put('/contributors/id_test', self.dict_to_json(contributor))
        r = self.assert_failed_call(raw)
        assert 'error' in r

    def test_post_contrib_one_data_source_without_id(self):
        post_data = {
            "id": "id_test",
            "name": "name_test",
            "data_prefix": "AAA",
            "data_sources": [
                {
                    "name": "data_source_name",
                    "input": {
                        "type": "auto",
                        "url": "http://stif.com/od.zip",
                        "frequency": {
                            "type": "daily",
                            "hour_of_day": 20
                        }
                    }
                }
            ]
        }
        raw = self.post('/contributors', json.dumps(post_data))
        self.assert_sucessful_create(raw)
        raw = self.get('/contributors/id_test/')
        r = self.assert_sucessful_call(raw)
        assert len(r["contributors"][0]["data_sources"]) == 1

    def test_post_contrib_one_data_source_with_frequency(self):
        post_data = {
            "id": "id_test",
            "name": "name_test",
            "data_prefix": "AAA",
            "data_sources": [
                {
                    "name": "data_source_name",
                    "input": {
                        "type": "auto",
                        "url": "http://stif.com/od.zip",
                        "frequency": {
                            "type": "continuously",
                            "minutes": 5,
                            "enabled": True
                        }
                    },
                },
                {
                    "name": "data_source_name",
                    "input": {
                        "type": "auto",
                        "url": "http://stif.com/od.zip",
                        "frequency": {
                            "type": "daily",
                            "hour_of_day": 14,
                            "enabled": False
                        }
                    },
                },
                {
                    "name": "data_source_name",
                    "input": {
                        "type": "auto",
                        "url": "http://stif.com/od.zip",
                        "frequency": {
                            "type": "weekly",
                            "day_of_week": 'Friday',
                            "hour_of_day": 6,
                            "enabled": True
                        }
                    },

                },
                {
                    "name": "data_source_name",
                    "input": {
                        "type": "auto",
                        "url": "http://stif.com/od.zip",
                        "frequency": {
                            "type": "monthly",
                            "day_of_month": 10,
                            "hour_of_day": 6,
                            "enabled": True
                        }
                    },

                }
            ]
        }
        raw = self.post('/contributors', json.dumps(post_data))
        self.assert_sucessful_create(raw)
        raw = self.get('/contributors/id_test/')
        r = self.assert_sucessful_call(raw)
        assert len(r["contributors"][0]["data_sources"]) == 4, print(r["contributors"][0]["data_sources"])

        frequency = r["contributors"][0]["data_sources"][0]['input']['frequency']
        assert frequency['type'] == 'continuously'
        assert frequency['minutes'] == 5
        assert frequency['enabled'] is True

        frequency = r["contributors"][0]["data_sources"][1]['input']['frequency']
        assert frequency['type'] == 'daily'
        assert frequency['hour_of_day'] == 14
        assert frequency['enabled'] is False

        frequency = r["contributors"][0]["data_sources"][2]['input']['frequency']
        assert frequency['type'] == 'weekly'
        assert frequency['day_of_week'] == 'Friday'
        assert frequency['hour_of_day'] == 6
        assert frequency['enabled'] is True

        frequency = r["contributors"][0]["data_sources"][3]['input']['frequency']
        assert frequency['type'] == 'monthly'
        assert frequency['day_of_month'] == 10
        assert frequency['hour_of_day'] == 6
        assert frequency['enabled'] is True

    @pytest.mark.parametrize("minutes", [-50, -1, 0])
    def test_post_contrib_one_data_source_with_continuously_frequency_and_invalid_minutes(self, minutes):
        post_data = {
            "id": "id_test",
            "name": "name_test",
            "data_prefix": "AAA",
            "data_sources": [
                {
                    "name": "data_source_name",
                    "input": {
                        "type": "auto",
                        "url": "http://stif.com/od.zip",
                        "frequency": {
                            "type": "continuously",
                            "minutes": minutes
                        }
                    },
                }
            ]
        }
        raw = self.post('/contributors', json.dumps(post_data))
        r = self.assert_failed_call(raw)
        assert r == {
            'error': {
                'data_sources': {'0': {'input': {'frequency': {'minutes': ['minutes should be greater than 1']}}}}},
            'message': 'Invalid arguments'
        }

    @pytest.mark.parametrize("hour_of_day", [-5, -1, 24, 50])
    def test_post_contrib_one_data_source_with_daily_frequency_and_invalid_hour(self, hour_of_day):
        post_data = {
            "id": "id_test",
            "name": "name_test",
            "data_prefix": "AAA",
            "data_sources": [
                {
                    "name": "data_source_name",
                    "input": {
                        "type": "auto",
                        "url": "http://stif.com/od.zip",
                        "frequency": {
                            "type": "daily",
                            "hour_of_day": hour_of_day
                        }
                    },
                }
            ]
        }
        raw = self.post('/contributors', json.dumps(post_data))
        r = self.assert_failed_call(raw)
        assert r == {
            'error': {
                'data_sources': {
                    '0': {'input': {'frequency': {'hour_of_day': ['hour_of_day should be between 0 and 23']}}}}},
            'message': 'Invalid arguments'
        }

    @pytest.mark.parametrize("day_of_week,hour_of_day", [
        ('mondaay', -10), ('lundi', -1), ('unknown', 24), ('wednesday', 36)
    ])
    def test_post_contrib_one_data_source_with_weekly_frequency_and_invalid_params(self, day_of_week, hour_of_day):
        post_data = {
            "id": "id_test",
            "name": "name_test",
            "data_prefix": "AAA",
            "data_sources": [
                {
                    "name": "data_source_name",
                    "input": {
                        "type": "auto",
                        "url": "http://stif.com/od.zip",
                        "frequency": {
                            "type": "weekly",
                            "day_of_week": day_of_week,
                            "hour_of_day": hour_of_day
                        }
                    },
                }
            ]
        }
        raw = self.post('/contributors', json.dumps(post_data))
        r = self.assert_failed_call(raw)
        assert r == {'error': {
            'data_sources': {'0': {'input': {'frequency': {
                'day_of_week': [
                    'day_of_week should be one of Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday'],
                'hour_of_day': ['hour_of_day should be between 0 and 23']
            }}}}}, 'message': 'Invalid arguments'
        }

    @pytest.mark.parametrize("day_of_month,hour_of_day", [
        (-5, -10), (-1, -1), (29, 24), (34, 36)
    ])
    def test_post_contrib_one_data_source_with_monthly_frequency_and_invalid_params(self, day_of_month, hour_of_day):
        post_data = {
            "id": "id_test",
            "name": "name_test",
            "data_prefix": "AAA",
            "data_sources": [
                {
                    "name": "data_source_name",
                    "input": {
                        "type": "auto",
                        "url": "http://stif.com/od.zip",
                        "frequency": {
                            "type": "monthly",
                            "day_of_month": day_of_month,
                            "hour_of_day": hour_of_day
                        }
                    },
                }
            ]
        }
        raw = self.post('/contributors', json.dumps(post_data))
        r = self.assert_failed_call(raw)
        assert r == {'error': {
            'data_sources': {'0': {'input': {'frequency': {
                'day_of_month': ['day_of_month should be between 1 and 28'],
                'hour_of_day': ['hour_of_day should be between 0 and 23']
            }}}}}, 'message': 'Invalid arguments'
        }

    def test_post_contrib_one_data_source_with_id(self):
        post_data = {
            "id": "id_test",
            "name": "name_test",
            "data_prefix": "AAA",
            "data_sources": [
                {
                    "id": "data_source_id",
                    "name": "data_source_name",
                    "input": {
                        "type": "auto",
                        "url": "http://stif.com/od.zip",
                        "frequency": {
                            "type": "daily",
                            "hour_of_day": 20
                        }
                    }
                }
            ]
        }
        raw = self.post('/contributors', json.dumps(post_data))
        assert raw.status_code == 201, print(self.json_to_dict(raw))
        raw = self.get('/contributors/id_test/')
        r = self.json_to_dict(raw)
        self.assert_sucessful_call(raw)
        assert len(r["contributors"][0]["data_sources"]) == 1

    def test_post_contrib_one_data_source_with_service_id(self):
        post_data = {
            "id": "id_test",
            "name": "name_test",
            "data_prefix": "AAA",
            "data_sources": [
                {
                    "id": "data_source_id",
                    "name": "data_source_name",
                    "service_id": "Google-1",
                    "input": {
                        "type": "auto",
                        "url": "http://stif.com/od.zip",
                        "frequency": {
                            "type": "daily",
                            "hour_of_day": 20
                        }
                    }
                }
            ]
        }
        raw = self.post('/contributors', json.dumps(post_data))
        assert raw.status_code == 201, print(self.json_to_dict(raw))
        raw = self.get('/contributors/id_test/')
        r = self.json_to_dict(raw)
        self.assert_sucessful_call(raw)
        assert len(r["contributors"][0]["data_sources"]) == 1
        assert r["contributors"][0]["data_sources"][0]["service_id"] == "Google-1"

    def test_post_contrib_one_data_source_with_invalid_input(self):
        post_data = {
            "id": "id_test",
            "name": "name_test",
            "data_prefix": "AAA",
            "data_sources": [
                {
                    "name": "data_source_name",
                    "data_format": "gtfs",
                    "input": {
                        "type": "unknown",
                    }
                }
            ]
        }
        raw = self.post('/contributors', json.dumps(post_data))
        assert raw.status_code == 400, print(self.json_to_dict(raw))
        r = self.json_to_dict(raw)
        assert 'error' in r
        assert r == {'error': {'data_sources': {'0': {'input': {'type': ['Unsupported value: unknown']}}}},
                     'message': 'Invalid arguments'}

    def test_post_contrib_one_data_source_with_invalid_data_format(self):
        post_data = {
            "id": "id_test",
            "name": "name_test",
            "data_prefix": "AAA",
            "data_sources": [
                {
                    "name": "data_source_name",
                    "data_format": "Neptune",
                    "input": {
                        "type": "auto",
                        "url": "http://stif.com/od.zip"
                    }
                }
            ]
        }
        raw = self.post('/contributors', json.dumps(post_data))
        assert raw.status_code == 400, print(self.json_to_dict(raw))
        r = self.json_to_dict(raw)
        assert 'error' in r
        assert r['message'] == 'Invalid arguments'

    def test_post_contrib_two_data_source(self):
        post_data = {
            "id": "id_test",
            "name": "name_test",
            "data_prefix": "AAA",
            "data_sources": [
                {
                    "name": "data_source_name",
                    "input": {
                        "type": "auto",
                        "url": "http://stif.com/od.zip",
                        "frequency": {
                            "type": "daily",
                            "hour_of_day": 20
                        }
                    }
                },
                {
                    "name": "data_source_name2",
                    "input": {
                        "type": "auto",
                        "url": "http://stif.com/od.zip",
                        "frequency": {
                            "type": "daily",
                            "hour_of_day": 20
                        }
                    }
                }
            ]
        }
        raw = self.post('/contributors', json.dumps(post_data))
        assert raw.status_code == 201
        raw = self.get('/contributors/id_test/')
        r = self.json_to_dict(raw)
        self.assert_sucessful_call(raw)
        assert len(r["contributors"][0]["data_sources"]) == 2
        assert r["contributors"][0]["data_sources"][0]["id"] != r["contributors"][0]["data_sources"][1]["id"]

    def test_put_contrib_data_source_with_full_contributor(self):
        post_data = {
            "id": "id_test",
            "name": "name_test",
            "data_prefix": "AAA",
            "data_sources": [
                {
                    "name": "data_source_name",
                    "input": {
                        "type": "auto",
                        "url": "http://stif.com/od.zip",
                        "frequency": {
                            "type": "daily",
                            "hour_of_day": 20
                        }
                    }
                }
            ]
        }
        raw = self.post('/contributors', self.dict_to_json(post_data))
        self.assert_sucessful_create(raw)
        post_data["data_sources"][0]["name"] = "name_modified"
        raw = self.put('/contributors/id_test', self.dict_to_json(post_data))
        r = self.assert_sucessful_call(raw)
        assert len(r["contributors"][0]["data_sources"]) == 1
        patched_data_source = r["contributors"][0]["data_sources"][0]
        assert patched_data_source["name"] == "name_modified"

    def test_put_contrib_add_data_source_with_existing_id(self):
        self.init_contributor('stif', 'ds_id_1', type='manual')
        raw = self.add_data_source_to_contributor('stif', 'ds_id_1', 'whatever', check_success=False)
        r = self.assert_failed_call(raw, 409)
        assert r["error"] == "duplicate data source ds_id_1"
        assert r["message"] == "Duplicate entry"

    def test_put_contrib_with_different_input(self):
        post_data = {
            "id": "id_test",
            "name": "name_test",
            "data_prefix": "AAA",
            "data_sources": [
                {
                    "name": "data_source_name",
                    "input": {
                        "type": "auto",
                        "url": "http://stif.com/od.zip",
                        "frequency": {
                            "type": "daily",
                            "hour_of_day": 20
                        }
                    }
                }
            ]
        }
        raw = self.post('/contributors', self.dict_to_json(post_data))
        self.assert_sucessful_create(raw)
        post_data["data_sources"][0]["name"] = "name_modified"
        post_data["data_sources"][0]["input"] = {
            'type': 'manual'
        }
        raw = self.put('/contributors/id_test', self.dict_to_json(post_data))
        r = self.assert_sucessful_call(raw)
        assert len(r["contributors"][0]["data_sources"]) == 1
        patched_data_source = r["contributors"][0]["data_sources"][0]
        assert patched_data_source["name"] == "name_modified"
        assert patched_data_source["input"]["type"] == "manual"

    def test_put_contrib_with_different_frequency(self):
        post_data = {
            "id": "id_test",
            "name": "name_test",
            "data_prefix": "AAA",
            "data_sources": [
                {
                    "name": "data_source_name",
                    "input": {
                        "type": "auto",
                        "url": "http://stif.com/od.zip",
                        "frequency": {
                            "type": "daily",
                            "hour_of_day": 20
                        }
                    }
                }
            ]
        }
        raw = self.post('/contributors', self.dict_to_json(post_data))
        self.assert_sucessful_create(raw)
        post_data["data_sources"][0]["name"] = "name_modified"
        post_data["data_sources"][0]["input"] = {
            "type": "auto",
            "url": "http://stif.com/od.zip",
            "frequency": {
                "type": "continuously",
                "minutes": 30
            }
        }
        raw = self.put('/contributors/id_test', self.dict_to_json(post_data))
        r = self.assert_sucessful_call(raw)
        assert len(r["contributors"][0]["data_sources"]) == 1
        patched_data_source = r["contributors"][0]["data_sources"][0]
        assert patched_data_source["name"] == "name_modified"
        assert patched_data_source["input"]["type"] == "auto"
        assert patched_data_source["input"]["frequency"]["type"] == "continuously"
        assert patched_data_source["input"]["frequency"]["minutes"] == 30

    def test_put_contrib_processes_without_id(self, contributor):
        processes = [
            {
                "type": "Ruspell",
                "sequence": 1,
                "data_source_ids": [],
                "params": {
                    "bano_data_ids": ["bano_75", "bano_91"],
                    "config_file": "conf_yml"
                }
            },
            {
                "type": "HeadsignShortName",
                "sequence": 2,
                "data_source_ids": [],
            }
        ]
        contributor["processes"] = processes
        raw = self.put('/contributors/id_test', self.dict_to_json(contributor))
        r = self.assert_sucessful_call(raw)
        assert len(r["contributors"][0]["processes"]) == 2
        types = [p.get("type") for p in r["contributors"][0]["processes"]]
        excepted = [p.get("type") for p in processes]
        assert types.sort() == excepted.sort()

    def test_put_contrib_processes_with_id(self, contributor):
        processes = [
            {
                "id": "ruspell",
                "type": "Ruspell",
                "sequence": 1,
                "data_source_ids": [],
                "params": {
                    "bano_data_ids": ["bano_75", "bano_91"],
                    "config_file": "conf_yml"
                }
            }
        ]
        contributor["processes"] = processes
        raw = self.put('/contributors/id_test', self.dict_to_json(contributor))
        r = self.assert_sucessful_call(raw)
        assert len(r["contributors"][0]["processes"]) == 1
        assert r["contributors"][0]["processes"][0]['id'] == processes[0]["id"]
        assert r["contributors"][0]["processes"][0]['type'] == processes[0]["type"]

    def test_put_contrib_processes_type_unknown(self, contributor):
        processes = [
            {
                "id": "ruspell",
                "sequence": 1,
                "type": "BOB",
                "data_source_ids": ["datasource_stif"],
                "params": {
                    "bano_data_ids": ["bano_75", "bano_91"],
                    "config_file": "conf_yml"
                }
            }
        ]
        contributor["processes"] = processes
        raw = self.put('/contributors/id_test', self.dict_to_json(contributor))
        r = self.assert_failed_call(raw)
        assert "error" in r
        assert r["message"] == "Invalid arguments"
        assert r[
                   'error'] == "data_source referenced by id 'datasource_stif' in process 'BOB' not found in contributor"

    def test_put_contrib_processes_gtfs_agency_file(self, contributor):
        processes = [
            {
                "id": "gtfs_agency_file",
                "sequence": 1,
                "type": "GtfsAgencyFile",
                "params": {
                    "data_source_ids": ["tc-stif"],
                    "data": {
                        "agency_id": "112",
                        "agency_name": "stif",
                        "agency_url": "http://stif.com"
                    }
                }
            }
        ]
        contributor["processes"] = processes
        raw = self.put('/contributors/id_test', self.dict_to_json(contributor))
        r = self.assert_sucessful_call(raw)
        assert len(r["contributors"][0]["processes"]) == 1
        assert r["contributors"][0]["processes"][0]["id"] == processes[0]["id"]
        assert r["contributors"][0]["processes"][0]["sequence"] == processes[0]["sequence"]
        assert r["contributors"][0]["processes"][0]["type"] == processes[0]["type"]
        assert r["contributors"][0]["processes"][0]["params"]["data"]["agency_id"] == \
               processes[0]["params"]["data"]["agency_id"]
        assert r["contributors"][0]["processes"][0]["params"]["data"]["agency_name"] == \
               processes[0]["params"]["data"]["agency_name"]

    @pytest.mark.parametrize("data_sources,data_source_ids,missing_id", [
        ([], ['test'], 'test'),
        ([{'id': 'one-id'}], ['another-id'], 'another-id'),
        ([{'id': 'one-id'}], ['one-id', 'another-id'], 'another-id'),
        ([{'id': 'one-id'}, {'id': 'another-id'}], ['third-id'], 'third-id'),
        ([{'id': 'one-id'}, {'id': 'another-id'}], ['another-id', 'third-id'], 'third-id')
    ])
    def test_post_contrib_integrity_fail_data_source_ids(self, data_sources, data_source_ids, missing_id):
        payload = {
            "data_sources": data_sources,
            "processes": [
                {
                    "type": "GtfsAgencyFile",
                    "data_source_ids": data_source_ids
                }
            ]
        }
        raw = self.post('/contributors', json.dumps(payload))
        assert raw.status_code == 400
        r = self.json_to_dict(raw)
        assert r[
                   'error'] == "data_source referenced by id '{missing_id}' in process 'GtfsAgencyFile' not found in contributor".format(
            missing_id=missing_id)
        assert r['message'] == "Invalid arguments"

    @pytest.mark.parametrize("data_source_to_build_ids,process_data_source_ids,missing_id", [
        ([], ['test'], 'test'),
        (['one-id'], ['another-id'], 'another-id'),
        (['one-id'], ['one-id', 'another-id'], 'another-id'),
        (['one-id', 'another-id'], ['third-id'], 'third-id'),
        (['one-id', 'another-id'], ['another-id', 'third-id'], 'third-id')
    ])
    def test_put_contrib_integrity_fail_data_source_ids(self, data_source_to_build_ids, process_data_source_ids,
                                                        missing_id):
        data_sources = []
        for data_source_to_build_id in data_source_to_build_ids:
            data_sources.append({
                "id": data_source_to_build_id,
                "name": data_source_to_build_id,
                "input": {
                    "type": "auto",
                    "url": "http://stif.com/ods.zip",
                    "frequency": {
                        "type": "daily",
                        "hour_of_day": 20
                    }
                }
            })
        post_data = {
            "id": "id_test",
            "name": "name_test",
            "data_prefix": "AAA",
            "data_sources": data_sources
        }
        raw = self.post('/contributors', json.dumps(post_data))
        self.assert_sucessful_create(raw)
        post_data['processes'] = [
            {
                "type": "GtfsAgencyFile",
                "data_source_ids": process_data_source_ids
            }
        ]
        raw = self.put('/contributors/id_test', self.dict_to_json(post_data))
        r = self.assert_failed_call(raw)
        assert r['error'] == "data_source referenced by id '{missing_id}' in process 'GtfsAgencyFile' " \
                             "not found in contributor".format(missing_id=missing_id)
        assert r['message'] == "Invalid arguments"

    def __create_contributor(self, data_type, data_format):
        id = 'id-{}-{}'.format(data_type, data_format)
        post_data = {
            "id": id,
            "name": id,
            "data_type": data_type,
            "data_prefix": id,
            "data_sources": [
                {
                    "name": "data-source-{}".format(id),
                    'id': id,
                    'data_format': data_format,
                    "input": {
                        "type": "auto",
                        "url": "http://stif.com/od.zip",
                        "frequency": {
                            "type": "daily",
                            "hour_of_day": 20
                        }
                    }
                }
            ]
        }
        return self.post('/contributors', json.dumps(post_data))

    def test_post_contrib_public_transport_with_data_format_invalid(self):
        for data_type in DATA_TYPE_VALUES:
            for data_format in set(DATA_FORMAT_VALUES) - set(DATA_FORMAT_BY_DATA_TYPE[data_type]):
                raw = self.__create_contributor(data_type, data_format)
                assert raw.status_code == 400, print(self.json_to_dict(raw))
                r = self.json_to_dict(raw)
                assert 'error' in r
                assert r[
                           'error'] == "data source format {format} is incompatible with contributor data_type {type}, possibles values are: '{values}'". \
                           format(format=data_format, type=data_type,
                                  values=','.join((DATA_FORMAT_BY_DATA_TYPE[data_type])))

    def test_post_contrib_public_transport_with_data_format_valid(self):
        for data_type in DATA_TYPE_VALUES:
            for data_format in DATA_FORMAT_BY_DATA_TYPE[data_type]:
                raw = self.__create_contributor(data_type, data_format)
                self.assert_sucessful_create(raw)

    def test_put_contrib_public_transport_with_data_format_invalid(self):
        for data_type in DATA_TYPE_VALUES:
            contributor_id = 'id-{}-{}'.format(data_type, DATA_FORMAT_BY_DATA_TYPE[data_type][0])
            contributor = self.init_contributor(contributor_id, data_source_id=contributor_id + '-ds',
                                                data_type=data_type,
                                                data_format=DATA_FORMAT_BY_DATA_TYPE[data_type][0], type='manual')
            for other_data_format in set(DATA_FORMAT_VALUES) - set(DATA_FORMAT_BY_DATA_TYPE[data_type]):
                contributor['data_sources'][0]['data_format'] = other_data_format
                raw = self.put('/contributors/{}'.format(contributor_id), self.dict_to_json(contributor))
                r = self.assert_failed_call(raw)
                assert 'error' in r
                assert r[
                           'error'] == "data source format {format} is incompatible with contributor data_type {type}, possibles values are: '{values}'". \
                           format(format=other_data_format, type=data_type,
                                  values=','.join(DATA_FORMAT_BY_DATA_TYPE[data_type]))

    def test_put_contrib_public_transport_with_data_format_valid(self):
        for data_type in DATA_TYPE_VALUES:
            contributor_id = 'id-{}-{}'.format(data_type, DATA_FORMAT_BY_DATA_TYPE[data_type][0])
            contributor = self.init_contributor(contributor_id, data_source_id=contributor_id + '-ds',
                                                data_type=data_type, type='manual',
                                                data_format=DATA_FORMAT_BY_DATA_TYPE[data_type][0])
            for other_data_format in DATA_FORMAT_BY_DATA_TYPE[data_type]:
                contributor['data_sources'][0]['data_format'] = other_data_format
                raw = self.put('/contributors/{}'.format(contributor_id), self.dict_to_json(contributor))
                self.assert_sucessful_call(raw)

    def test_put_data_type_with_wrong_data_source(self):
        contributor_id = 'id-{}-{}'.format(DATA_TYPE_GEOGRAPHIC, DATA_FORMAT_OSM_FILE)
        contributor = self.init_contributor(contributor_id, data_source_id=contributor_id + '-ds',
                                            data_type=DATA_TYPE_GEOGRAPHIC,
                                            data_format=DATA_FORMAT_OSM_FILE, type='manual')
        contributor['data_type'] = DATA_TYPE_PUBLIC_TRANSPORT
        raw = self.put('/contributors/{}'.format(contributor_id), self.dict_to_json(contributor))
        resp = self.assert_failed_call(raw)
        assert resp[
                   'error'] == "data source format {} is incompatible with contributor data_type {}, possibles values are: '{}'".format(
            DATA_FORMAT_OSM_FILE, DATA_TYPE_PUBLIC_TRANSPORT,
            ','.join(DATA_FORMAT_BY_DATA_TYPE[DATA_TYPE_PUBLIC_TRANSPORT])
        )
        assert resp['message'] == 'Invalid arguments'

    @pytest.mark.parametrize("data_format", [
        DATA_FORMAT_OSM_FILE,
        DATA_FORMAT_POLY_FILE
    ])
    def test_post_contributor_multi_data_sources_osm_poly(self, data_format):
        data_sources = [
            {'id': 'id1', 'name': 'id1', 'data_format': data_format},
            {'id': 'id2', 'name': 'id2', 'data_format': data_format},
        ]
        contributor = {
            'id': 'id_test',
            'name': 'id_test',
            'data_prefix': 'id_test',
            'data_type': DATA_TYPE_GEOGRAPHIC,
            'data_sources': data_sources,
        }
        raw = self.post('/contributors', self.dict_to_json(contributor))
        response = self.assert_failed_call(raw)
        assert response['error'] == 'contributor contains more than one {} data source'.format(data_format)
        assert response['message'] == 'Invalid arguments'

    @pytest.mark.parametrize("data_format", [
        DATA_FORMAT_OSM_FILE,
        DATA_FORMAT_POLY_FILE
    ])
    def test_put_contributor_multi_data_sources_osm_poly_with_new_one(self, data_format):
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
        data_source = {'id': 'id3', 'name': 'id3', 'data_format': data_format}
        contributor['data_sources'].append(data_source)
        raw = self.put('/contributors/id_test', self.dict_to_json(contributor))
        response = self.assert_failed_call(raw)
        assert response['error'] == 'contributor contains more than one {} data source'.format(data_format)
        assert response['message'] == 'Invalid arguments'

    @pytest.mark.parametrize("data_format", [
        DATA_FORMAT_OSM_FILE,
        DATA_FORMAT_POLY_FILE
    ])
    def test_put_contributor_multi_data_sources_osm_or_poly_update_one(self, data_format):
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
        data_source = {'id': 'id1', 'name': 'id1-updated', 'data_format': data_format}
        contributor['data_sources'][0] = data_source
        raw = self.put('/contributors/id_test', self.dict_to_json(contributor))
        self.assert_sucessful_call(raw)

    def test_put_contributor_simple(self, contributor):
        update = {"name": "name_updated", "data_prefix": "data_prefix_updated", "data_type": DATA_TYPE_GEOGRAPHIC}
        expected = {'contributors': [{'data_sources': [], 'data_prefix': 'data_prefix_updated', 'name': 'name_updated',
                                      'processes': [],
                                      'data_type': DATA_TYPE_GEOGRAPHIC, 'id': 'id_test'}]}
        raw = self.put('/contributors/id_test', self.dict_to_json(update))
        assert self.assert_sucessful_call(raw) == expected
        contrib_dict = self.json_to_dict(self.get('/contributors/id_test'))
        assert contrib_dict == expected

    def test_put_contributor_id(self, contributor):
        contributor['id'] = 'changed'
        raw = self.put('/contributors/id_test', self.dict_to_json(contributor))
        self.assert_failed_call(raw)
        assert self.json_to_dict(raw) == {
            'error': 'the modification of the id is not possible',
            'message': 'Invalid arguments'
        }

    def test_put_invalid_contributor_preserve_existing_one(self, contributor):
        del contributor['name']
        raw = self.put('/contributors/{}'.format(contributor['id']), self.dict_to_json(contributor))
        self.assert_failed_call(raw)
        assert self.json_to_dict(raw) == {
            'error': {'name': ['Missing data for required field.']},
            'message': 'Invalid arguments'
        }
        raw = self.get('/contributors/{}'.format(contributor['id']))
        self.assert_sucessful_call(raw)

    def test_put_contributor_data_sources(self, init_http_download_server):
        self.init_contributor('cid', 'dsid', self.format_url(init_http_download_server.ip_addr, 'some_archive.zip'))
        contributor = self.get_contributor('cid')
        contributor['data_type'] = DATA_TYPE_GEOGRAPHIC
        contributor['data_sources'] = [
            {
                "id": 'dsid',
                "name": 'dsname_updated',
                "data_format": DATA_FORMAT_BANO_FILE,
                "input": {'type': 'manual'}
            },
            {
                "id": 'dsid_2',
                "name": 'dsname_2',
                "data_format": DATA_FORMAT_OSM_FILE,
                "input": {'type': 'manual'}
            },
        ]
        raw = self.put('/contributors/cid', self.dict_to_json(contributor))
        self.assert_sucessful_call(raw)
        contrib_dict = self.get_contributor('cid')
        ds_1 = contrib_dict['data_sources'][0]
        assert ds_1['id'] == 'dsid'
        assert ds_1['name'] == 'dsname_updated'
        assert ds_1['data_format'] == DATA_FORMAT_BANO_FILE
        assert ds_1['input']['type'] == 'manual'
        ds_2 = contrib_dict['data_sources'][1]
        assert ds_2['id'] == 'dsid_2'
        assert ds_2['name'] == 'dsname_2'
        assert ds_2['data_format'] == DATA_FORMAT_OSM_FILE
        assert ds_2['input']['type'] == 'manual'

    def test_put_contributor_processes(self, init_http_download_server):
        self.init_contributor('cid', 'dsid', self.format_url(init_http_download_server.ip_addr, 'some_archive.zip'))
        contributor = self.get_contributor('cid')
        contributor['processes'] = [
            {
                "id": 'p1',
                "sequence": 0,
                "type": 'HeadsignShortName',
                "data_source_ids": ['dsid']
            },
            {
                "id": 'p2',
                "sequence": 1,
                "type": 'GtfsAgencyFile',
                "data_source_ids": ['dsid'],
                "params": {'data': {'agency_name': 'my_agency'}}
            }
        ]
        raw = self.put('/contributors/cid', self.dict_to_json(contributor))
        self.assert_sucessful_call(raw)
        contrib_dict = self.get_contributor('cid')
        process_1 = contrib_dict['processes'][0]
        process_2 = contrib_dict['processes'][1]
        assert process_1['id'] == 'p1'
        assert process_1['sequence'] == 0
        assert process_1['type'] == 'HeadsignShortName'
        assert process_1['data_source_ids'] == ['dsid']
        assert process_2['id'] == 'p2'
        assert process_2['sequence'] == 1
        assert process_2['type'] == 'GtfsAgencyFile'
        assert process_2['data_source_ids'] == ['dsid']
        assert process_2['params'] == {'data': {'agency_name': 'my_agency'}}

    def test_post_and_put_contributor_processes_with_target_data_source_id(self, init_http_download_server):
        contrib_payload = {
            "id": "id_test",
            "name": "name_test",
            "data_prefix": "OIF",
            "processes": [
                {
                    "sequence": 0,
                    "data_source_ids": [],
                    "type": "ComputeExternalSettings",
                    "params": {
                        "target_data_source_id": "target_1",
                        "export_type": DATA_FORMAT_PT_EXTERNAL_SETTINGS,
                    }
                },
                {
                    "sequence": 1,
                    "data_source_ids": [],
                    "type": "ComputeExternalSettings",
                    "params": {
                        "target_data_source_id": "target_2",
                        "export_type": DATA_FORMAT_PT_EXTERNAL_SETTINGS,
                    }
                }
            ]
        }

        raw = self.post('/contributors', self.dict_to_json(contrib_payload))
        result = self.json_to_dict(raw)
        self.assert_sucessful_create(raw)

        data_sources = result['contributors'][0]['data_sources']

        assert data_sources[0]['id'] == 'target_1'
        assert data_sources[0]['name'] == 'target_1'
        assert data_sources[0]['data_format'] == DATA_FORMAT_PT_EXTERNAL_SETTINGS
        assert data_sources[0]['input']['type'] == INPUT_TYPE_COMPUTED

        assert data_sources[1]['id'] == 'target_2'
        assert data_sources[1]['name'] == 'target_2'
        assert data_sources[1]['data_format'] == DATA_FORMAT_PT_EXTERNAL_SETTINGS
        assert data_sources[1]['input']['type'] == INPUT_TYPE_COMPUTED

        # put a contributor with a computed data source
        contributor = result['contributors'][0]
        del contributor['processes'][1]

        raw = self.put('/contributors/id_test', self.dict_to_json(contributor))
        result = self.json_to_dict(raw)
        assert (len(result['contributors'][0]['data_sources']) == 1)

    def __assert_export_id_generated_computed_data_source(self, contributor):
        assert len(contributor['data_sources']) == 2
        assert all(data_source['data_format'] == DATA_FORMAT_OBITI for data_source in contributor['data_sources'])
        ds_input = next(data_source for data_source in contributor['data_sources'] if data_source['id'] == 'ds1')
        ds_output = next(
            data_source for data_source in contributor['data_sources'] if data_source['id'] == 'export_ds_id')
        assert ds_input['input']['type'] == 'auto'
        assert ds_input['export_data_source_id'] == 'export_ds_id'
        assert ds_output['input']['type'] == 'computed'

    def test_post_contributor_data_source_export_id(self):
        self.init_contributor('c1', 'ds1', 'http://my-url', data_format=DATA_FORMAT_OBITI, export_id='export_ds_id')
        contributor = self.get_contributor('c1')
        self.__assert_export_id_generated_computed_data_source(contributor)

    def test_put_contributor_data_source_export_id(self):
        self.init_contributor('c1', 'ds1', 'http://my-url', data_format=DATA_FORMAT_OBITI)
        contributor = self.get_contributor('c1')
        assert len(contributor['data_sources']) == 1
        contributor['data_sources'][0]['export_data_source_id'] = 'export_ds_id'
        self.put('/contributors/c1', self.dict_to_json(contributor))
        contributor = self.get_contributor('c1')
        self.__assert_export_id_generated_computed_data_source(contributor)

    def test_post_contributor_with_data_source_and_password_hidden(self):
        username = 'my_user'
        password = 'my_secret_password'
        self.init_contributor('cid', 'dsid', "http://some_url", options={
            'authent': {'username': username, 'password': password}
        })
        data_source = self.get_contributor('cid')['data_sources'][0]
        self.assert_data_source_has_username_and_password(data_source, username, password, Contributor)

    def test_put_contributor_with_data_source_and_password_hidden(self):
        username = 'my_user'
        password = 'my_secret_password'
        self.init_contributor('cid', 'dsid', "http://some_url", options={
            'authent': {'username': username, 'password': password}
        })
        # update contributor preserve password
        contributor = self.get_contributor('cid')
        contributor['name'] = 'new_name'
        self.put('/contributors/cid', self.dict_to_json(contributor))
        contributor_updated = self.get_contributor('cid')
        assert contributor_updated['name'] == 'new_name'
        data_source = contributor_updated['data_sources'][0]
        self.assert_data_source_has_username_and_password(data_source, username, password, Contributor)

        # update password
        data_source['input']['options']['authent']['password'] = 'new_password'
        self.put('/contributors/cid', self.dict_to_json(contributor_updated))
        contributor_updated_password = self.get_contributor('cid')
        data_source_with_new_password = contributor_updated_password['data_sources'][0]
        self.assert_data_source_has_username_and_password(data_source_with_new_password, username, 'new_password',
                                                          Contributor)

        # update username
        data_source_with_new_password['input']['options']['authent']['username'] = 'new_user'
        self.put('/contributors/cid', self.dict_to_json(contributor_updated_password))
        final_contributor = self.get_contributor('cid')
        assert not final_contributor['data_sources'][0]['input']['options']['authent']['password']
        with tartare.app.app_context():
            contributor = Contributor.get('cid')
            assert not contributor.data_sources[0].input.options.authent.password

    def test_delete_contributor_with_data_source_used_by_other_contributor(self, init_http_download_server):
        self.init_contributor('geo', 'ruspell_bano_file',
                              self.format_url(init_http_download_server.ip_addr, 'bano-75.csv', path='ruspell'))
        self.init_contributor('cid', 'dsid', self.format_url(init_http_download_server.ip_addr, 'some_archive.zip'))
        self.add_process_to_contributor({
            "id": "ruspell_id",
            "type": "Ruspell",
            "sequence": 1,
            "data_source_ids": [
                "dsid"
            ],
            "params": {
                "links": [
                    {
                        "contributor_id": "geo",
                        "data_source_id": "ruspell_bano_file"
                    }
                ]
            }
        }, 'cid')
        raw = self.delete('/contributors/geo')
        details = self.assert_failed_call(raw)
        assert details == {
            'error': 'unable to delete contributor geo because the following contributors are using one of its data sources: cid',
            'message': 'Invalid arguments'
        }

    def test_delete_contributor_with_data_source_used_by_other_new_contributor(self, init_http_download_server):
        self.init_contributor('config', 'config-file',
                              self.format_url(init_http_download_server.ip_addr, 'config.json',
                                              path='compute_directions'), data_format=DATA_FORMAT_DIRECTION_CONFIG)
        self.init_contributor('cid', 'dsid', self.format_url(init_http_download_server.ip_addr, 'some_archive.zip'))
        self.add_process_to_contributor({
            "id": "compute",
            "type": "ComputeDirections",
            "sequence": 1,
            "input_data_source_ids": [
                "dsid"
            ],
            'configuration_data_sources': [
                {'name': 'directions', 'ids': ['config-file']}
            ],
        }, 'cid')
        raw = self.delete('/contributors/config')
        details = self.assert_failed_call(raw)
        assert details == {
            'error': 'unable to delete contributor config because the following contributors are using one of its data sources: cid',
            'message': 'Invalid arguments'
        }

    def test_delete_contributor_with_data_source_used_by_coverage(self, init_http_download_server):
        self.init_contributor('cid', 'dsid', self.format_url(init_http_download_server.ip_addr, 'some_archive.zip'))
        self.init_contributor('cid2', 'dsid2', self.format_url(init_http_download_server.ip_addr, 'some_archive.zip'))
        self.init_coverage('covid', ['dsid', 'dsid2'])
        raw = self.delete('/contributors/cid')
        details = self.assert_failed_call(raw)
        assert details == {
            'error': 'unable to delete contributor cid because the following coverages are using one of its data sources: covid',
            'message': 'Invalid arguments'
        }

    def test_delete_contributor_remove_files(self, init_http_download_server):
        self.init_contributor('cid', 'dsid', self.format_url(init_http_download_server.ip_addr, 'some_archive.zip'),
                              export_id='export_id')
        self.contributor_export('cid')
        with tartare.app.app_context():
            assert tartare.mongo.db['fs.files'].find({}).count() == 1
            self.delete('/contributors/cid')
            assert tartare.mongo.db['fs.files'].find({}).count() == 0

    def test_delete_contributor_with_process_remove_files(self, init_http_download_server):
        self.init_contributor('cid', 'dsid', self.format_url(init_http_download_server.ip_addr, 'some_archive.zip'),
                              export_id='export_id')
        self.add_process_to_contributor({
            "sequence": 0,
            "data_source_ids": ['dsid'],
            "type": "GtfsAgencyFile",
            "params": {"data": {"agency_id": "foo"}}
        }, 'cid')
        self.contributor_export('cid')
        with tartare.app.app_context():
            assert tartare.mongo.db['fs.files'].find({}).count() == 2
            self.delete('/contributors/cid')
            assert tartare.mongo.db['fs.files'].find({}).count() == 0

    def test_get_data_source_of_unknown_contributor(self):
        raw = self.get('/contributors/unknown/data_sources/stillunknown')
        details = self.assert_failed_call(raw, 404)
        assert details['error'] == "contributor 'unknown' not found"

    def test_get_data_source_unknown_in_contributor(self, contributor):
        raw = self.get('/contributors/{}/data_sources/stillunknown'.format(contributor['id']))
        details = self.assert_failed_call(raw, 404)
        assert details['error'] == "data source 'stillunknown' not found for contributor '{}'".format(contributor['id'])
