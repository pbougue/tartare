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
from tests.utils import to_json


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


def test_add_coverage_returns_success(app):
    raw = app.post('/coverages', headers={'Content-Type':'application/json'}, data=json.dumps({"id": "id_test", "name":"name_test"}))
    assert raw.status_code == 201
    raw = app.get('/coverages')
    r = to_json(raw)

    assert len(r["coverages"]) == 1
    assert isinstance(r["coverages"], list)
    assert r["coverages"][0]["id"] == "id_test"
    assert r["coverages"][0]["name"] == "name_test"


def test_add_coverage_no_id(app):
    raw = app.post('/coverages', headers={'Content-Type':'application/json'}, data=json.dumps({"name":"name_test"}))
    assert raw.status_code == 400
    raw = app.get('/coverages')
    r = to_json(raw)
    assert len(r["coverages"]) == 0


def test_add_coverage_no_name(app):
    raw = app.post('/coverages', headers={'Content-Type':'application/json'}, data=json.dumps({"id": "id_test"}))
    assert raw.status_code == 400
    raw = app.get('/coverages')
    r = to_json(raw)
    assert len(r["coverages"]) == 0


def test_delete_coverage_returns_success(app):
    raw = app.get('/coverages/id_test')
    assert raw.status_code == 404

    raw = app.post('/coverages', headers={'Content-Type':'application/json'}, data=json.dumps({"id": "id_test", "name":"name_test"}))
    assert raw.status_code == 201
    raw = app.delete('/coverages/id_test')
    assert raw.status_code == 204
    raw = app.get('/coverages/id_test')
    assert raw.status_code == 404

    raw = app.post('/coverages', headers={'Content-Type':'application/json'}, data=json.dumps({"id": "id_test2", "name":"name_test2"}))
    assert raw.status_code == 201
    raw = app.get('/coverages')
    r = to_json(raw)
    assert len(r["coverages"]) == 1
