import json

from tests.integration.test_mechanism import TartareFixture


class TestUnsupportedMediaType(TartareFixture):
    def test_posts_without_head(self):
        roots = ['/contributors',
                 '/coverages',
                 ]
        for root in roots:
            raw = self.post(root, json.dumps({}), headers=None)
            assert raw.status_code == 415
            r = self.json_to_dict(raw)
            assert r['error'] == 'request without data'

    def test_put_without_head(self):
        roots = ['/contributors/id_test',
                 ]
        for root in roots:
            raw = self.put(root, json.dumps({}), headers=None)
            assert raw.status_code == 415
            r = self.json_to_dict(raw)
            assert r['error'] == 'request without data'
