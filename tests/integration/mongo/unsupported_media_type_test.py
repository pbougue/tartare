
import json
from tests.integration.test_mechanism import TartareFixture


class TestUnsupportedMediaType(TartareFixture):
    def test_posts_without_head(self):
        roots = ['/contributors/id_test/preprocesses',
                 '/contributors',
                 '/coverages',
                 '/coverages/unknown/contributors',
                 '/coverages/jdr/preprocesses',
                 '/contributors/id_test/data_sources',
                 ]
        for root in roots:
            raw = self.post(root, json.dumps({}), headers=None)
            assert raw.status_code == 415
            r = self.to_json(raw)
            assert r['error'] == 'request without data.'

    def test_patchs_without_head(self):
        roots = ['/coverages/jdr/preprocesses/1234',
                 '/contributors/id_test/data_sources'
                 ]
        for root in roots:
            raw = self.patch(root, json.dumps({}), headers=None)
            assert raw.status_code == 415
            r = self.to_json(raw)
            assert r['error'] == 'request without data.'
