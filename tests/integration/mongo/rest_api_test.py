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
import os
import pytest
import tartare
import tartare.api
import json
from tests.utils import to_json


@pytest.fixture(scope="function")
def coverage(app):
    coverage = app.post('/coverages',
                headers={'Content-Type': 'application/json'},
               data='{"id": "jdr", "name": "name of the coverage jdr"}')
    return to_json(coverage)['coverage']


def test_post_grid_calendar_returns_success_status(app, coverage):
    filename = 'export_calendars.zip'
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'fixtures/gridcalendar/', filename)
    files = {'file': (open(path, 'rb'), 'export_calendars.zip')}
    raw = app.post('/coverages/jdr/grid_calendar', data=files)
    r = to_json(raw)
    input_dir = coverage['technical_conf']['input_dir']
    assert input_dir == './input/jdr'
    assert raw.status_code == 200
    assert r.get('message') == 'OK'
    assert os.path.exists(os.path.join(input_dir, filename))


def test_post_grid_calendar_returns_non_compliant_file_status(app, coverage):
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                        'fixtures/gridcalendar/export_calendars_with_invalid_header.zip')
    files = {'file': (open(path, 'rb'), 'export_calendars.zip')}
    raw = app.post('/coverages/jdr/grid_calendar', data=files)
    r = to_json(raw)
    assert raw.status_code == 400
    assert r.get('message') == 'non-compliant file(s) : grid_periods.txt'


def test_post_grid_calendar_returns_file_missing_status(app, coverage):
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                        'fixtures/gridcalendar/export_calendars_without_grid_calendars.zip')
    files = {'file': (open(path, 'rb'), 'export_calendars.zip')}
    raw = app.post('/coverages/jdr/grid_calendar', data=files)
    r = to_json(raw)
    assert raw.status_code == 400
    assert r.get('message') == 'file(s) missing : grid_calendars.txt'


def test_post_grid_calendar_returns_archive_missing_message(app, coverage):
    raw = app.post('/coverages/jdr/grid_calendar')
    r = to_json(raw)
    assert raw.status_code == 400
    assert r.get('message') == 'the archive is missing'


def test_unkown_version_status(app):
    raw = app.get('/status')
    r = to_json(raw)
    assert raw.status_code == 200
    assert r.get('version') == 'unknown_version'


def test_kown_version_status(app, monkeypatch):
    """if TARTARE_VERSION is given at startup, a version is available"""
    version = 'v1.42.12'
    monkeypatch.setitem(os.environ, 'TARTARE_VERSION', version)
    raw = app.get('/status')
    r = to_json(raw)
    assert raw.status_code == 200
    assert r.get('version') == version

