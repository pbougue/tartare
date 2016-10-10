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
from glob import glob
from tests.utils import to_json, post, patch
from zipfile import ZipFile, ZIP_DEFLATED


def test_post_pbf_returns_success_status(app, coverage):
    filename = 'empty_pbf.osm.pbf'
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'fixtures/geo_data/', filename)
    files = {'file': (open(path, 'rb'), 'empty_pbf.osm.pbf')}
    raw = app.post('/coverages/jdr/data_update', data=files)
    r = to_json(raw)
    input_dir = coverage['technical_conf']['input_dir']
    assert input_dir == './input/jdr'
    assert raw.status_code == 200
    assert r.get('message').startswith('Valid osm file provided')
    assert os.path.exists(os.path.join(input_dir, filename))

def test_post_osm_returns_invalid_file_extension_message(app, coverage):
    filename = 'empty_pbf.funky_extension'
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'fixtures/geo_data/', filename)
    files = {'file': (open(path, 'rb'), 'empty_pbf.funky_extension')}
    raw = app.post('/coverages/jdr/data_update', data=files)
    r = to_json(raw)
    assert raw.status_code == 400
    assert r.get('message').startswith('invalid file provided')

def test_post_osm_returns_invalid_coverage(app, coverage):
    filename = 'empty_pbf.osm.pbf'
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'fixtures/geo_data/', filename)
    files = {'file': (open(path, 'rb'), 'empty_pbf.funky_extension')}
    raw = app.post('/coverages/jdr_bug/data_update', data=files)
    r = to_json(raw)
    assert raw.status_code == 404
    assert r.get('message') == 'bad coverage jdr_bug'

def test_post_pbf_returns_file_missing_message(app, coverage):
    raw = app.post('/coverages/jdr/data_update')
    r = to_json(raw)
    assert raw.status_code == 400
    assert r.get('message') == 'no file provided'

def test_post_ntfs_success(tmpdir, app, coverage):
    #create ZIP file with fixture before sending it
    input = tmpdir.mkdir('input')
    ntfs_file_name = 'ntfs.zip'
    ntfs_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'fixtures/ntfs/*.txt')
    ntfs_zip = ZipFile(os.path.join(str(input), ntfs_file_name), 'a', ZIP_DEFLATED, False)
    for filename in glob(ntfs_path):
        ntfs_zip.write(filename, os.path.basename(filename))
    ntfs_zip.close()
    ntfs_path = os.path.join(os.path.join(str(input), ntfs_file_name))
    assert os.path.isfile(ntfs_path)

    files = {'file': (open(ntfs_path, 'rb'), ntfs_file_name)}
    raw = app.post('/coverages/jdr/data_update', data=files)
    r = to_json(raw)
    input_dir = coverage['technical_conf']['input_dir']
    assert input_dir == './input/jdr'
    assert raw.status_code == 200
    assert r.get('message').startswith('Valid fusio file provided')
    assert os.path.exists(os.path.join(input_dir, filename))
