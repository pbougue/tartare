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
from tartare import mongo
from tests.utils import to_json, post, patch
from gridfs import GridFS
from bson.objectid import ObjectId
from zipfile import ZipFile, ZIP_DEFLATED
from glob import glob
from tartare.core import calendar_handler


def test_post_grid_calendar_returns_success_status(app, coverage, get_app_context):
    filename = 'export_calendars.zip'
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'fixtures/gridcalendar/', filename)
    files = {'file': (open(path, 'rb'), 'export_calendars.zip')}
    raw = app.post('/coverages/jdr/grid_calendar', data=files)
    r = to_json(raw)
    input_dir = coverage['technical_conf']['input_dir']
    assert raw.status_code == 200
    assert r.get('message') == 'OK'
    raw = app.get('/coverages')
    r = to_json(raw)
    assert len(r['coverages']) == 1
    assert 'grid_calendars_id' in r['coverages'][0]
    gridfs = GridFS(mongo.db)
    file_id = r['coverages'][0]['grid_calendars_id']
    assert gridfs.exists(ObjectId(file_id))
    #we update the file (it's the same, but that's not the point)
    files = {'file': (open(path, 'rb'), 'export_calendars.zip')}
    raw = app.post('/coverages/jdr/grid_calendar', data=files)
    assert raw.status_code == 200

    raw = app.get('/coverages')
    r = to_json(raw)
    assert len(r['coverages']) == 1
    assert 'grid_calendars_id' in r['coverages'][0]
    #it should be another file
    assert file_id != r['coverages'][0]['grid_calendars_id']
    #the previous file has been deleted
    assert not gridfs.exists(ObjectId(file_id))
    #and the new one exist
    assert gridfs.exists(ObjectId(r['coverages'][0]['grid_calendars_id']))



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


def test_update_calendar_data_with_last_ntfs_after_post(app, coverage_obj, fixture_dir):
    """
    we have a ntfs for the coverage, when we publish a new gris_calendar we want a ntfs to be generated for tyr
    """
    calendar_file = os.path.join(fixture_dir, 'gridcalendar/export_calendars.zip')
    print(calendar_file)
    ntfs_path = os.path.join(fixture_dir, 'ntfs/*.txt')

    path = os.path.join(coverage_obj.technical_conf.current_data_dir, 'ntfs.zip')
    ntfs_zip = ZipFile(path, 'a', ZIP_DEFLATED, False)
    for filename in glob(ntfs_path):
        ntfs_zip.write(filename, os.path.basename(filename))
    ntfs_zip.close()


    files = {'file': (open(calendar_file, 'rb'), 'export_calendars.zip')}
    raw = app.post('/coverages/{}/grid_calendar'.format(coverage_obj.id), data=files)
    print(to_json(raw))
    assert raw.status_code == 200

    files_in_output_dir = os.listdir(coverage_obj.technical_conf.output_dir)

    assert files_in_output_dir[0].endswith('database.zip')

    with ZipFile(os.path.join(coverage_obj.technical_conf.output_dir, files_in_output_dir[0])) as new_ntfs_zip:
        files_in_zip = new_ntfs_zip.namelist()
        assert calendar_handler.GRID_CALENDARS in files_in_zip
        assert calendar_handler.GRID_PERIODS in files_in_zip
        assert calendar_handler.GRID_CALENDAR_REL_LINE in files_in_zip
