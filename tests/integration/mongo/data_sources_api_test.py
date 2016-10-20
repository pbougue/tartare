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


def test_post_contrib_no_data_source(app):
    raw = post(app, '/contributors', '{"id": "id_test", "name":"name_test", "data_prefix":"AAA"}')
    assert raw.status_code == 201
    raw = app.get('/contributors/id_test/')
    r = to_json(raw)
    assert raw.status_code == 200
    assert len(r["contributor"]["data_sources"]) == 0

def test_post_contrib_one_data_source(app):
    post_data = {"id": "id_test", "name":"name_test", "data_prefix":"AAA"}
    post_data["data_sources"] = []
    post_data["data_sources"].append({"id":"data_id", "name":"data_source_name"})
    raw = post(app, '/contributors', json.dumps(post_data))
    assert raw.status_code == 201
    raw = app.get('/contributors/id_test/')
    r = to_json(raw)
    assert raw.status_code == 200
    assert len(r["contributor"]["data_sources"]) == 1

def test_post_contrib_one_data_source_with_datasource(app):
    post_data = {"id": "id_test", "name":"name_test", "data_prefix":"AAA"}
    post_data["data_sources"] = []
    post_data["data_sources"].append({"id":"data_id", "name":"data_source_name", "data_format":"Neptune"})
    raw = post(app, '/contributors', json.dumps(post_data))
    assert raw.status_code == 201
    raw = app.get('/contributors/id_test/')
    r = to_json(raw)
    assert raw.status_code == 200
    assert len(r["contributor"]["data_sources"]) == 1
    assert r["contributor"]["data_sources"][0]["data_format"] == "Neptune"

def test_post_contrib_two_data_source(app):
    post_data = {"id": "id_test", "name":"name_test", "data_prefix":"AAA"}
    post_data["data_sources"] = []
    post_data["data_sources"].append({"id":"data_id", "name":"data_source_name"})
    post_data["data_sources"].append({"id":"data_id2", "name":"data_source_name2"})
    raw = post(app, '/contributors', json.dumps(post_data))
    assert raw.status_code == 201
    raw = app.get('/contributors/id_test/')
    r = to_json(raw)
    assert raw.status_code == 200
    assert len(r["contributor"]["data_sources"]) == 2


def test_patch_data_source(app):
    post_data = {"id": "id_test", "name":"name_test", "data_prefix":"AAA"}
    post_data["data_sources"] = []
    post_data["data_sources"].append({"id":"data_id", "name":"data_source_name"})
    raw = post(app, '/contributors', json.dumps(post_data))
    assert raw.status_code == 201
    raw = patch(app, '/contributors/id_test', '{"data_sources": [{"id": "data_id", "name": "name_modified"}]}')
    r = to_json(raw)
    assert raw.status_code == 200
    assert len(r["contributor"]["data_sources"]) == 1
    patched_data_source = r["contributor"]["data_sources"][0]
    assert patched_data_source["id"] == "data_id"
    assert patched_data_source["name"] == "name_modified"

def test_patch_data_source_datatype_unmodified(app):
    post_data = {"id": "id_test", "name":"name_test", "data_prefix":"AAA"}
    post_data["data_sources"] = []
    post_data["data_sources"].append({"id":"data_id", "name":"data_source_name", "data_format":"Neptune"})
    raw = post(app, '/contributors', json.dumps(post_data))
    assert raw.status_code == 201
    raw = patch(app, '/contributors/id_test', '{"data_sources": [{"id": "data_id", "name": "name_modified"}]}')
    r = to_json(raw)
    assert raw.status_code == 200
    assert len(r["contributor"]["data_sources"]) == 1
    patched_data_source = r["contributor"]["data_sources"][0]
    assert patched_data_source["id"] == "data_id"
    assert patched_data_source["name"] == "name_modified"
    assert patched_data_source["data_format"] == "Neptune"
