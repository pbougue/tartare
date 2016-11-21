import os
from tartare.tasks import send_file_to_tyr_and_discard
from tartare.core import models
import requests_mock
import logging
from tests.utils import to_json, get_valid_ntfs_memory_archive

from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED


def test_upload_file_ok(coverage_obj, fixture_dir):
    path = os.path.join(fixture_dir, 'geo_data/empty_pbf.osm.pbf')
    with open(path, 'rb') as f:
        file_id = models.save_file_in_gridfs(f, filename='test.osm.pbf')
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
        assert raw.status_code == 404
        assert r["message"].startswith('bad data type')
