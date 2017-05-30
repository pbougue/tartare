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
from tests.utils import to_json, post, patch
import json


def test_get_contributors_empty_success(app):
    raw = app.get('/contributors')
    assert raw.status_code == 200
    raw = app.get('/contributors/')
    assert raw.status_code == 200
    r = to_json(raw)
    assert len(r["contributors"]) == 0


def test_get_contributors_non_exist(app):
    raw = app.get('/contributors/id_test')
    assert raw.status_code == 404
    r = to_json(raw)
    assert 'message' in r

def test_add_contributor_without_id(app):
    raw = post(app, '/contributors', '{"name":"whatever", "data_prefix":"any_prefix"}')
    assert raw.status_code == 400
    r = to_json(raw)
    assert 'error' in r
    assert r['error'] == "contributor id has to be specified"


def test_add_contributor_returns_success(app):
    raw = post(app, '/contributors', '{"id": "id_test", "name":"name_test", "data_prefix":"AAA"}')
    assert raw.status_code == 201
    raw = app.get('/contributors')
    r = to_json(raw)

    assert len(r["contributors"]) == 1
    assert isinstance(r["contributors"], list)
    assert r["contributors"][0]["id"] == "id_test"
    assert r["contributors"][0]["name"] == "name_test"
    assert r["contributors"][0]["data_prefix"] == "AAA"


def test_add_contributors_no_id(app):
    raw = post(app, '/contributors', '{"name": "name_test"}')
    r = to_json(raw)
    assert 'error' in r
    assert raw.status_code == 400
    raw = app.get('/contributors')
    r = to_json(raw)
    assert len(r["contributors"]) == 0


def test_add_coverage_no_name(app):
    raw = post(app, '/contributors', '{"id": "id_test"}')
    r = to_json(raw)
    assert 'error' in r
    assert raw.status_code == 400
    raw = app.get('/contributors')
    r = to_json(raw)
    assert len(r["contributors"]) == 0


def test_add_coverage_no_prefix(app):
    raw = post(app, '/contributors', '{"id": "id_test", "name":"name_test"}')
    r = to_json(raw)
    assert 'error' in r
    assert raw.status_code == 400
    raw = app.get('/contributors')
    r = to_json(raw)
    assert len(r["contributors"]) == 0


def test_add_contributors_unique_data_suffix_ok(app):
    raw = post(app, '/contributors', '{"id": "id_test1", "name":"name_test1", "data_prefix":"AAA"}')
    assert raw.status_code == 201
    raw = post(app, '/contributors', '{"id": "id_test2", "name":"name_test2", "data_prefix":"AAB"}')
    assert raw.status_code == 201
    raw = app.get('/contributors')
    r = to_json(raw)
    assert len(r["contributors"]) == 2


def test_add_contributors_unique_data_suffix_error(app):
    raw = post(app, '/contributors', '{"id": "id_test1", "name":"name_test1", "data_prefix":"AAA"}')
    assert raw.status_code == 201
    raw = post(app, '/contributors', '{"id": "id_test2", "name":"name_test2", "data_prefix":"AAA"}')
    assert raw.status_code == 409
    raw = app.get('/contributors')
    r = to_json(raw)
    assert len(r["contributors"]) == 1


def test_post_contrib_no_data_source(app):
    raw = post(app, '/contributors', '{"id": "id_test", "name":"name_test", "data_prefix":"AAA"}')
    assert raw.status_code == 201
    raw = app.get('/contributors/id_test/')
    r = to_json(raw)
    print(r)
    assert raw.status_code == 200
    assert len(r["contributors"][0]["data_sources"]) == 0


def test_delete_contributors_returns_success(app):
    raw = app.get('/contributors/id_test')
    assert raw.status_code == 404

    raw = post(app, '/contributors', '{"id": "id_test", "name": "name_test", "data_prefix":"AAA"}')
    assert raw.status_code == 201
    raw = app.delete('/contributors/id_test')
    assert raw.status_code == 204
    raw = app.get('/contributors/id_test')
    assert raw.status_code == 404

    raw = post(app, '/contributors', '{"id": "id_test2", "name": "name_test2", "data_prefix":"AAA"}')
    assert raw.status_code == 201
    raw = app.get('/contributors')
    r = to_json(raw)
    assert len(r["contributors"]) == 1


def test_update_contributor_name(app):
    raw = post(app, '/contributors', '{"id": "id_test", "name": "name_test", "data_prefix":"AAA"}')
    assert raw.status_code == 201

    raw = patch(app, '/contributors/id_test', '{"name": "new_name_test"}')
    r = to_json(raw)

    assert raw.status_code == 200
    assert r["contributors"][0]['id'] == "id_test"
    assert r["contributors"][0]['name'] == "new_name_test"


def test_update_contributor_data_prefix_error(app):
    raw = post(app, '/contributors', '{"id": "id_test", "name": "name_test", "data_prefix":"AAA"}')
    assert raw.status_code == 201

    raw = patch(app, '/contributors/id_test', '{"data_prefix": "AAB"}')
    r = to_json(raw)

    assert raw.status_code == 400


def test_update_unknown_coverage(app):
    raw = patch(app, '/contributors/unknown', '{"name": "new_name_test"}')
    r = to_json(raw)
    assert 'message' in r
    assert raw.status_code == 404


def test_update_contributor_id_impossible(app):
    """It should not be possible to update the id of an object"""
    raw = post(app, '/contributors', '{"id": "id_test", "name": "name_test", "data_prefix":"AAA"}')
    assert raw.status_code == 201
    raw = patch(app, '/contributors/id_test', '{"id": "bob"}')
    r = to_json(raw)
    assert 'error' in r
    assert raw.status_code == 400


def test_post_contrib_one_data_source_without_id(app):
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
    raw = post(app, '/contributors', json.dumps(post_data))
    assert raw.status_code == 201, print(to_json(raw))
    raw = app.get('/contributors/id_test/')
    r = to_json(raw)
    assert raw.status_code == 200, print(r)
    assert len(r["contributors"][0]["data_sources"]) == 1


def test_post_contrib_one_data_source_with_id(app):
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
    raw = post(app, '/contributors', json.dumps(post_data))
    assert raw.status_code == 201, print(to_json(raw))
    raw = app.get('/contributors/id_test/')
    r = to_json(raw)
    assert raw.status_code == 200, print(r)
    assert len(r["contributors"][0]["data_sources"]) == 1


def test_post_contrib_one_data_source_with_data_format(app):
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
    raw = post(app, '/contributors', json.dumps(post_data))
    assert raw.status_code == 201, print(to_json(raw))
    raw = app.get('/contributors/id_test/')
    r = to_json(raw)
    assert raw.status_code == 200, print(r)
    assert len(r["contributors"][0]["data_sources"]) == 1
    assert r["contributors"][0]["data_sources"][0]["data_format"] == "Neptune"
    assert r["contributors"][0]["data_sources"][0]["input"]["type"] == "url"
    assert r["contributors"][0]["data_sources"][0]["input"]["url"] == "http://stif.com/od.zip"


def test_post_contrib_two_data_source(app):
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
    raw = post(app, '/contributors', json.dumps(post_data))
    assert raw.status_code == 201
    raw = app.get('/contributors/id_test/')
    r = to_json(raw)
    assert raw.status_code == 200, print(r)
    assert len(r["contributors"][0]["data_sources"]) == 2
    assert r["contributors"][0]["data_sources"][0]["id"] != r["contributors"][0]["data_sources"][1]["id"]


def test_patch_contrib_data_source_with_full_contributor(app):
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
    raw = post(app, '/contributors', json.dumps(post_data))
    r = to_json(raw)
    assert raw.status_code == 201, print(r)
    r["contributors"][0]["data_sources"][0]["name"] = "name_modified"
    raw = patch(app, '/contributors/id_test', json.dumps(r["contributors"][0]))
    r = to_json(raw)
    assert raw.status_code == 200, print(r)
    assert len(r["contributors"][0]["data_sources"]) == 1
    patched_data_source = r["contributors"][0]["data_sources"][0]
    assert patched_data_source["name"] == "name_modified"


def test_patch_contrib_data_source_only(app, data_source):
    """
    using /contributors endpoint
    """
    new_data_source = {
        "id": data_source["id"],
        "name": "name_modified",
        "input": {
            "type": "existing_version",
            "v": "-2"
        }
    }
    data_source_list = {}
    data_source_list["data_sources"] = [new_data_source]
    print("patching data with ", json.dumps(data_source_list))
    raw = patch(app, '/contributors/id_test', json.dumps(data_source_list))
    r = to_json(raw)
    assert raw.status_code == 200, print(r)
    assert len(r["contributors"][0]["data_sources"]) == 1
    patched_data_source = r["contributors"][0]["data_sources"][0]
    assert patched_data_source["name"] == "name_modified"
    assert patched_data_source["data_format"] == "Neptune"
    assert patched_data_source["input"]["type"] == "existing_version"
    assert patched_data_source["input"]["v"] == "-2"


def test_patch_contrib_one_data_source_name_of_two_and_add_one(app):
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
            },
            {
                "name": "data_source_2",
                "data_format": "Neptune",
                "input": {
                    "type": "url",
                    "url": "http://stif.com/od.zip"
                }
            }
        ]
    }
    raw = post(app, '/contributors', json.dumps(post_data))
    r = to_json(raw)
    assert raw.status_code == 201, print(r)
    new_data_source = {
        "id": r["contributors"][0]["data_sources"][1]["id"],
        "name": "name_modified",
        "input": {
            "type": "existing_version",
            "v": "-2"
        }
    }
    r["contributors"][0]["data_sources"][0] = new_data_source
    data_source_list = {}
    data_source_list["data_sources"] = [
        new_data_source,
        {
            "name": "data_source_3",
            "input": {
                "type": "url",
                "url": "http://stif.com/od.zip"
            }
        }
    ]
    print("patching data with ", json.dumps(data_source_list))
    raw = patch(app, '/contributors/id_test', json.dumps(data_source_list))
    r = to_json(raw)
    assert raw.status_code == 200, print(r)
    assert len(r["contributors"][0]["data_sources"]) == 3
    patched_data_sources = r["contributors"][0]["data_sources"]
    assert patched_data_sources[0]["data_format"] == "Neptune"
    assert patched_data_sources[1]["data_format"] == "Neptune"
    assert patched_data_sources[2]["data_format"] == "gtfs"
    assert patched_data_sources[0]["name"] == "data_source_name"
    assert patched_data_sources[1]["name"] == "name_modified"
    assert patched_data_sources[2]["name"] == "data_source_3"
