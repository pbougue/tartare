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
from tests.utils import to_json, post, delete
import json


def test_bad_coverage(app):
    raw = post(app, '/coverages/unknown/contributors',
               '''{"id": "bob"}''')
    r = to_json(raw)
    assert raw.status_code == 404
    assert r.get('error') == 'coverage unknown not found'


def test_missing_contributor_id(app, coverage):
    raw = post(app, '/coverages/jdr/contributors',
               '''{}''')
    r = to_json(raw)
    assert raw.status_code == 400
    assert r.get('error') == 'missing contributor_id attribute in request body'


def test_unknown_contributor(app, coverage):
    raw = post(app, '/coverages/jdr/contributors',
               '''{"id": "bob"}''')
    r = to_json(raw)
    assert raw.status_code == 404
    assert r.get('error') == 'contributor bob not found'


def test_add_contributor(app, coverage, contributor):
    raw = post(app, '/coverages/jdr/contributors',
               json.dumps({"id": contributor.get('id')}))
    r = to_json(raw)
    assert raw.status_code == 201
    contributors = r.get('coverages')[0].get('contributors')
    assert isinstance(contributors, list)
    assert len(contributors) == 1
    assert contributors[0] == contributor.get('id')

    # test add existing data_source in coverage
    raw = post(app, '/coverages/jdr/contributors',
               json.dumps({"id": contributor.get('id')}))
    r = to_json(raw)
    assert raw.status_code == 409
    assert r.get('error') == 'contributor id {} already exists in coverage jdr'.format(contributor.get('id'))


def test_delete_unknown_coverage(app):
    raw = delete(app, '/coverages/jdr/contributors/toto')
    r = to_json(raw)
    assert raw.status_code == 404
    assert r.get('error') == 'unknown coverage id "jdr"'


def test_delete_unknown_contributor(app, coverage, contributor):
    raw = delete(app, '/coverages/jdr/contributors/toto')
    r = to_json(raw)
    assert raw.status_code == 404
    assert r.get('error') == 'unknown contributor id "toto" attribute in uri'


def test_delete_valid_contributor(app, coverage, contributor):
    raw = post(app, '/coverages/jdr/contributors', json.dumps({"id": contributor.get('id')}))
    assert raw.status_code==201
    raw = app.get('/coverages/jdr')
    r = to_json(raw)
    assert len(r['coverages'][0]['contributors']) == 1

    r = delete(app, '/coverages/jdr/contributors/{}'.format(contributor.get('id')))

    raw = app.get('/coverages/jdr')
    r = to_json(raw)
    assert len(r['coverages'][0]['contributors']) == 0
