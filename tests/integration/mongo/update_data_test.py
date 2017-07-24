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
from tartare.tasks import send_file_to_tyr_and_discard
import requests_mock
from tests.utils import to_json, get_valid_ntfs_memory_archive
from tartare.core.gridfs_handler import GridFsHandler

from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED


def test_upload_file_ok(coverage_obj, fixture_dir):
    path = os.path.join(fixture_dir, 'geo_data/empty_pbf.osm.pbf')
    with open(path, 'rb') as f:
        grifs_handler = GridFsHandler()
        file_id = grifs_handler.save_file_in_gridfs(f, filename='test.osm.pbf')
    with requests_mock.Mocker() as m:
        m.post('http://tyr.prod/v0/instances/test', text='ok')
        send_file_to_tyr_and_discard(coverage_obj.id, 'production', file_id)
        assert m.called


def test_get_ntfs_file_ok(app, coverage_obj, fixture_dir):
    with get_valid_ntfs_memory_archive() as (ntfs_file_name, ntfs_zip_memory):
        files = {'file': (ntfs_zip_memory, ntfs_file_name)}
        with requests_mock.Mocker() as m:
            m.post('http://tyr.prod/v0/instances/test', text='ok')
            raw = app.post('/coverages/test/environments/production/data_update', data=files)
        r = to_json(raw)
        assert r['message'].startswith('Valid fusio file provided')
        raw = app.get('/coverages/test/environments/production/data/ntfs')
        assert raw.status_code == 200
        assert raw.mimetype == 'application/zip'
        data = raw.get_data()
        with BytesIO(data) as ntfs_zip_memory:
            ntfs_zip = ZipFile(ntfs_zip_memory, 'r', ZIP_DEFLATED, False)
            assert ntfs_zip.testzip() is None
            ntfs_zip.close()


def test_get_ntfs_bad_requedted_type(app, coverage_obj, fixture_dir):
    with get_valid_ntfs_memory_archive() as (ntfs_file_name, ntfs_zip_memory):
        files = {'file': (ntfs_zip_memory, ntfs_file_name)}
        with requests_mock.Mocker() as m:
            m.post('http://tyr.prod/v0/instances/test', text='ok')
            raw = app.post('/coverages/test/environments/production/data_update', data=files)
        r = to_json(raw)
        assert r['message'].startswith('Valid fusio file provided')
        raw = app.get('/coverages/test/environments/production/data/ntfs_error')
        r = to_json(raw)
        assert raw.status_code == 400
        assert r["error"].startswith('Bad data type')
