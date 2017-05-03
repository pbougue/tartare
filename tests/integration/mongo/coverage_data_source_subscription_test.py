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
from tests.utils import to_json, post
import json


def test_bad_coverage(app):
    raw = post(app, '/coverages/unknown/data_sources',
               '''{"id": "bob"}''')
    r = to_json(raw)
    assert raw.status_code == 400
    assert r.get('message') == 'Bad coverage unknown.'


def test_missing_data_source_id(app, coverage):
    raw = post(app, '/coverages/jdr/data_sources',
               '''{}''')
    r = to_json(raw)
    assert raw.status_code == 400
    assert r.get('message') == 'Missing data_source_id attribute in request body.'


def test_unknown_data_source(app, coverage):
    raw = post(app, '/coverages/jdr/data_sources',
               '''{"id": "bob"}''')
    r = to_json(raw)
    assert raw.status_code == 400
    assert r.get('message') == 'Unknown data_source_id bob.'


def test_add_data_source(app, coverage, data_source):
    raw = post(app, '/coverages/jdr/data_sources',
               json.dumps({"id": data_source.get('id')}))
    r = to_json(raw)
    assert raw.status_code == 200
    data_sources = r.get('coverages')[0].get('data_sources')
    assert isinstance(data_sources, list)
    assert len(data_sources) == 1
    assert data_sources[0] == data_source.get('id')

    # test add existing data_source in coverage
    raw = post(app, '/coverages/jdr/data_sources',
               json.dumps({"id": data_source.get('id')}))
    r = to_json(raw)
    assert raw.status_code == 409
    assert r.get('message') == 'Data source id {} already exists in coverage jdr.'.format(data_source.get('id'))
