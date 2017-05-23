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
from tests.utils import to_json, post, patch, delete
import json



def test_post_ds_one_data_source_without_id(app, contributor):
    '''
    using /preprocesses endpoint
    '''
    post_ps = {
        "type": "ruspell",
        "source_params": {
            "tc_data": {"key": "data_sources.id", "value": "datasource_stif"},
            "bano_data": {"key": "data_sources.id", "value": "bano_75"}
        }
    }
    raw = post(app, '/contributors/bob/preprocesses', json.dumps(post_ps))
    assert raw.status_code == 201, print(to_json(raw))

    raw = app.get('/contributors/bob/preprocesses')
    r = to_json(raw)
    assert raw.status_code == 200, print(r)
    assert len(r["preprocesses"]) == 1
    assert r["preprocesses"][0]["type"] == post_ps["type"]
    assert r["preprocesses"][0]["source_params"] == post_ps["source_params"]

    preprocess_id = r["preprocesses"][0]["id"]

    raw = app.get('/contributors/bob/preprocesses/{}'.format(preprocess_id))
    r = to_json(raw)
    assert raw.status_code == 200, print(r)
    assert len(r["preprocesses"]) == 1
    assert r["preprocesses"][0]["type"] == post_ps["type"]
    assert r["preprocesses"][0]["source_params"] == post_ps["source_params"]

    raw = app.get('/contributors/bob/preprocesses/toto')
    r = to_json(raw)
    assert raw.status_code == 404, print(r)


def test_post_contrib_one_data_source_with_id(app):
    '''
    using /contributors endpoint
    '''
    post_data = {"id": "id_test", "name":"name_test", "data_prefix":"AAA"}
    post_data["preprocesses"] = [{
        "id": "toto",
        "type": "ruspell",
        "source_params": {
            "tc_data": {"key": "data_sources_id", "value": "datasource_stif"},
            "bano_data": {"key": "data_sources_id", "value": "bano_75"}
        }
    }]
    raw = post(app, '/contributors', json.dumps(post_data))
    assert raw.status_code == 201, print(to_json(raw))
    raw = app.get('/contributors/id_test/')
    r = to_json(raw)
    assert raw.status_code == 200, print(r)
    assert len(r["contributors"][0]["preprocesses"]) == 1

def test_update_preprocess_with_id(app):
    '''
    using /contributors endpoint
    '''
    post_data = {"id": "id_test", "name":"name_test", "data_prefix":"AAA"}
    post_data["preprocesses"] = [{
        "id": "toto",
        "type": "ruspell",
        "source_params": {
            "tc_data": {"key": "data_sources_id", "value": "datasource_stif"},
            "bano_data": {"key": "data_sources_id", "value": "bano_75"}
        }
    }]
    raw = post(app, '/contributors', json.dumps(post_data))
    assert raw.status_code == 201, print(to_json(raw))
    raw = app.get('/contributors/id_test/')
    r = to_json(raw)
    assert raw.status_code == 200, print(r)
    assert len(r["contributors"][0]["preprocesses"]) == 1
    preprocess_id = r["contributors"][0]["preprocesses"][0]["id"]
    new_preprocess = {
        "type": "compute_directions",
        "source_params": {
            "tc_data": {"key": "data_sources.data_format", "value": "gtfs"}
        }
    }

    raw = patch(app, '/contributors/id_test/preprocesses/{}'.format(preprocess_id), json.dumps(new_preprocess))
    r = to_json(raw)
    assert raw.status_code == 200, print(r)
    assert len(r["preprocesses"]) == 1
    assert r["preprocesses"][0]["type"] == new_preprocess["type"]
    assert r["preprocesses"][0]["source_params"] == new_preprocess["source_params"]


def test_delete_preprocess(app):
    '''
    using /contributors endpoint
    '''
    post_data = {"id": "id_test", "name":"name_test", "data_prefix":"AAA"}
    post_data["preprocesses"] = [{
        "id": "toto",
        "type": "ruspell",
        "source_params": {
            "tc_data": {"key": "data_sources_id", "value": "datasource_stif"},
            "bano_data": {"key": "data_sources_id", "value": "bano_75"}
        }
    }]
    raw = post(app, '/contributors', json.dumps(post_data))
    r = to_json(raw)
    assert raw.status_code == 201, print(r)

    preprocess_id = r["contributors"][0]["preprocesses"][0]["id"]
    raw = delete(app, '/contributors/id_test/preprocesses/{}'.format(preprocess_id))
    assert raw.status_code == 204, print(to_json(raw))
