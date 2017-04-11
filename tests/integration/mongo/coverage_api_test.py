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
    coverage = r["coverages"][0]
    assert coverage["id"] == "id_test"
    assert coverage["name"] == "name_test"
    #A default environment should have been created
    assert 'environments' in coverage
    assert 'production' in coverage['environments']
    assert coverage['environments']['production']['name'] == 'production'
    assert coverage['environments']['production']['tyr_url'] == 'http://tyr.prod/v0/coverage/id_test/'



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


def test_add_coverage_with_name(app):
    raw = post(app, '/coverages',
            '{"id": "id_test", "name": "name of the coverage"}')
    assert raw.status_code == 201
    raw = app.get('/coverages')
    r = to_json(raw)
    assert len(r["coverages"]) == 1
    assert isinstance(r["coverages"], list)
    assert r["coverages"][0]["id"] == "id_test"
    assert r["coverages"][0]["name"] == "name of the coverage"

def test_add_coverage_with_pre_env(app):
    raw = post(app, '/coverages',
            '''{"id": "id_test", "name": "name of the coverage",
                "environments" : {"preproduction": {"name": "pre", "tyr_url": "http://foo.bar/"}}}''')
    assert raw.status_code == 201
    raw = app.get('/coverages')
    r = to_json(raw)
    assert len(r["coverages"]) == 1
    assert isinstance(r["coverages"], list)
    coverage = r["coverages"][0]
    assert coverage["id"] == "id_test"
    assert coverage["name"] == "name of the coverage"
    assert 'environments' in coverage
    assert 'production' not in coverage['environments']
    assert 'preproduction' in coverage['environments']
    assert coverage['environments']['preproduction']['name'] == 'pre'
    assert coverage['environments']['preproduction']['tyr_url'] == 'http://foo.bar/'

def test_add_coverage_with_no_env(app):
    raw = post(app, '/coverages',
            '''{"id": "id_test", "name": "name of the coverage",
                "environments" : {"notvalidenv": {"name": "pre", "tyr_url": "http://foo.bar/"}}}''')
    print(raw.data)
    assert raw.status_code == 400
    r = to_json(raw)
    assert 'error' in r
    assert 'environments' in r['error']

def test_add_coverage_with_env_invalid_url(app):
    raw = post(app, '/coverages',
            '''{"id": "id_test", "name": "name of the coverage",
                "environments" : {"notvalidenv": {"name": "pre", "tyr_url": "foo"}}}''')
    print(raw.data)
    assert raw.status_code == 400
    r = to_json(raw)
    assert 'error' in r
    assert 'environments' in r['error']

def test_add_coverage_with_all_env(app):
    raw = post(app, '/coverages',
            '''{"id": "id_test", "name": "name of the coverage",
                "environments" : {
                    "preproduction": {"name": "pre", "tyr_url": "http://pre.bar/"},
                    "production": {"name": "prod", "tyr_url": "http://prod.bar/"},
                    "integration": {"name": "sim", "tyr_url": "http://int.bar/"}
                }}''')
    assert raw.status_code == 201
    raw = app.get('/coverages')
    r = to_json(raw)
    assert len(r["coverages"]) == 1
    assert isinstance(r["coverages"], list)
    coverage = r["coverages"][0]
    assert coverage["id"] == "id_test"
    assert coverage["name"] == "name of the coverage"
    assert 'environments' in coverage
    assert 'production'  in coverage['environments']
    assert 'preproduction' in coverage['environments']
    assert 'integration'  in coverage['environments']
    assert coverage['environments']['preproduction']['name'] == 'pre'
    assert coverage['environments']['preproduction']['tyr_url'] == 'http://pre.bar/'
    assert coverage['environments']['production']['name'] == 'prod'
    assert coverage['environments']['production']['tyr_url'] == 'http://prod.bar/'
    assert coverage['environments']['integration']['name'] == 'sim'
    assert coverage['environments']['integration']['tyr_url'] == 'http://int.bar/'


def test_patch_simple_coverage(app):
    raw = post(app, '/coverages',
               '''{"id": "id_test", "name": "name of the coverage"}''')
    assert raw.status_code == 201
    raw = app.get('/coverages')
    r = to_json(raw)
    assert len(r["coverages"]) == 1
    assert isinstance(r["coverages"], list)
    assert r["coverages"][0]["id"] == "id_test"
    assert r["coverages"][0]["name"] == "name of the coverage"

    raw = patch(app, '/coverages/id_test', '{"name": "new name"}')
    assert raw.status_code == 200
    r = to_json(raw)
    assert r["coverages"][0]["id"] == "id_test"
    assert r["coverages"][0]["name"] == "new name"


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
    assert r["coverages"][0]['id'] == "id_test"
    assert r["coverages"][0]['name'] == "new_name_test"


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

def test_update_coverage_forbid_unkown_environments_type(app):
    raw = post(app, '/coverages', '{"id": "id_test", "name": "name_test"}')
    assert raw.status_code == 201

    raw = patch(app, '/coverages/id_test', '{"name": "new_name_test", "environments": {"integration": {"name": "bar"}}}')
    assert raw.status_code == 200

    raw = patch(app, '/coverages/id_test', '{"name": "new_name_test", "environments": {"bar": {"name": "bar"}}}')
    assert raw.status_code == 400
    r = to_json(raw)
    assert 'error' in r

def test_update_coverage__env(app):
    raw = post(app, '/coverages', '{"id": "id_test", "name": "name_test"}')
    assert raw.status_code == 201

    raw = patch(app, '/coverages/id_test',
            '''{"environments" : {
                    "preproduction": {"name": "pre", "tyr_url": "http://pre.bar/"},
                    "production": null
                }}''')
    print(raw.data)
    assert raw.status_code == 200
    raw = app.get('/coverages')
    r = to_json(raw)
    assert len(r["coverages"]) == 1
    assert isinstance(r["coverages"], list)
    coverage = r["coverages"][0]
    assert coverage["id"] == "id_test"
    assert coverage["name"] == "name_test"
    assert 'environments' in coverage
    assert 'production' not in coverage['environments']
    assert 'preproduction' in coverage['environments']
    assert coverage['environments']['preproduction']['name'] == 'pre'
    assert coverage['environments']['preproduction']['tyr_url'] == 'http://pre.bar/'
