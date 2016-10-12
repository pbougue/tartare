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
    assert raw.status_code == 400
    raw = app.get('/contributors')
    r = to_json(raw)
    assert len(r["contributors"]) == 1


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
    assert r["contributor"]['id'] == "id_test"
    assert r["contributor"]['name'] == "new_name_test"


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
