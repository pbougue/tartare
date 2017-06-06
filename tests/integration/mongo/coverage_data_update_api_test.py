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
from tests.utils import to_json, get_valid_ntfs_memory_archive
import requests_mock
from tartare.tasks import send_file_to_tyr_and_discard, send_ntfs_to_tyr


def test_post_pbf_returns_success_status(app, coverage_obj, fixture_dir):
    path = os.path.join(fixture_dir, 'geo_data/empty_pbf.osm.pbf')
    files = {'file': (open(path, 'rb'), 'empty_pbf.osm.pbf')}
    with requests_mock.Mocker() as m:
        m.post('http://tyr.prod/v0/instances/test', text='ok')
        raw = app.post('/coverages/test/environments/production/data_update', data=files)
        assert m.called
    r = to_json(raw)
    assert raw.status_code == 200
    assert r.get('message').startswith('Valid osm file provided')


def test_post_pbf_mocked(app, coverage_obj, fixture_dir, mocker):
    m = mocker.patch.object(send_file_to_tyr_and_discard, 'delay')
    path = os.path.join(fixture_dir, 'geo_data/empty_pbf.osm.pbf')
    files = {'file': (open(path, 'rb'), 'empty_pbf.osm.pbf')}
    raw = app.post('/coverages/test/environments/production/data_update', data=files)
    assert m.called
    r = to_json(raw)
    assert raw.status_code == 200
    assert r.get('message').startswith('Valid osm file provided')


def test_post_pbf_with_bad_param(app, coverage_obj, fixture_dir):
    filename = 'empty_pbf.osm.pbf'
    path = os.path.join(fixture_dir, 'geo_data/empty_pbf.osm.pbf')
    files = {'file_name': (open(path, 'rb'), 'empty_pbf.osm.pbf')}
    raw = app.post('/coverages/test/environments/production/data_update', data=files)
    r = to_json(raw)
    assert raw.status_code == 400
    assert r.get('error') == 'File provided with bad param ("file" param expected).'


def test_post_osm_returns_invalid_file_extension_message(app, coverage_obj, fixture_dir):
    filename = 'empty_pbf.funky_extension'
    path = os.path.join(fixture_dir, 'geo_data/empty_pbf.funky_extension')
    files = {'file': (open(path, 'rb'), 'empty_pbf.funky_extension')}
    raw = app.post('/coverages/test/environments/production/data_update', data=files)
    r = to_json(raw)
    assert raw.status_code == 400
    assert r.get('error').startswith('Invalid file provided')


def test_post_osm_returns_invalid_coverage(app, fixture_dir):
    path = os.path.join(fixture_dir, 'geo_data/empty_pbf.osm.pbf')
    files = {'file': (open(path, 'rb'), 'empty_pbf.funky_extension')}
    raw = app.post('/coverages/jdr_bug/environments/production/data_update', data=files)
    r = to_json(raw)
    assert raw.status_code == 404
    assert r.get('error') == 'Coverage jdr_bug not found.'


def test_post_pbf_returns_file_missing_message(app, coverage_obj):
    raw = app.post('/coverages/test/environments/production/data_update')
    r = to_json(raw)
    assert raw.status_code == 400
    assert r.get('error') == 'No file provided.'


def test_post_ntfs_success(app, coverage_obj):
    #create ZIP file with fixture before sending it
    with get_valid_ntfs_memory_archive() as (ntfs_file_name, ntfs_zip_memory):
        files = {'file': (ntfs_zip_memory, ntfs_file_name)}
        with requests_mock.Mocker() as m:
            m.post('http://tyr.prod/v0/instances/test', text='ok')
            raw = app.post('/coverages/test/environments/production/data_update', data=files)
            assert m.called
        r = to_json(raw)
        assert raw.status_code == 200
        assert r.get('message').startswith('Valid fusio file provided')


def test_post_ntfs_mocked(app, coverage_obj, mocker):
    #create ZIP file with fixture before sending it
    m = mocker.patch.object(send_ntfs_to_tyr, 'delay')
    with get_valid_ntfs_memory_archive() as (ntfs_file_name, ntfs_zip_memory):
        files = {'file': (ntfs_zip_memory, ntfs_file_name)}
        raw = app.post('/coverages/test/environments/production/data_update', data=files)
        assert m.called
        r = to_json(raw)
        assert raw.status_code == 200
        assert r.get('message').startswith('Valid fusio file provided')
