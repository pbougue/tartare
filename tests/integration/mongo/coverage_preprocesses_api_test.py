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
import json

import pytest

from tartare.core.constants import DATA_FORMAT_GTFS
from tests.integration.test_mechanism import TartareFixture


class TestCoveragePreProcesses(TartareFixture):
    def test_post_ds_one_data_source_without_id(self):
        '''
        using /preprocesses endpoint
        '''
        post_ps = {
            "type": "FusioDataUpdate",
            "sequence": 1,
            "params": {
                "url": "http://fusio.canaltp.fr/fusio.dll"
            }
        }

        coverage = {"id": "jdr", "name": "name of the coverage jdr"}
        raw = self.post('/coverages', json.dumps(coverage))
        assert raw.status_code == 201, print(self.json_to_dict(raw))

        raw = self.post('/coverages/jdr/preprocesses', json.dumps(post_ps))
        assert raw.status_code == 201, print(self.json_to_dict(raw))

        raw = self.get('/coverages/jdr/preprocesses')
        r = self.json_to_dict(raw)
        self.assert_sucessful_call(raw)
        assert len(r["preprocesses"]) == 1
        assert r["preprocesses"][0]["type"] == post_ps["type"]
        assert r["preprocesses"][0]["params"] == post_ps["params"]

        preprocess_id = r["preprocesses"][0]["id"]

        raw = self.get('/coverages/jdr/preprocesses/{}'.format(preprocess_id))
        r = self.json_to_dict(raw)
        self.assert_sucessful_call(raw)
        assert len(r["preprocesses"]) == 1
        assert r["preprocesses"][0]["type"] == post_ps["type"]
        assert r["preprocesses"][0]["params"] == post_ps["params"]

        raw = self.get('/coverages/jdr/preprocesses/toto')
        r = self.json_to_dict(raw)
        assert raw.status_code == 404, print(r)

    def test_post_contrib_one_data_source_with_id(self):
        '''
        using /coverages endpoint
        '''
        post_data = {"id": "jdr", "name": "name of the coverage jdr"}
        post_data["preprocesses"] = [{
            "id": "toto",
            "type": "FusioDataUpdate",
            "sequence": 1,
            "params": {
                "url": "http://fusio.canaltp.fr/fusio.dll"
            }
        }]
        raw = self.post('/coverages', json.dumps(post_data))
        assert raw.status_code == 201, print(self.json_to_dict(raw))
        raw = self.get('/coverages/jdr/')
        r = self.json_to_dict(raw)
        self.assert_sucessful_call(raw)
        assert len(r["coverages"][0]["preprocesses"]) == 1
        assert r["coverages"][0]["preprocesses"][0]['id'] == 'toto'

    def test_update_preprocess_with_id(self):
        '''
        using /coverages endpoint
        '''
        post_data = {"id": "jdr", "name": "name of the coverage jdr"}
        post_data["preprocesses"] = [{
            "id": "toto",
            "type": "FusioDataUpdate",
            "sequence": 1,
            "params": {
                "url": "http://fusio.canaltp.fr/fusio.dll"
            }
        }]
        raw = self.post('/coverages', json.dumps(post_data))
        assert raw.status_code == 201, print(self.json_to_dict(raw))
        raw = self.get('/coverages/jdr/')
        r = self.json_to_dict(raw)
        self.assert_sucessful_call(raw)
        assert len(r["coverages"][0]["preprocesses"]) == 1
        preprocess_id = r["coverages"][0]["preprocesses"][0]["id"]
        new_preprocess = {
            "type": "FusioImport",
            "id": preprocess_id,
            "sequence": 1,
            "params": {
                "url": "http://fusio.canaltp.fr/fusio.dll"
            }
        }

        raw = self.patch('/coverages/jdr/preprocesses/{}'.format(preprocess_id), json.dumps(new_preprocess))
        r = self.json_to_dict(raw)
        self.assert_sucessful_call(raw)
        assert len(r["preprocesses"]) == 1
        assert r["preprocesses"][0]["type"] == new_preprocess["type"]
        assert r["preprocesses"][0]["params"] == new_preprocess["params"]

    def test_delete_preprocess(self):
        '''
        using /contributors endpoint
        '''
        post_data = {"id": "jdr", "name": "name of the coverage jdr"}
        post_data["preprocesses"] = [{
            "id": "toto",
            "type": "FusioImport",
            "sequence": 1,
            "params": {
                "url": "http://fusio.canaltp.fr/fusio.dll"
            }
        }]
        raw = self.post('/coverages', json.dumps(post_data))
        r = self.json_to_dict(raw)
        self.assert_sucessful_create(raw)

        preprocess_id = r["coverages"][0]["preprocesses"][0]["id"]
        raw = self.delete('/coverages/jdr/preprocesses/{}'.format(preprocess_id))
        self.assert_sucessful_call(raw, 204)
        raw = self.get('/coverages/jdr/preprocesses')
        r = self.json_to_dict(raw)
        assert len(r['preprocesses']) == 0

    def test_post_preprocess_with_unknown_type(self):
        '''
        using /preprocesses endpoint
        '''

        contributor = {"id": "jdr", "name": "name of the coverage jdr"}
        raw = self.post('/coverages', json.dumps(contributor))
        assert raw.status_code == 201, print(self.json_to_dict(raw))

        post_ps = {
            "type": "bob",
            "sequence": 1,
            "params": {
                "url": "http://fusio.canaltp.fr/fusio.dll"
            }
        }
        raw = self.post('/coverages/jdr/preprocesses', json.dumps(post_ps))
        r = self.json_to_dict(raw)
        assert raw.status_code == 400, print(r)
        assert 'error' in r
        assert r['error'] == "impossible to build preprocess bob : " \
                             + "modules within tartare.processes.coverage have no class bob"

    def test_update_preprocess_with_unknown_type(self):
        '''
        using /contributors endpoint
        '''
        post_data = {"id": "jdr", "name": "name of the coverage jdr"}
        post_data["preprocesses"] = [{
            "id": "toto",
            "type": "FusioImport",
            "sequence": 1,
            "params": {
                "url": "http://fusio.canaltp.fr/fusio.dll"
            }
        }]
        raw = self.post('/coverages', json.dumps(post_data))
        r = self.json_to_dict(raw)
        self.assert_sucessful_create(raw)

        preprocess_id = r["coverages"][0]["preprocesses"][0]["id"]
        new_preprocess = {
            "type": "bob",
            "sequence": 1,
            "params": {
                "url": "http://fusio.canaltp.fr/fusio.dll"
            }
        }

        raw = self.patch('/coverages/jdr/preprocesses/{}'.format(preprocess_id), json.dumps(new_preprocess))
        r = self.json_to_dict(raw)
        assert raw.status_code == 400, print(r)
        assert 'error' in r
        assert r['error'] == "impossible to build preprocess bob : " \
                             + "modules within tartare.processes.coverage have no class bob"

    def test_update_preprocesses_with_id(self):
        '''
        using /contributors endpoint
        '''
        post_data = {"id": "jdr", "name": "name of the coverage jdr"}
        post_data["preprocesses"] = [
            {
                "id": "toto",
                "type": "FusioDataUpdate",
                "sequence": 1,
                "params": {
                    "url": "http://fusio.canaltp.fr/fusio.dll"
                }
            },
            {
                "id": "titi",
                "type": "FusioImport",
                "sequence": 2,
                "params": {
                    "url": "http://fusio.canaltp.fr/fusio.dll"
                }
            }
        ]

        raw = self.post('/coverages', json.dumps(post_data))
        assert raw.status_code == 201, print(self.json_to_dict(raw))
        raw = self.get('/coverages/jdr/')
        r = self.json_to_dict(raw)
        self.assert_sucessful_call(raw)
        assert len(r["coverages"][0]["preprocesses"]) == 2
        new_preprocess = {
            "type": "FusioPreProd",
            "sequence": 3,
            "params": {
                "url": "http://fusio.canaltp.fr/fusio.dll"
            }
        }

        raw = self.patch('/coverages/jdr/preprocesses/titi', json.dumps(new_preprocess))
        r = self.json_to_dict(raw)
        self.assert_sucessful_call(raw)
        # Update only one preprocess
        assert len(r["preprocesses"]) == 1

        raw = self.get('/coverages/jdr')
        r = self.json_to_dict(raw)
        self.assert_sucessful_call(raw)
        assert len(r["coverages"][0]["preprocesses"]) == 2
        p_titi = None
        for p in r["coverages"][0]["preprocesses"]:
            if p['id'] == 'titi':
                p_titi = p
        assert p_titi
        assert p_titi['type'] == 'FusioPreProd'

    def test_add_preprocess_generates_computed_data_source(self, coverage):
        self.add_preprocess_to_coverage({
            "sequence": 0,
            "type": "FusioExport",
            "params": {
                "url": "http://fusio-ihm.fr-ne-amiens.dev.canaltp.fr/cgi-bin/fusio.dll",
                "export_type": DATA_FORMAT_GTFS,
                "target_data_source_id": "gtfs_export"
            }
        }, coverage['id'])
        coverage_data_sources = self.get_coverage(coverage['id'])['data_sources']
        assert len(coverage_data_sources) == 1
        assert coverage_data_sources[0]['data_format'] == DATA_FORMAT_GTFS
        assert coverage_data_sources[0]['id'] == 'gtfs_export'

    def test_update_preprocess_generates_computed_data_source(self, coverage):
        self.add_preprocess_to_coverage({
            "sequence": 0,
            "type": "FusioExport",
            "params": {
                "url": "http://fusio-ihm.fr-ne-amiens.dev.canaltp.fr/cgi-bin/fusio.dll",
                "export_type": DATA_FORMAT_GTFS,
            }
        }, coverage['id'])
        coverage_created = self.get_coverage(coverage['id'])
        assert len(coverage_created['data_sources']) == 0
        coverage_created['preprocesses'][0]['params']['target_data_source_id'] = 'gtfs_export'
        self.put('/coverages/{}'.format(coverage['id']), self.dict_to_json(coverage_created))
        coverage_data_sources = self.get_coverage(coverage['id'])['data_sources']
        assert len(coverage_data_sources) == 1
        assert coverage_data_sources[0]['data_format'] == DATA_FORMAT_GTFS
        assert coverage_data_sources[0]['id'] == 'gtfs_export'

    def test_add_preprocess_empty_target_data_source_id_generates_computed_data_source(self, coverage):
        self.add_preprocess_to_coverage({
            "sequence": 0,
            "type": "FusioExport",
            "params": {
                "url": "http://fusio-ihm.fr-ne-amiens.dev.canaltp.fr/cgi-bin/fusio.dll",
                "export_type": DATA_FORMAT_GTFS,
                "target_data_source_id": ""
            }
        }, coverage['id'])
        coverage_created = self.get_coverage(coverage['id'])
        coverage_data_sources = coverage_created['data_sources']
        assert len(coverage_data_sources) == 1
        assert coverage_data_sources[0]['data_format'] == DATA_FORMAT_GTFS
        assert coverage_data_sources[0]['id'] is not None
        assert coverage_created['preprocesses'][0]['params']['target_data_source_id'] == \
               coverage_data_sources[0]['id']

    def test_preprocess_enabled_by_default(self, coverage):
        self.add_preprocess_to_coverage({
            "id": "fusio_preprod",
            "type": "FusioPreProd",
            "sequence": 3,
            "params": {
                "url": "http://fusio.canaltp.fr/fusio.dll"
            }
        }, coverage['id'])
        preprocesses = self.json_to_dict(
            self.get('/coverages/{}/preprocesses'.format(coverage['id']))
        )['preprocesses']
        assert len(preprocesses) == 1
        preprocess = preprocesses[0]
        assert preprocess['enabled'] == True

    @pytest.mark.parametrize("enabled", [
        True,
        False
    ])
    def test_preprocess_enabled_specified(self, coverage, enabled):
        self.add_preprocess_to_coverage({
            "id": "fusio_preprod",
            "type": "FusioPreProd",
            "sequence": 3,
            "params": {
                "url": "http://fusio.canaltp.fr/fusio.dll"
            },
            "enabled": enabled
        }, coverage['id'])
        preprocess = self.json_to_dict(
            self.get('/coverages/{}/preprocesses'.format(coverage['id']))
        )['preprocesses'][0]
        assert preprocess['enabled'] == enabled
