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
from tests.utils import to_json


def post(app, url, params):
    """
    post on API with params as json
    """
    return app.post(url,
                    headers={'Content-Type': 'application/json'},
                    data=params)


def patch(app, url, params):
    """
    patch on API with params as json
    """
    return app.patch(url,
                     headers={'Content-Type': 'application/json'},
                     data=params)


def test_get_coverage_empty_success(app):
    raw = app.get('/coverages')
    assert raw.status_code == 200
    raw = app.get('/coverages/')
    assert raw.status_code == 200
    r = to_json(raw)
    assert len(r["coverages"]) == 0


def test_get_coverage_non_exist(app):
    raw = app.get('/coverages/id_test')
    assert raw.status_code == 404
    r = to_json(raw)
    assert 'message' in r


def test_add_coverage_returns_success(app):
    raw = post(app, '/coverages', '{"id": "id_test", "name":"name_test"}')
    assert raw.status_code == 201
    raw = app.get('/coverages')
    r = to_json(raw)

    assert len(r["coverages"]) == 1
    assert isinstance(r["coverages"], list)
    assert r["coverages"][0]["id"] == "id_test"
    assert r["coverages"][0]["name"] == "name_test"
    # the input_dir, output_dir and current_data_dir shouldn't be null
    for d in('input_dir', 'output_dir', 'current_data_dir'):
        assert r["coverages"][0]["technical_conf"].get(d)


def test_add_coverage_no_id(app):
    raw = post(app, '/coverages', '{"name": "name_test"}')
    r = to_json(raw)
    assert 'error' in r
    assert raw.status_code == 400
    raw = app.get('/coverages')
    r = to_json(raw)
    assert len(r["coverages"]) == 0


def test_add_coverage_no_name(app):
    raw = post(app, '/coverages', '{"id": "id_test"}')
    r = to_json(raw)
    assert 'error' in r
    assert raw.status_code == 400
    raw = app.get('/coverages')
    r = to_json(raw)
    assert len(r["coverages"]) == 0


def test_add_coverage_with_input_path(app):
    raw = post(app, '/coverages',
            '{"id": "id_test", "name": "name of the coverage", "technical_conf" : {"input_dir": "/srv/tartare/id_test/input"}}')
    assert raw.status_code == 201
    raw = app.get('/coverages')
    r = to_json(raw)
    assert len(r["coverages"]) == 1
    assert isinstance(r["coverages"], list)
    assert r["coverages"][0]["id"] == "id_test"
    assert r["coverages"][0]["name"] == "name of the coverage"
    assert r["coverages"][0]["technical_conf"]["input_dir"] == "/srv/tartare/id_test/input"


def test_patch_complex_coverage(app):
    raw = post(app, '/coverages',
               '''{"id": "id_test", "name": "name of the coverage",
                   "technical_conf": {"current_data_dir": "/srv/tartare/id_test/current_data_dir",
                                      "output_dir": "/srv/tartare/id_test/output_dir"}
               }''')
    assert raw.status_code == 201
    raw = app.get('/coverages')
    r = to_json(raw)
    assert len(r["coverages"]) == 1
    assert isinstance(r["coverages"], list)
    assert r["coverages"][0]["id"] == "id_test"
    assert r["coverages"][0]["name"] == "name of the coverage"
    # input dir has not been given but should have a default value
    conf = r["coverages"][0]["technical_conf"]
    assert conf["input_dir"] != ""
    assert conf["current_data_dir"] == "/srv/tartare/id_test/current_data_dir"
    assert conf["output_dir"] == "/srv/tartare/id_test/output_dir"

    raw = patch(app, '/coverages/id_test', '{"technical_conf": {"output_dir": "/srv/bob"}}')
    assert raw.status_code == 200
    r = to_json(raw)
    assert r["coverage"]["id"] == "id_test"
    assert r["coverage"]["name"] == "name of the coverage"
    updated_conf = r["coverage"]["technical_conf"]
    assert updated_conf["input_dir"] == conf["input_dir"]
    assert updated_conf["current_data_dir"] == conf['current_data_dir']
    assert updated_conf["output_dir"] == "/srv/bob"


def test_delete_coverage_returns_success(app):
    raw = app.get('/coverages/id_test')
    assert raw.status_code == 404

    raw = post(app, '/coverages', '{"id": "id_test", "name": "name_test"}')
    assert raw.status_code == 201
    raw = app.delete('/coverages/id_test')
    assert raw.status_code == 204
    raw = app.get('/coverages/id_test')
    assert raw.status_code == 404

    raw = post(app, '/coverages', '{"id": "id_test2", "name": "name_test2"}')
    assert raw.status_code == 201
    raw = app.get('/coverages')
    r = to_json(raw)
    assert len(r["coverages"]) == 1


def test_update_coverage_returns_success_status(app):
    raw = post(app, '/coverages', '{"id": "id_test", "name": "name_test"}')
    assert raw.status_code == 201

    raw = patch(app, '/coverages/id_test', '{"name": "new_name_test"}')
    r = to_json(raw)

    assert raw.status_code == 200
    assert r["coverage"]['id'] == "id_test"
    assert r["coverage"]['name'] == "new_name_test"


def test_update_unknown_coverage(app):
    raw = patch(app, '/coverages/unknown', '{"name": "new_name_test"}')
    r = to_json(raw)
    assert 'message' in r
    assert raw.status_code == 404


def test_update_id_impossible(app):
    """It should not be possible to update the id of an object"""
    raw = post(app, '/coverages', '{"id": "id_test", "name": "name_test"}')
    assert raw.status_code == 201
    raw = patch(app, '/coverages/id_test', '{"id": "bob"}')
    r = to_json(raw)
    assert 'error' in r
    assert raw.status_code == 400

def test_update_coverage_forbid_unkown_field(app):
    raw = post(app, '/coverages', '{"id": "id_test", "name": "name_test"}')
    assert raw.status_code == 201

    raw = patch(app, '/coverages/id_test', '{"name": "new_name_test", "foo": "bar"}')
    r = to_json(raw)

    assert raw.status_code == 400
    assert 'error' in r

def test_update_coverage_forbid_unkown_field_techconf(app):
    raw = post(app, '/coverages', '{"id": "id_test", "name": "name_test"}')
    assert raw.status_code == 201

    raw = patch(app, '/coverages/id_test', '{"name": "new_name_test", "technical_conf": {"foo": "bar"}}')
    r = to_json(raw)

    assert raw.status_code == 400
    assert 'error' in r
