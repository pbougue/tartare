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

def test_post_ds_one_data_source_without_id(app):
    '''
    using /data_sources endpoint
    '''
    post_contrib = {"id": "id_test", "name":"name_test", "data_prefix":"AAA"}
    raw = post(app, '/contributors', json.dumps(post_contrib))
    assert raw.status_code == 201, print(to_json(raw))
    post_ds = {"name":"data_source_name", "data_prefix": "STF",
               "input": [{"key": "type", "value": "url"},
                         {"key": "url", "value": "http://stif.com/od.zip"}]}
    raw = post(app, '/contributors/id_test/data_sources', json.dumps(post_ds))
    assert raw.status_code == 201, print(to_json(raw))

    raw = app.get('/contributors/id_test/data_sources')
    r = to_json(raw)
    assert raw.status_code == 200, print(r)
    assert len(r["data_sources"]) == 1

def test_post_contrib_one_data_source_without_id(app):
    '''
    using /contributors endpoint
    '''
    post_data = {"id": "id_test", "name":"name_test", "data_prefix":"AAA"}
    post_data["data_sources"] = []
    post_data["data_sources"].append({"name": "data_source_name", "data_prefix": "STF",
                                      "input": [{"key": "type", "value": "url"},
                                                {"key": "url", "value": "http://stif.com/od.zip"}]})
    raw = post(app, '/contributors', json.dumps(post_data))
    assert raw.status_code == 201, print(to_json(raw))
    raw = app.get('/contributors/id_test/')
    r = to_json(raw)
    print(r)
    assert raw.status_code == 200, print(r)
    assert len(r["contributors"][0]["data_sources"]) == 1


def test_post_ds_one_data_source_with_id(app):
    '''
    using /data_sources endpoint
    '''
    post_contrib = {"id": "id_test", "name":"name_test", "data_prefix":"AAA"}
    raw = post(app, '/contributors', json.dumps(post_contrib))
    assert raw.status_code == 201, print(to_json(raw))
    post_ds = {"id": "data_source_id", "name": "data_source_name",
               "data_prefix": "STF", "input": [{"key": "type", "value": "url"},
                                               {"key": "url", "value": "http://stif.com/od.zip"}]}
    raw = post(app, '/contributors/id_test/data_sources', json.dumps(post_ds))
    assert raw.status_code == 201, print(to_json(raw))

    raw = app.get('/contributors/id_test/data_sources')
    r = to_json(raw)
    assert raw.status_code == 200, print(r)
    assert len(r["data_sources"]) == 1

def test_post_contrib_one_data_source_with_id(app):
    '''
    using /contributors endpoint
    '''
    post_data = {"id": "id_test", "name": "name_test", "data_prefix": "AAA"}
    post_data["data_sources"] = []
    post_data["data_sources"].append({"id": "data_source_id", "name":"data_source_name",
                                      "data_prefix": "STF",
                                      "input": [{"key": "type", "value": "url"},
                                                {"key": "url", "value": "http://stif.com/od.zip"}]})
    raw = post(app, '/contributors', json.dumps(post_data))
    assert raw.status_code == 201, print(to_json(raw))
    raw = app.get('/contributors/id_test/')
    r = to_json(raw)
    assert raw.status_code == 200, print(r)
    assert len(r["contributors"][0]["data_sources"]) == 1


def test_post_ds_one_data_source_with_data_format(app):
    '''
    using /data_sources endpoint
    '''
    post_contrib = {"id": "id_test", "name":"name_test", "data_prefix":"AAA"}
    raw = post(app, '/contributors', json.dumps(post_contrib))
    assert raw.status_code == 201, print(to_json(raw))
    post_ds = {"name":"data_source_name", "data_format": "Neptune",
               "input": [{"key": "type", "value": "url"},
                         {"key": "url", "value": "http://stif.com/od.zip"}]}
    raw = post(app, '/contributors/id_test/data_sources', json.dumps(post_ds))
    assert raw.status_code == 201, print(to_json(raw))

    raw = app.get('/contributors/id_test/data_sources')
    r = to_json(raw)
    assert raw.status_code == 200, print(r)
    assert len(r["data_sources"]) == 1
    assert r["data_sources"][0]["data_format"] == "Neptune"
    assert r["data_sources"][0]["data_prefix"] is None
    assert r["data_sources"][0]["input"][0]["key"] == "type"
    assert r["data_sources"][0]["input"][0]["value"] == "url"
    assert r["data_sources"][0]["input"][1]["key"] == "url"
    assert r["data_sources"][0]["input"][1]["value"] == "http://stif.com/od.zip"

def test_post_contrib_one_data_source_with_data_format(app):
    '''
    using /contributors endpoint
    '''
    post_data = {"id": "id_test", "name":"name_test", "data_prefix":"AAA"}
    post_data["data_sources"] = []
    post_data["data_sources"].append({"name":"data_source_name", "data_format": "Neptune",
                                      "data_prefix": "STF",
                                      "input": [{"key": "type", "value": "url"},
                                                {"key": "url", "value": "http://stif.com/od.zip"}]})
    raw = post(app, '/contributors', json.dumps(post_data))
    assert raw.status_code == 201, print(to_json(raw))
    raw = app.get('/contributors/id_test/')
    r = to_json(raw)
    assert raw.status_code == 200, print(r)
    assert len(r["contributors"][0]["data_sources"]) == 1
    assert r["contributors"][0]["data_sources"][0]["data_format"] == "Neptune"
    assert r["contributors"][0]["data_sources"][0]["data_prefix"] == "STF"
    assert r["contributors"][0]["data_sources"][0]["input"][0]["key"] == "type"
    assert r["contributors"][0]["data_sources"][0]["input"][0]["value"] == "url"
    assert r["contributors"][0]["data_sources"][0]["input"][1]["key"] == "url"
    assert r["contributors"][0]["data_sources"][0]["input"][1]["value"] == "http://stif.com/od.zip"


def test_post_ds_two_data_source(app):
    '''
    using /data_sources endpoint
    '''
    post_contrib = {"id": "id_test", "name":"name_test", "data_prefix":"AAA"}
    raw = post(app, '/contributors', json.dumps(post_contrib))
    assert raw.status_code == 201, print(to_json(raw))
    post_ds = {"name":"data_source_name1", "data_prefix": "STF",
               "input": [{"key": "type", "value": "url"},
                         {"key": "url", "value": "http://stif.com/od.zip"}]}
    raw = post(app, '/contributors/id_test/data_sources', json.dumps(post_ds))
    assert raw.status_code == 201, print(to_json(raw))
    post_ds = {"name": "data_source_name2", "data_prefix": "STF",
               "input": [{"key": "type", "value": "url"},
                         {"key": "url", "value": "http://stof.com/od.zip"}]}
    raw = post(app, '/contributors/id_test/data_sources', json.dumps(post_ds))
    assert raw.status_code == 201, print(to_json(raw))

    raw = app.get('/contributors/id_test/data_sources')
    r = to_json(raw)
    assert raw.status_code == 200, print(r)
    assert len(r["data_sources"]) == 2
    assert r["data_sources"][0]["id"] != r["data_sources"][1]["id"]

def test_post_ds_duplicate_two_data_source(app):
    '''
    using /data_sources endpoint
    '''
    post_contrib = {"id": "id_test", "name":"name_test", "data_prefix":"AAA"}
    raw = post(app, '/contributors', json.dumps(post_contrib))
    assert raw.status_code == 201, print(to_json(raw))
    post_ds = {"id": "dupplicate_id", "name":"data_source_name1"}
    raw = post(app, '/contributors/id_test/data_sources', json.dumps(post_ds))
    assert raw.status_code == 201, print(to_json(raw))
    post_ds = {"id": "dupplicate_id", "name": "data_source_name2"}
    raw = post(app, '/contributors/id_test/data_sources', json.dumps(post_ds))
    payload = to_json(raw)
    assert raw.status_code == 409, print(payload)
    assert payload['error'] == "Duplicate data_source id 'dupplicate_id'"

def test_post_contrib_two_data_source(app):
    '''
    using /contributors endpoint
    '''
    post_data = {"id": "id_test", "name":"name_test", "data_prefix":"AAA"}
    post_data["data_sources"] = []
    post_data["data_sources"].append({"name":"data_source_name",
                                      "data_prefix": "STF",
                                      "input": [{"key": "type", "value": "url"},
                                                {"key": "url", "value": "http://stif.com/od.zip"}]})
    post_data["data_sources"].append({"name": "data_source_name2", "data_prefix": "STG",
                                      "input": [{"key": "type", "value": "url"},
                                                {"key": "url", "value": "http://stof.com/od.zip"}]})
    raw = post(app, '/contributors', json.dumps(post_data))
    assert raw.status_code == 201
    raw = app.get('/contributors/id_test/')
    r = to_json(raw)
    assert raw.status_code == 200, print(r)
    assert len(r["contributors"][0]["data_sources"]) == 2
    assert r["contributors"][0]["data_sources"][0]["id"] != r["contributors"][0]["data_sources"][1]["id"]


def test_patch_ds_data_source_with_full_contributor(app):
    '''
    using /data_sources endpoint
    '''
    post_contrib = {"id": "id_test", "name":"name_test", "data_prefix":"AAA"}
    raw = post(app, '/contributors', json.dumps(post_contrib))
    assert raw.status_code == 201
    post_ds = {"id": "ds_id", "name":"data_source_name",
               "data_prefix": "STF",
               "input": [{"key": "type", "value": "url"},
                         {"key": "url", "value": "http://stif.com/od.zip"}]}
    raw = post(app, '/contributors/id_test/data_sources', json.dumps(post_ds))
    r = to_json(raw)
    assert raw.status_code == 201, print(r)
    r["data_sources"][0]["name"] = "name_modified"
    print("patching data with ", json.dumps(r["data_sources"][0]))
    raw = patch(app, '/contributors/id_test/data_sources/ds_id', json.dumps(r["data_sources"][0]))
    r = to_json(raw)
    assert raw.status_code == 200, print(r)
    assert len(r["data_sources"]) == 1
    patched_data_source = r["data_sources"][0]
    assert patched_data_source["name"] == "name_modified"

def test_patch_contrib_data_source_with_full_contributor(app):
    '''
    using /contributors endpoint
    '''
    post_data = {"id": "id_test", "name":"name_test", "data_prefix":"AAA"}
    post_data["data_sources"] = []
    post_data["data_sources"].append({"name":"data_source_name", "data_prefix": "STF",
                                      "input": [{"key": "type", "value": "url"},
                                                {"key": "url", "value": "http://stif.com/od.zip"}]})
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


def test_patch_ds_data_source_name_only(app):
    '''
    using /data_sources endpoint
    '''
    post_contrib = {"id": "id_test", "name":"name_test", "data_prefix":"AAA"}
    raw = post(app, '/contributors', json.dumps(post_contrib))
    assert raw.status_code == 201
    post_ds = {"id": "ds_id", "name":"data_source_name", "data_format":"Neptune", "data_prefix": "STF",
               "input": [{"key": "type", "value": "url"},
                         {"key": "url", "value": "http://stif.com/od.zip"}]}
    raw = post(app, '/contributors/id_test/data_sources', json.dumps(post_ds))
    r = to_json(raw)
    assert raw.status_code == 201, print(r)
    modif_ds = {"id": "ds_id", "name":"name_modified"}
    raw = patch(app, '/contributors/id_test/data_sources/ds_id', json.dumps(modif_ds))
    r = to_json(raw)
    assert raw.status_code == 200, print(r)
    assert len(r["data_sources"]) == 1
    patched_data_source = r["data_sources"][0]
    assert patched_data_source["name"] == "name_modified"
    assert patched_data_source["data_format"] == "Neptune"

def test_patch_contrib_data_source_only(app):
    '''
    using /contributors endpoint
    '''
    post_data = {"id": "id_test", "name":"name_test", "data_prefix":"AAA"}
    post_data["data_sources"] = []
    post_data["data_sources"].append({"name":"data_source_name", "data_format":"Neptune", "data_prefix": "STF",
                                      "input": [{"key": "type", "value": "url"},
                                                {"key": "url", "value": "http://stif.com/od.zip"}]})
    raw = post(app, '/contributors', json.dumps(post_data))
    r = to_json(raw)
    assert raw.status_code == 201, print(r)
    new_data_source = {}
    new_data_source["id"] = r["contributors"][0]["data_sources"][0]["id"]
    new_data_source["name"] = "name_modified"
    new_data_source["data_prefix"] = "LOL"
    new_data_source["input"] = [
        {"key": "type", "value": "existing_version"},
        {"key": "v", "value": "-2"}
    ]
    r["contributors"][0]["data_sources"][0] = new_data_source
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
    assert patched_data_source["data_prefix"] == "LOL"
    assert patched_data_source["input"][0]["key"] == "type"
    assert patched_data_source["input"][0]["value"] == "existing_version"
    assert patched_data_source["input"][1]["key"] == "v"
    assert patched_data_source["input"][1]["value"] == "-2"


def test_patch_ds_one_data_source_name_of_two_and_add_one(app):
    '''
    using /data_sources endpoint
    '''
    post_contrib = {"id": "id_test", "name":"name_test", "data_prefix":"AAA"}
    raw = post(app, '/contributors', json.dumps(post_contrib))
    assert raw.status_code == 201
    post_ds = {"id": "ds1_id", "name":"data_source_name1", "data_format":"Neptune", "data_prefix": "STF",
               "input": [{"key": "type", "value": "url"},
                         {"key": "url", "value": "http://stif.com/od.zip"}]}
    raw = post(app, '/contributors/id_test/data_sources', json.dumps(post_ds))
    r = to_json(raw)
    assert raw.status_code == 201, print(r)
    post_ds = {"id": "ds2_id", "name":"data_source_name2", "data_format":"Neptune", "data_prefix": "STF",
               "input": [{"key": "type", "value": "url"},
                         {"key": "url", "value": "http://stif.com/od.zip"}]}
    raw = post(app, '/contributors/id_test/data_sources', json.dumps(post_ds))
    r = to_json(raw)
    assert raw.status_code == 201, print(r)
    modif_ds = {"name": "name_modified", "data_prefix": "STF",
                "input": [{"key": "type", "value": "url"},
                          {"key": "url", "value": "http://stif.com/od.zip"}]
                }
    raw = patch(app, '/contributors/id_test/data_sources/ds2_id', json.dumps(modif_ds))
    r = to_json(raw)
    print(r)
    assert raw.status_code == 200, print(r)
    post_ds = {"id": "ds3_id", "name":"data_source_name3", "data_prefix": "STF",
               "input": [{"key": "type", "value": "url"},
                         {"key": "url", "value": "http://stif.com/od.zip"}]}
    raw = post(app, '/contributors/id_test/data_sources', json.dumps(post_ds))
    r = to_json(raw)
    assert raw.status_code == 201, print(r)

    raw = app.get('/contributors/id_test/data_sources')
    r = to_json(raw)
    assert raw.status_code == 200, print(r)
    assert len(r["data_sources"]) == 3
    patched_data_sources = r["data_sources"]
    assert patched_data_sources[0]["data_format"] == "Neptune"
    assert patched_data_sources[1]["data_format"] == "Neptune"
    assert patched_data_sources[2]["data_format"] == "gtfs"
    assert patched_data_sources[0]["name"] == "data_source_name1"
    assert patched_data_sources[1]["name"] == "name_modified"
    assert patched_data_sources[2]["name"] == "data_source_name3"

def test_patch_contrib_one_data_source_name_of_two_and_add_one(app):
    '''
    using /contributors endpoint
    '''
    post_data = {"id": "id_test", "name":"name_test", "data_prefix":"AAA"}
    post_data["data_sources"] = []
    post_data["data_sources"].append({"name":"data_source_name", "data_format":"Neptune", "data_prefix": "STF",
                                      "input": [{"key": "type", "value": "url"},
                                                {"key": "url", "value": "http://stif.com/od.zip"}]})
    post_data["data_sources"].append({"name":"data_source_2", "data_format":"Neptune", "data_prefix": "LOL",
                                      "input": [{"key": "type", "value": "url"},
                                                {"key": "url", "value": "http://stif.com/od.zip"}]})
    raw = post(app, '/contributors', json.dumps(post_data))
    r = to_json(raw)
    assert raw.status_code == 201, print(r)
    new_data_source = {}
    new_data_source["id"] = r["contributors"][0]["data_sources"][1]["id"]
    new_data_source["name"] = "name_modified"
    new_data_source["input"] = [
        {"key": "type", "value": "existing_version"},
        {"key": "v", "value": "-2"}
    ]
    r["contributors"][0]["data_sources"][0] = new_data_source
    data_source_list = {}
    data_source_list["data_sources"] = [new_data_source, {"name": "data_source_3",
                                                          "input": [{"key": "type", "value": "url"},
                                                                    {"key": "url", "value": "http://stif.com/od.zip"}]}]
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


def test_post_ds_one_data_source_without_input(app):
    '''
    using /data_sources endpoint
    '''
    post_contrib = {"id": "id_test", "name":"name_test", "data_prefix": "AAA"}
    raw = post(app, '/contributors', json.dumps(post_contrib))
    assert raw.status_code == 201, print(to_json(raw))
    post_ds = {"name": "data_source_name"}
    raw = post(app, '/contributors/id_test/data_sources', json.dumps(post_ds))
    r = to_json(raw)
    assert 'error' in r
    assert raw.status_code == 400, print(to_json(raw))

    raw = app.get('/contributors/id_test/data_sources')
    r = to_json(raw)
    assert raw.status_code == 200, print(r)
    assert len(r["data_sources"]) == 0