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


def test_post_ds_one_data_source_without_id(app, contributor):
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
    raw = post(app, '/contributors/id_test/data_sources', json.dumps(post_ds))
    assert raw.status_code == 201, print(to_json(raw))

    raw = app.get('/contributors/id_test/data_sources')
    r = to_json(raw)
    assert raw.status_code == 200, print(r)
    assert len(r["data_sources"]) == 1


def test_post_ds_one_data_source_with_id(app, contributor):
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
    raw = post(app, '/contributors/id_test/data_sources', json.dumps(post_ds))
    assert raw.status_code == 201, print(to_json(raw))

    raw = app.get('/contributors/id_test/data_sources')
    r = to_json(raw)
    assert raw.status_code == 200, print(r)
    assert len(r["data_sources"]) == 1


def test_post_ds_one_data_source_with_data_format(app, contributor):
    """
    using /data_sources endpoint
    """
    post_ds = {
        "name": "data_source_name",
        "data_format": "Neptune",
        "input": {
            "type": "url",
            "url": "http://stif.com/od.zip"
        }
    }
    raw = post(app, '/contributors/id_test/data_sources', json.dumps(post_ds))
    assert raw.status_code == 201, print(to_json(raw))

    raw = app.get('/contributors/id_test/data_sources')
    r = to_json(raw)
    assert raw.status_code == 200, print(r)
    assert len(r["data_sources"]) == 1
    assert r["data_sources"][0]["data_format"] == "Neptune"
    assert r["data_sources"][0]["input"]["type"] == "url"
    assert r["data_sources"][0]["input"]["url"] == "http://stif.com/od.zip"


def test_post_ds_two_data_source(app, contributor):
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
    raw = post(app, '/contributors/id_test/data_sources', json.dumps(post_ds))
    assert raw.status_code == 201, print(to_json(raw))
    post_ds = {
        "name": "data_source_name2",
        "input": {
            "type": "url",
            "url": "http://stif.com/od.zip"
        }
    }
    raw = post(app, '/contributors/id_test/data_sources', json.dumps(post_ds))
    assert raw.status_code == 201, print(to_json(raw))

    raw = app.get('/contributors/id_test/data_sources')
    r = to_json(raw)
    assert raw.status_code == 200, print(r)
    assert len(r["data_sources"]) == 2
    assert r["data_sources"][0]["id"] != r["data_sources"][1]["id"]


def test_post_ds_duplicate_two_data_source(app, contributor):
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
    raw = post(app, '/contributors/id_test/data_sources', json.dumps(post_ds))
    assert raw.status_code == 201, print(to_json(raw))
    post_ds = {
        "id": "duplicate_id",
        "name": "data_source_name2",
        "input": {
            "type": "url",
            "url": "http://stif.com/od.zip"
        }
    }
    raw = post(app, '/contributors/id_test/data_sources', json.dumps(post_ds))
    payload = to_json(raw)
    assert raw.status_code == 409, print(payload)
    assert payload['error'] == "Duplicate data_source id 'duplicate_id'"


def test_patch_ds_data_source_with_full_contributor(app, data_source):
    """
    using /data_sources endpoint
    """
    data_source["name"] = "name_modified"
    print("patching data with ", json.dumps(data_source))
    raw = patch(app, '/contributors/id_test/data_sources/{}'.format(data_source["id"]), json.dumps(data_source))
    r = to_json(raw)
    assert raw.status_code == 200, print(r)
    assert len(r["data_sources"]) == 1
    patched_data_source = r["data_sources"][0]
    assert patched_data_source["name"] == "name_modified"


def test_patch_ds_data_source_name_only(app, data_source):
    """
    using /data_sources endpoint
    """
    modif_ds = {"name": "name_modified"}
    raw = patch(app, '/contributors/id_test/data_sources/{}'.format(data_source["id"]), json.dumps(modif_ds))
    r = to_json(raw)
    assert raw.status_code == 200, print(r)
    assert len(r["data_sources"]) == 1
    patched_data_source = r["data_sources"][0]
    assert patched_data_source["name"] == "name_modified"
    assert patched_data_source["data_format"] == "gtfs"


def test_patch_ds_one_data_source_name_of_two_and_add_one(app, contributor):
    """
    using /data_sources endpoint
    """
    post_ds = {
        "id": "ds1_id",
        "name": "data_source_name1",
        "data_format": "Neptune",
        "input": {
            "type": "url",
            "url": "http://stif.com/od.zip"
        }
    }
    raw = post(app, '/contributors/id_test/data_sources', json.dumps(post_ds))
    r = to_json(raw)
    assert raw.status_code == 201, print(r)
    post_ds = {
        "id": "ds2_id",
        "name": "data_source_name2",
        "data_format": "Neptune",
        "input": {
            "type": "url",
            "url": "http://stif.com/od.zip"
        }
    }
    raw = post(app, '/contributors/id_test/data_sources', json.dumps(post_ds))
    r = to_json(raw)
    assert raw.status_code == 201, print(r)
    modif_ds = {
        "name": "name_modified",
        "data_format": "Neptune",
        "input": {
            "type": "url",
            "url": "http://stif.com/od.zip"
        }
    }
    raw = patch(app, '/contributors/id_test/data_sources/ds2_id', json.dumps(modif_ds))
    r = to_json(raw)
    assert raw.status_code == 200, print(r)
    post_ds = {
        "id": "ds3_id",
        "name": "data_source_name3",
        "input": {
            "type": "url",
            "url": "http://stif.com/od.zip"
        }
    }
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


def test_post_ds_one_data_source_without_input(app, contributor):
    """
    using /data_sources endpoint
    """
    post_ds = {"name": "data_source_name"}
    raw = post(app, '/contributors/id_test/data_sources', json.dumps(post_ds))
    r = to_json(raw)
    assert 'error' in r
    assert raw.status_code == 400, print(to_json(raw))

    raw = app.get('/contributors/id_test/data_sources')
    r = to_json(raw)
    assert raw.status_code == 200, print(r)
    assert len(r["data_sources"]) == 0

def test_post_without_headers(app, contributor):
    """
    using /data_sources endpoint
    """
    post_ds = {
        "id": "ds1_id",
        "name": "data_source_name1",
        "data_format": "Neptune",
        "input": {
            "type": "url",
            "url": "http://stif.com/od.zip"
        }
    }
    raw = post(app, '/contributors/id_test/data_sources', json.dumps(post_ds), headers=None)
    assert raw.status_code == 415
    r = to_json(raw)
    assert r['error'] == 'request without data.'


def test_patch_without_headers(app, contributor):
    """
    using /data_sources endpoint
    """
    post_ds = {
        "id": "ds1_id",
        "name": "data_source_name1",
        "data_format": "Neptune",
        "input": {
            "type": "url",
            "url": "http://stif.com/od.zip"
        }
    }
    raw = patch(app, '/contributors/id_test/data_sources', json.dumps(post_ds), headers=None)
    assert raw.status_code == 415
    r = to_json(raw)
    assert r['error'] == 'request without data.'
