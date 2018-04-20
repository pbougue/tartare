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

from tartare.core.constants import DATA_TYPE_VALUES, DATA_FORMAT_BY_DATA_TYPE, DATA_FORMAT_VALUES, DATA_FORMAT_OSM_FILE, \
    DATA_TYPE_GEOGRAPHIC, DATA_FORMAT_BANO_FILE, DATA_FORMAT_POLY_FILE, DATA_TYPE_PUBLIC_TRANSPORT, \
    DATA_FORMAT_PT_EXTERNAL_SETTINGS, INPUT_TYPE_COMPUTED
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
        """
        using /contributors endpoint
        """
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
        """
        using /contributors endpoint
        """
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
        """
        using /contributors endpoint
        """
        post_data = {
            "id": "stif",
            "name": "stif",
            "data_prefix": "BBB",
            "data_sources": [
                {
                    "id": data_source["id"],
                    "name": "data_source_name",
                    "input": {
                        "type": "url",
                        "url": "http://stif.com/od.zip"
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

    def test_update_contributor_name(self):
        raw = self.post('/contributors', '{"id": "id_test", "name": "name_test", "data_prefix":"AAA"}')
        assert raw.status_code == 201

        raw = self.patch('/contributors/id_test', '{"name": "new_name_test"}')
        r = self.json_to_dict(raw)

        assert raw.status_code == 200
        assert r["contributors"][0]['id'] == "id_test"
        assert r["contributors"][0]['name'] == "new_name_test"

    def test_update_contributor_data_prefix(self):
        raw = self.post('/contributors', '{"id": "id_test", "name": "name_test", "data_prefix":"AAA"}')
        assert raw.status_code == 201

        raw = self.patch('/contributors/id_test', '{"data_prefix": "BBB"}')
        r = self.json_to_dict(raw)

        assert raw.status_code == 200
        assert r["contributors"][0]['id'] == "id_test"
        assert r["contributors"][0]['data_prefix'] == "BBB"

    def test_update_unknown_coverage(self):
        raw = self.patch('/contributors/unknown', '{"name": "new_name_test"}')
        r = self.json_to_dict(raw)
        assert 'message' in r
        assert raw.status_code == 404

    def test_update_contributor_id_impossible(self):
        """It should not be possible to update the id of an object"""
        raw = self.post('/contributors', '{"id": "id_test", "name": "name_test", "data_prefix":"AAA"}')
        assert raw.status_code == 201
        raw = self.patch('/contributors/id_test', '{"id": "bob"}')
        r = self.json_to_dict(raw)
        assert 'error' in r
        assert raw.status_code == 400

    def test_post_contrib_one_data_source_without_id(self):
        '''
        using /contributors endpoint
        '''
        post_data = {
            "id": "id_test",
            "name": "name_test",
            "data_prefix": "AAA",
            "data_sources": [
                {
                    "name": "data_source_name",
                    "input": {
                        "type": "url",
                        "url": "http://stif.com/od.zip"
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

    def test_post_contrib_one_data_source_with_id(self):
        """
        using /contributors endpoint
        """
        post_data = {
            "id": "id_test",
            "name": "name_test",
            "data_prefix": "AAA",
            "data_sources": [
                {
                    "id": "data_source_id",
                    "name": "data_source_name",
                    "input": {
                        "type": "url",
                        "url": "http://stif.com/od.zip"
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
        """
        using /contributors endpoint
        """
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
                        "type": "url",
                        "url": "http://stif.com/od.zip"
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

    def test_post_contrib_one_data_source_with_invalid_data_format(self):
        """
        using /contributors endpoint
        """
        post_data = {
            "id": "id_test",
            "name": "name_test",
            "data_prefix": "AAA",
            "data_sources": [
                {
                    "name": "data_source_name",
                    "data_format": "Neptune",
                    "input": {
                        "type": "url",
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
        """
        using /contributors endpoint
        """
        post_data = {
            "id": "id_test",
            "name": "name_test",
            "data_prefix": "AAA",
            "data_sources": [
                {
                    "name": "data_source_name",
                    "input": {
                        "type": "url",
                        "url": "http://stif.com/od.zip"
                    }
                },
                {
                    "name": "data_source_name2",
                    "input": {
                        "type": "url",
                        "url": "http://stif.com/od.zip"
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

    def test_patch_contrib_data_source_with_full_contributor(self):
        """
        using /contributors endpoint
        """
        post_data = {
            "id": "id_test",
            "name": "name_test",
            "data_prefix": "AAA",
            "data_sources": [
                {
                    "name": "data_source_name",
                    "input": {
                        "type": "url",
                        "url": "http://stif.com/od.zip"
                    }
                }
            ]
        }
        raw = self.post('/contributors', json.dumps(post_data))
        r = self.json_to_dict(raw)
        self.assert_sucessful_create(raw)
        r["contributors"][0]["data_sources"][0]["name"] = "name_modified"
        raw = self.patch('/contributors/id_test', json.dumps(r["contributors"][0]))
        r = self.json_to_dict(raw)
        self.assert_sucessful_call(raw)
        assert len(r["contributors"][0]["data_sources"]) == 1
        patched_data_source = r["contributors"][0]["data_sources"][0]
        assert patched_data_source["name"] == "name_modified"

    def test_patch_contrib_data_source_only(self, data_source):
        """
        using /contributors endpoint
        """
        new_data_source = {
            "id": data_source["id"],
            "name": "name_modified",
            "input": {
                "type": "url",
                "url": "http://bob.com",
            }
        }
        data_source_list = {}
        data_source_list["data_sources"] = [new_data_source]
        print("patching data with ", json.dumps(data_source_list))
        raw = self.patch('/contributors/id_test', json.dumps(data_source_list))
        r = self.json_to_dict(raw)
        self.assert_sucessful_call(raw)
        assert len(r["contributors"][0]["data_sources"]) == 1
        patched_data_source = r["contributors"][0]["data_sources"][0]
        assert patched_data_source["name"] == "name_modified"
        assert patched_data_source["data_format"] == "gtfs"
        assert patched_data_source["input"]["type"] == "url"
        assert patched_data_source["input"]["url"] == "http://bob.com"

    def test_patch_contrib_one_data_source_name_of_two_and_add_one(self):
        """
        using /contributors endpoint
        """
        post_data = {
            "id": "id_test",
            "name": "name_test",
            "data_prefix": "AAA",
            "data_sources": [
                {
                    "name": "data_source_name",
                    "data_format": "gtfs",
                    "input": {
                        "type": "url",
                        "url": "http://stif.com/od.zip"
                    }
                },
                {
                    "name": "data_source_2",
                    "data_format": "gtfs",
                    "service_id": "Google-1",
                    "input": {
                        "type": "url",
                        "url": "http://stif.com/od.zip"
                    }
                }
            ]
        }
        raw = self.post('/contributors', json.dumps(post_data))
        r = self.json_to_dict(raw)
        self.assert_sucessful_create(raw)
        new_data_source = {
            "id": r["contributors"][0]["data_sources"][1]["id"],
            "name": "name_modified",
            "service_id": None,
            "input": {
                "type": "manual",
            }
        }
        r["contributors"][0]["data_sources"][0] = new_data_source
        data_source_list = {}
        data_source_list["data_sources"] = [
            new_data_source,
            {
                "name": "data_source_3",
                "service_id": "Google-2",
                "input": {
                    "type": "computed",
                }
            }
        ]
        raw = self.patch('/contributors/id_test', json.dumps(data_source_list))
        r = self.json_to_dict(raw)
        self.assert_sucessful_call(raw)
        assert len(r["contributors"][0]["data_sources"]) == 3
        patched_data_sources = r["contributors"][0]["data_sources"]
        assert patched_data_sources[0]["data_format"] == "gtfs"
        assert patched_data_sources[1]["data_format"] == "gtfs"
        assert patched_data_sources[2]["data_format"] == "gtfs"
        assert patched_data_sources[0]["name"] == "data_source_name"
        assert patched_data_sources[1]["name"] == "name_modified"
        assert patched_data_sources[2]["name"] == "data_source_3"
        assert patched_data_sources[0]["service_id"] is None
        assert patched_data_sources[1]["service_id"] is None
        assert patched_data_sources[2]["service_id"] == "Google-2"

    def test_patch_contrib_preprocesses_without_id(self, contributor):
        """
        using /contributors endpoint
        """
        preprocesses = [
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
                "type": "ComputeDirections",
                "sequence": 2,
                "params": {
                    "tc_data": {"key": "data_sources.data_format", "value": "gtfs"}
                }
            }
        ]
        raw = self.get('/contributors')
        r = self.json_to_dict(raw)
        self.assert_sucessful_call(raw)
        assert len(r['contributors']) == 1
        r["contributors"][0]["preprocesses"] = preprocesses
        raw = self.patch('/contributors/id_test', json.dumps(r["contributors"][0]))
        r = self.json_to_dict(raw)
        self.assert_sucessful_call(raw)
        assert len(r["contributors"][0]["preprocesses"]) == 2
        types = [p.get("type") for p in r["contributors"][0]["preprocesses"]]
        excepted = [p.get("type") for p in preprocesses]
        assert types.sort() == excepted.sort()

    def test_patch_contrib_preprocesses_with_id(self, contributor):
        """
        using /contributors endpoint
        """
        preprocesses = [
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
        raw = self.get('/contributors')
        r = self.json_to_dict(raw)
        self.assert_sucessful_call(raw)
        assert len(r['contributors']) == 1
        r["contributors"][0]["preprocesses"] = preprocesses
        raw = self.patch('/contributors/id_test', json.dumps(r["contributors"][0]))
        r = self.json_to_dict(raw)
        self.assert_sucessful_call(raw)
        assert len(r["contributors"][0]["preprocesses"]) == 1
        assert r["contributors"][0]["preprocesses"][0]['id'] == preprocesses[0]["id"]
        assert r["contributors"][0]["preprocesses"][0]['type'] == preprocesses[0]["type"]

    def test_patch_contrib_preprocesses_type_unknown(self, contributor):
        """
        using /contributors endpoint
        """
        preprocesses = [
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
        raw = self.get('/contributors')
        r = self.json_to_dict(raw)
        self.assert_sucessful_call(raw)
        assert len(r['contributors']) == 1
        r["contributors"][0]["preprocesses"] = preprocesses
        raw = self.patch('/contributors/id_test', json.dumps(r["contributors"][0]))
        r = self.json_to_dict(raw)
        assert raw.status_code == 400, print(r)
        assert "contributors" not in r
        assert "message" in r
        assert "error" in r
        assert r["message"] == "Invalid arguments"
        assert r['error'] == "impossible to build preprocess BOB : " \
                             "modules within tartare.processes.contributor have no class BOB"

    def test_patch_contrib_preprocesses_gtfs_agency_file(self, contributor):
        """
        using /contributors endpoint
        """
        preprocesses = [
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
        raw = self.get('/contributors')
        r = self.json_to_dict(raw)
        self.assert_sucessful_call(raw)
        assert len(r['contributors']) == 1
        r["contributors"][0]["preprocesses"] = preprocesses
        raw = self.patch('/contributors/id_test', json.dumps(r["contributors"][0]))
        self.assert_sucessful_call(raw)
        assert len(r["contributors"][0]["preprocesses"]) == 1
        assert r["contributors"][0]["preprocesses"][0]["id"] == preprocesses[0]["id"]
        assert r["contributors"][0]["preprocesses"][0]["sequence"] == preprocesses[0]["sequence"]
        assert r["contributors"][0]["preprocesses"][0]["type"] == preprocesses[0]["type"]
        assert r["contributors"][0]["preprocesses"][0]["params"]["data"]["agency_id"] == \
               preprocesses[0]["params"]["data"]["agency_id"]
        assert r["contributors"][0]["preprocesses"][0]["params"]["data"]["agency_name"] == \
               preprocesses[0]["params"]["data"]["agency_name"]

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
            "preprocesses": [
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
                   'error'] == "data_source referenced by id '{missing_id}' in preprocess 'GtfsAgencyFile' not found in contributor".format(
            missing_id=missing_id)
        assert r['message'] == "Invalid arguments"

    @pytest.mark.parametrize("data_source_to_build_ids,preprocess_data_source_ids,missing_id", [
        ([], ['test'], 'test'),
        (['one-id'], ['another-id'], 'another-id'),
        (['one-id'], ['one-id', 'another-id'], 'another-id'),
        (['one-id', 'another-id'], ['third-id'], 'third-id'),
        (['one-id', 'another-id'], ['another-id', 'third-id'], 'third-id')
    ])
    def test_patch_contrib_integrity_fail_data_source_ids(self, data_source_to_build_ids, preprocess_data_source_ids,
                                                          missing_id):
        data_sources = []
        for data_source_to_build_id in data_source_to_build_ids:
            data_sources.append({
                "id": data_source_to_build_id,
                "name": data_source_to_build_id,
                "input": {
                    "type": "url",
                    "url": "http://stif.com/ods.zip"
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
        payload = {
            "preprocesses": [
                {
                    "type": "GtfsAgencyFile",
                    "data_source_ids": preprocess_data_source_ids
                }
            ]
        }
        raw = self.patch('/contributors/id_test', json.dumps(payload))
        assert raw.status_code == 400
        r = self.json_to_dict(raw)
        assert r['error'] == "data_source referenced by id '{missing_id}' in preprocess 'GtfsAgencyFile' " \
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
                        "type": "url",
                        "url": "http://stif.com/od.zip"
                    }
                }
            ]
        }
        return self.post('/contributors', json.dumps(post_data))

    def __patch_contributor(self, contributor_id, data_type, data_format):
        id = 'id-{}-{}'.format(data_type, data_format)
        post_data = {
            "data_sources": [
                {
                    "name": id,
                    'id': id,
                    'data_format': data_format
                }
            ]
        }
        return self.patch('/contributors/{}'.format(contributor_id), json.dumps(post_data))

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

    def test_patch_contrib_public_transport_with_data_format_invalid(self):
        for data_type in DATA_TYPE_VALUES:
            contributor_id = 'id-{}-{}'.format(data_type, DATA_FORMAT_BY_DATA_TYPE[data_type][0])
            raw = self.__create_contributor(data_type, DATA_FORMAT_BY_DATA_TYPE[data_type][0])
            self.assert_sucessful_create(raw)
            for other_data_format in set(DATA_FORMAT_VALUES) - set(DATA_FORMAT_BY_DATA_TYPE[data_type]):
                raw = self.__patch_contributor(contributor_id, data_type, other_data_format)
                self.assert_sucessful_call(raw, 400)
                r = self.json_to_dict(raw)
                assert 'error' in r
                assert r[
                           'error'] == "data source format {format} is incompatible with contributor data_type {type}, possibles values are: '{values}'". \
                           format(format=other_data_format, type=data_type,
                                  values=','.join(DATA_FORMAT_BY_DATA_TYPE[data_type]))

    def test_patch_contrib_public_transport_with_data_format_valid(self):
        for data_type in DATA_TYPE_VALUES:
            contributor_id = 'id-{}-{}'.format(data_type, DATA_FORMAT_BY_DATA_TYPE[data_type][0])
            raw = self.__create_contributor(data_type, DATA_FORMAT_BY_DATA_TYPE[data_type][0])
            self.assert_sucessful_create(raw)
            for other_data_format in DATA_FORMAT_BY_DATA_TYPE[data_type]:
                raw = self.__patch_contributor(contributor_id, data_type, other_data_format)
                self.assert_sucessful_call(raw)

    def test_patch_data_type_with_wrong_data_source(self):
        raw = self.__create_contributor(DATA_TYPE_GEOGRAPHIC, DATA_FORMAT_OSM_FILE)
        contributor_id = 'id-{}-{}'.format(DATA_TYPE_GEOGRAPHIC, DATA_FORMAT_OSM_FILE)
        self.assert_sucessful_create(raw)
        raw = self.patch('/contributors/{}'.format(contributor_id),
                         self.dict_to_json({"data_type": DATA_TYPE_PUBLIC_TRANSPORT}))
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
    def test_patch_contributor_multi_data_sources_osm_poly_with_new_one(self, data_format):
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
        raw = self.patch('/contributors/id_test', self.dict_to_json({'data_sources': [data_source]}))
        response = self.assert_failed_call(raw)
        assert response['error'] == 'contributor contains more than one {} data source'.format(data_format)
        assert response['message'] == 'Invalid arguments'

    @pytest.mark.parametrize("data_format", [
        DATA_FORMAT_OSM_FILE,
        DATA_FORMAT_POLY_FILE
    ])
    def test_patch_contributor_multi_data_sources_osm_or_poly_update_one(self, data_format):
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
        raw = self.patch('/contributors/id_test', self.dict_to_json({'data_sources': [data_source]}))
        self.assert_sucessful_call(raw)

    def test_put_contributor_simple(self, contributor):
        update = {"name": "name_updated", "data_prefix": "data_prefix_updated", "data_type": DATA_TYPE_GEOGRAPHIC}
        expected = {'contributors': [{'data_sources': [], 'data_prefix': 'data_prefix_updated', 'name': 'name_updated',
                                'preprocesses': [],
                                'data_type': DATA_TYPE_GEOGRAPHIC, 'id': 'id_test'}]}
        raw = self.put('/contributors/id_test', self.dict_to_json(update))
        assert self.assert_sucessful_call(raw) == expected
        contrib_dict = self.json_to_dict(self.get('/contributors/id_test'))
        assert contrib_dict == expected

    def test_put_contributor_data_sources(self, init_http_download_server):
        self.init_contributor('cid', 'dsid', self.format_url(init_http_download_server.ip_addr, 'some_archive.zip'))
        update = {"name": "cid_name", "data_prefix": "cid_prefix", "data_type": DATA_TYPE_GEOGRAPHIC,
                  'data_sources': [
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
                  }
        raw = self.put('/contributors/cid', self.dict_to_json(update))
        expected = {'contributors': [{'name': 'cid_name', 'data_sources': [
            {'name': 'dsname_updated', 'data_format': 'bano_file',
             'license': {'name': 'Private (unspecified)', 'url': ''},
             'input': {'type': 'manual', 'expected_file_name': None, 'url': None}, 'service_id': None, 'id': 'dsid',
             'updated_at': None, 'validity_period': None, 'status': 'never_fetched', 'fetch_started_at': None},
            {'name': 'dsname_2', 'data_format': 'osm_file', 'license': {'name': 'Private (unspecified)', 'url': ''},
             'input': {'type': 'manual', 'expected_file_name': None, 'url': None}, 'service_id': None,
             'id': 'dsid_2',
             'updated_at': None, 'validity_period': None, 'status': 'never_fetched', 'fetch_started_at': None}
        ],
                    'preprocesses': [],
                    'data_prefix': 'cid_prefix',
                    'id': 'cid',
                    'data_type': 'geographic'}]}
        assert self.assert_sucessful_call(raw) == expected
        contrib_dict = self.json_to_dict(self.get('/contributors/cid'))
        assert contrib_dict == expected

    def test_put_contributor_preprocesses(self, init_http_download_server):
        self.init_contributor('cid', 'dsid', self.format_url(init_http_download_server.ip_addr, 'some_archive.zip'))
        update = {"name": "cid_name", "data_prefix": "cid_prefix", "data_type": DATA_TYPE_PUBLIC_TRANSPORT,
                  'data_sources': [{'id': 'dsid', 'name': 'dsid',
                                    'input': {
                                        'type': 'url', 'url': self.format_url(init_http_download_server.ip_addr,
                                                                              'some_archive.zip')}}],
                  'preprocesses': [
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
                  }
        raw = self.put('/contributors/cid', self.dict_to_json(update))
        expected = {'contributors': [{'data_type': 'public_transport', 'data_prefix': 'cid_prefix', 'name': 'cid_name',
                                'preprocesses': [
                                    {'params': {}, 'sequence': 0, 'data_source_ids': ['dsid'], 'id': 'p1',
                                     'type': 'HeadsignShortName'},
                                    {'params': {'data': {'agency_name': 'my_agency'}}, 'sequence': 1,
                                     'data_source_ids': ['dsid'],
                                     'id': 'p2', 'type': 'GtfsAgencyFile'}
                                ], 'data_sources': [
                {'license': {'name': 'Private (unspecified)', 'url': ''}, 'service_id': None, 'name': 'dsid',
                 'input': {'expected_file_name': None, 'url': self.format_url(init_http_download_server.ip_addr,
                                                                              'some_archive.zip'), 'type': 'url'},
                 'id': 'dsid', 'data_format': 'gtfs', 'validity_period': None, 'fetch_started_at': None,
                 'status': 'never_fetched', 'updated_at': None}
            ],
                                'id': 'cid'}]}
        assert self.assert_sucessful_call(raw) == expected
        contrib_dict = self.json_to_dict(self.get('/contributors/cid'))
        assert contrib_dict == expected

    def test_post_and_put_contributor_preprocesses_with_target_data_source_id(self, init_http_download_server):
        contrib_payload = {
            "id": "id_test",
            "name": "name_test",
            "data_prefix": "OIF",
            "preprocesses": [
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
                    "sequence": 0,
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
        assert data_sources[1]['input']['type'] == INPUT_TYPE_COMPUTED

        assert data_sources[1]['id'] == 'target_2'
        assert data_sources[1]['name'] == 'target_2'
        assert data_sources[1]['data_format'] == DATA_FORMAT_PT_EXTERNAL_SETTINGS
        assert data_sources[1]['input']['type'] == INPUT_TYPE_COMPUTED

        # put a contributor with a computed data source
        contributor = result['contributors'][0]
        del contributor['preprocesses'][1]

        raw = self.put('/contributors/id_test', self.dict_to_json(contributor))
        result = self.json_to_dict(raw)
        assert(len(result['contributors'][0]['data_sources']) == 1)
