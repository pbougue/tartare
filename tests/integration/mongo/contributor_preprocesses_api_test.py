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

from tartare.core.constants import DATA_FORMAT_PT_EXTERNAL_SETTINGS
from tests.integration.test_mechanism import TartareFixture


class TestContributorPreProcesses(TartareFixture):
    def test_post_ds_one_data_source_without_id(self):
        '''
        using /preprocesses endpoint
        '''
        post_ps = {
            "type": "Ruspell",
            "sequence": 1,
            "data_source_ids": ["datasource_stif"],
            "params": {
                "links": [
                    {"contributor_id": "geographic_id", "data_source_id": "bano_75"},
                    {"contributor_id": "geographic_id", "data_source_id": "bano_91"},
                    {"contributor_id": "id_test", "data_source_id": "conf_yml"},
                ]
            }
        }

        contributor = {"id": "id_test", "name": "name_test", "data_prefix": "AAA"}
        raw = self.post('/contributors', json.dumps(contributor))
        assert raw.status_code == 201, print(self.json_to_dict(raw))

        raw = self.post('/contributors/id_test/preprocesses', json.dumps(post_ps))
        assert raw.status_code == 201, print(self.json_to_dict(raw))

        raw = self.get('/contributors/id_test/preprocesses')
        r = self.json_to_dict(raw)
        self.assert_sucessful_call(raw)
        assert len(r["preprocesses"]) == 1
        assert r["preprocesses"][0]["type"] == post_ps["type"]
        assert r["preprocesses"][0]["data_source_ids"].sort() == post_ps["data_source_ids"].sort()
        assert r["preprocesses"][0]["params"] == post_ps["params"]

        preprocess_id = r["preprocesses"][0]["id"]

        raw = self.get('/contributors/id_test/preprocesses/{}'.format(preprocess_id))
        r = self.json_to_dict(raw)
        self.assert_sucessful_call(raw)
        assert len(r["preprocesses"]) == 1
        assert r["preprocesses"][0]["type"] == post_ps["type"]
        assert r["preprocesses"][0]["data_source_ids"].sort() == post_ps["data_source_ids"].sort()
        assert r["preprocesses"][0]["params"] == post_ps["params"]

    def test_preprocess_not_found(self):
        contributor = {"id": "id_test", "name": "name_test", "data_prefix": "AAA"}
        raw = self.post('/contributors', json.dumps(contributor))
        assert raw.status_code == 201, print(self.json_to_dict(raw))

        raw = self.get('/contributors/id_test/preprocesses/toto')
        r = self.json_to_dict(raw)
        assert raw.status_code == 404, print(r)

    def test_post_contrib_one_data_source_with_id(self):
        '''
        using /contributors endpoint
        '''
        post_data = {
            "id": "id_test", "name": "name_test", "data_prefix": "AAA",
            "data_sources": [{
                "id": "datasource_stif",
                "name": "datasource_stif",
                "input": {
                    "type": "url",
                    "url": "http://stif.com/ods.zip"
                }
            }],
            "preprocesses": [{
                "id": "toto",
                "type": "Ruspell",
                "sequence": 1,
                "data_source_ids": ["datasource_stif"],
                "params": {
                    "links": [
                        {"contributor_id": "geographic_id", "data_source_id": "bano_75"},
                        {"contributor_id": "geographic_id", "data_source_id": "bano_91"},
                        {"contributor_id": "id_test", "data_source_id": "conf_yml"},
                    ]
                }
            }]
        }
        raw = self.post('/contributors', json.dumps(post_data))
        assert raw.status_code == 201, print(self.json_to_dict(raw))
        raw = self.get('/contributors/id_test/')
        r = self.json_to_dict(raw)
        self.assert_sucessful_call(raw)
        assert len(r["contributors"][0]["preprocesses"]) == 1
        assert r["contributors"][0]["preprocesses"][0]['id'] == 'toto'

    def test_update_preprocess_with_id(self):
        '''
        using /contributors endpoint
        '''
        post_data = {
            "id": "id_test", "name": "name_test", "data_prefix": "AAA",
            "data_sources": [{
                "id": "datasource_stif",
                "name": "datasource_stif",
                "input": {
                    "type": "url",
                    "url": "http://stif.com/ods.zip"
                }
            }],
            "preprocesses": [{
                "id": "toto",
                "type": "Ruspell",
                "sequence": 1,
                "data_source_ids": ["datasource_stif"],
                "params": {
                    "links": [
                        {"contributor_id": "geographic_id", "data_source_id": "bano_75"},
                        {"contributor_id": "geographic_id", "data_source_id": "bano_91"},
                        {"contributor_id": "id_test", "data_source_id": "conf_yml"},
                    ]
                }
            }]
        }
        raw = self.post('/contributors', json.dumps(post_data))
        assert raw.status_code == 201, print(self.json_to_dict(raw))
        raw = self.get('/contributors/id_test/')
        r = self.json_to_dict(raw)
        self.assert_sucessful_call(raw)
        assert len(r["contributors"][0]["preprocesses"]) == 1
        preprocess_id = r["contributors"][0]["preprocesses"][0]["id"]
        new_preprocess = {
            "type": "ComputeDirections",
            "sequence": 1,
            "params": {
                "params": {
                    "links": [
                        {"contributor_id": "id_test", "data_source_id": "compute-direction-config"}
                    ]
                }
            }
        }

        raw = self.patch('/contributors/id_test/preprocesses/{}'.format(preprocess_id), json.dumps(new_preprocess))
        r = self.json_to_dict(raw)
        self.assert_sucessful_call(raw)
        assert len(r["preprocesses"]) == 1
        assert r["preprocesses"][0]["type"] == new_preprocess["type"]
        assert r["preprocesses"][0]["params"] == new_preprocess["params"]

    def test_delete_preprocess(self):
        '''
        using /contributors endpoint
        '''
        post_data = {
            "id": "id_test", "name": "name_test", "data_prefix": "AAA",
            "data_sources": [{
                "id": "datasource_stif",
                "name": "datasource_stif",
                "input": {
                    "type": "url",
                    "url": "http://stif.com/ods.zip"
                }
            }],
            "preprocesses": [{
                "id": "toto",
                "type": "Ruspell",
                "sequence": 1,
                "data_source_ids": ["datasource_stif"],
                "params": {
                    "links": [
                        {"contributor_id": "geographic_id", "data_source_id": "bano_75"},
                        {"contributor_id": "geographic_id", "data_source_id": "bano_91"},
                        {"contributor_id": "id_test", "data_source_id": "conf_yml"},
                    ]
                }
            }]
        }
        raw = self.post('/contributors', json.dumps(post_data))
        r = self.json_to_dict(raw)
        self.assert_sucessful_create(raw)

        preprocess_id = r["contributors"][0]["preprocesses"][0]["id"]
        raw = self.delete('/contributors/id_test/preprocesses/{}'.format(preprocess_id))
        self.assert_sucessful_call(raw, 204)
        raw = self.get('/contributors/id_test/preprocesses')
        r = self.json_to_dict(raw)
        assert len(r['preprocesses']) == 0

    def test_post_preprocess_with_unknown_type(self):
        '''
        using /preprocesses endpoint
        '''

        contributor = {"id": "id_test", "name": "name_test", "data_prefix": "AAA"}
        raw = self.post('/contributors', json.dumps(contributor))
        assert raw.status_code == 201, print(self.json_to_dict(raw))

        post_ps = {
            "type": "bob",
            "sequence": 1,
            "params": {
                "links": [
                    {"contributor_id": "geographic_id", "data_source_id": "bano_75"},
                    {"contributor_id": "geographic_id", "data_source_id": "bano_91"},
                    {"contributor_id": "id_test", "data_source_id": "conf_yml"},
                ]
            }
        }
        raw = self.post('/contributors/id_test/preprocesses', json.dumps(post_ps))
        r = self.json_to_dict(raw)
        assert raw.status_code == 400, print(r)
        assert 'error' in r
        assert r['error'] == "impossible to build preprocess bob : " \
                             "modules within tartare.processes.contributor have no class bob"

    def test_update_preprocess_with_unknown_type(self):
        '''
        using /contributors endpoint
        '''
        post_data = {
            "id": "id_test", "name": "name_test", "data_prefix": "AAA",
            "data_sources": [{
                "id": "datasource_stif",
                "name": "datasource_stif",
                "input": {
                    "type": "url",
                    "url": "http://stif.com/ods.zip"
                }
            }],
            "preprocesses": [{
                "id": "toto",
                "type": "Ruspell",
                "sequence": 1,
                "data_source_ids": ["datasource_stif"],
                "params": {
                    "links": [
                        {"contributor_id": "geographic_id", "data_source_id": "bano_75"},
                        {"contributor_id": "geographic_id", "data_source_id": "bano_91"},
                        {"contributor_id": "id_test", "data_source_id": "conf_yml"},
                    ]
                }
            }]
        }
        raw = self.post('/contributors', json.dumps(post_data))
        r = self.json_to_dict(raw)
        self.assert_sucessful_create(raw)

        preprocess_id = r["contributors"][0]["preprocesses"][0]["id"]
        new_preprocess = {
            "type": "bob",
            "sequence": 1,
            "data_source_ids": ["gtfs"]
        }

        raw = self.patch('/contributors/id_test/preprocesses/{}'.format(preprocess_id), json.dumps(new_preprocess))
        r = self.json_to_dict(raw)
        assert raw.status_code == 400, print(r)
        assert 'error' in r
        assert r['error'] == "impossible to build preprocess bob : " \
                             "modules within tartare.processes.contributor have no class bob"

    def test_update_preprocesses_with_id(self):
        '''
        using /contributors endpoint
        '''
        post_data = {
            "id": "id_test", "name": "name_test", "data_prefix": "AAA",
            "data_sources": [{
                "id": "datasource_stif",
                "name": "datasource_stif",
                "input": {
                    "type": "url",
                    "url": "http://stif.com/ods.zip"
                }
            }],
            "preprocesses": [
                {
                    "id": "toto",
                    "type": "Ruspell",
                    "sequence": 1,
                    "data_source_ids": ["datasource_stif"],
                    "params": {
                        "links": [
                            {"contributor_id": "geographic_id", "data_source_id": "bano_75"},
                            {"contributor_id": "geographic_id", "data_source_id": "bano_91"},
                            {"contributor_id": "id_test", "data_source_id": "conf_yml"},
                        ]
                    }
                },
                {
                    "id": "titi",
                    "type": "ComputeDirections",
                    "sequence": 2,
                    "data_source_ids": ["datasource_stif"]
                }
            ]}

        raw = self.post('/contributors', json.dumps(post_data))
        assert raw.status_code == 201, print(self.json_to_dict(raw))
        raw = self.get('/contributors/id_test/')
        r = self.json_to_dict(raw)
        self.assert_sucessful_call(raw)
        assert len(r["contributors"][0]["preprocesses"]) == 2
        new_preprocess = {
            "type": "HeadsignShortName",
            "sequence": 3,
            "data_source_ids": ["datasource_stif"]
        }

        raw = self.patch('/contributors/id_test/preprocesses/titi', json.dumps(new_preprocess))
        r = self.json_to_dict(raw)
        self.assert_sucessful_call(raw)
        # Update only one preprocess
        assert len(r["preprocesses"]) == 1

        raw = self.get('/contributors/id_test')
        r = self.json_to_dict(raw)
        self.assert_sucessful_call(raw)
        assert len(r["contributors"][0]["preprocesses"]) == 2
        p_titi = None
        for p in r["contributors"][0]["preprocesses"]:
            if p['id'] == 'titi':
                p_titi = p
        assert p_titi
        assert p_titi['type'] == 'HeadsignShortName'

    def test_add_preprocess_generates_computed_data_source(self, contributor):
        self.add_preprocess_to_contributor({
            "sequence": 0,
            "data_source_ids": [],
            "type": "ComputeExternalSettings",
            "params": {
                "target_data_source_id": "target_1",
                "export_type": DATA_FORMAT_PT_EXTERNAL_SETTINGS,
            }
        }, contributor['id'])
        contributor_data_sources = self.json_to_dict(
            self.get('/contributors/{}/data_sources'.format(contributor['id']))
        )['data_sources']
        assert len(contributor_data_sources) == 1
        assert contributor_data_sources[0]['data_format'] == DATA_FORMAT_PT_EXTERNAL_SETTINGS
        assert contributor_data_sources[0]['id'] == 'target_1'

    def test_update_preprocess_generates_computed_data_source(self, contributor):
        self.add_preprocess_to_contributor({
            "sequence": 0,
            "data_source_ids": [],
            "type": "ComputeExternalSettings",
            "params": {
                "export_type": DATA_FORMAT_PT_EXTERNAL_SETTINGS,
            }
        }, contributor['id'])
        contributor_created = self.get_contributor(contributor['id'])
        assert len(contributor_created['data_sources']) == 0
        contributor_created['preprocesses'][0]['params']['target_data_source_id'] = 'target_1'
        self.put('/contributors/{}'.format(contributor['id']), self.dict_to_json(contributor_created))
        contributor_data_sources = self.json_to_dict(
            self.get('/contributors/{}/data_sources'.format(contributor['id']))
        )['data_sources']
        assert len(contributor_data_sources) == 1
        assert contributor_data_sources[0]['data_format'] == DATA_FORMAT_PT_EXTERNAL_SETTINGS
        assert contributor_data_sources[0]['id'] == 'target_1'

    def test_add_preprocess_empty_target_data_source_id_generates_computed_data_source(self, contributor):
        self.add_preprocess_to_contributor({
            "sequence": 0,
            "data_source_ids": [],
            "type": "ComputeExternalSettings",
            "params": {
                "target_data_source_id": "",
                "export_type": DATA_FORMAT_PT_EXTERNAL_SETTINGS,
            }
        }, contributor['id'])
        contributor_created = self.get_contributor(contributor['id'])
        contributor_data_sources = contributor_created['data_sources']
        assert len(contributor_data_sources) == 1
        assert contributor_data_sources[0]['data_format'] == DATA_FORMAT_PT_EXTERNAL_SETTINGS
        assert contributor_data_sources[0]['id'] is not None
        assert contributor_created['preprocesses'][0]['params']['target_data_source_id'] == \
               contributor_data_sources[0]['id']

    def test_preprocess_enabled_by_default(self, contributor):
        self.add_preprocess_to_contributor({
            "id": "headsign_short_name",
            "type": "HeadsignShortName",
            "sequence": 0,
            "data_source_ids": []
        }, contributor['id'])
        preprocesses = self.json_to_dict(
            self.get('/contributors/{}/preprocesses'.format(contributor['id']))
        )['preprocesses']
        assert len(preprocesses) == 1
        preprocess = preprocesses[0]
        assert preprocess['enabled'] == True

    @pytest.mark.parametrize("enabled", [
        True,
        False
    ])
    def test_preprocess_enabled_specified(self, contributor, enabled):
        self.add_preprocess_to_contributor({
            "id": "headsign_short_name",
            "type": "HeadsignShortName",
            "sequence": 0,
            "data_source_ids": [],
            "enabled": enabled
        }, contributor['id'])
        preprocess = self.json_to_dict(
            self.get('/contributors/{}/preprocesses'.format(contributor['id']))
        )['preprocesses'][0]
        assert preprocess['enabled'] == enabled
