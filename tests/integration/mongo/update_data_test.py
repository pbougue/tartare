import os
from tartare.tasks import send_file_to_tyr_and_discard
from tartare.core import models
import requests_mock

def test_upload_file_ok(coverage_obj, fixture_dir):
    path = os.path.join(fixture_dir, 'geo_data/empty_pbf.osm.pbf')
    with open(path, 'rb') as f:
        file_id = models.save_file_in_gridfs(f, filename='test.osm.pbf')
    with requests_mock.Mocker() as m:
        m.post('http://tyr.prod/v0/instances/test', text='ok')
        send_file_to_tyr_and_discard(coverage_obj.id, 'production', file_id)
        assert m.called
