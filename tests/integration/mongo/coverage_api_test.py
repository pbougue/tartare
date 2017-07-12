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
from tests.integration.test_mechanism import TartareFixture
import pytest
import tartare

class TestCoverageApi(TartareFixture):
    def test_get_coverage_empty_success(self):
        raw = self.get('/coverages')
        assert raw.status_code == 200
        raw = self.get('/coverages/')
        assert raw.status_code == 200
        r = self.to_json(raw)
        assert len(r["coverages"]) == 0

    def test_get_coverage_non_exist(self):
        raw = self.get('/coverages/id_test')
        assert raw.status_code == 404
        r = self.to_json(raw)
        assert 'message' in r

    def test_add_coverage_returns_success(self):
        raw = self.post('/coverages', '{"id": "id_test", "name":"name_test"}')
        assert raw.status_code == 201
        raw = self.get('/coverages')
        r = self.to_json(raw)

        assert len(r["coverages"]) == 1
        assert isinstance(r["coverages"], list)
        coverage = r["coverages"][0]
        assert coverage["id"] == "id_test"
        assert coverage["name"] == "name_test"

    def test_add_coverage_no_id(self):
        raw = self.post('/coverages', '{"name": "name_test"}')
        r = self.to_json(raw)
        assert 'error' in r
        assert raw.status_code == 400
        raw = self.get('/coverages')
        r = self.to_json(raw)
        assert len(r["coverages"]) == 0

    def test_add_coverage_no_name(self):
        raw = self.post('/coverages', '{"id": "id_test"}')
        r = self.to_json(raw)
        assert 'error' in r
        assert raw.status_code == 400
        raw = self.get('/coverages')
        r = self.to_json(raw)
        assert len(r["coverages"]) == 0

    def test_add_coverage_with_name(self):
        raw = self.post('/coverages',
                   '{"id": "id_test", "name": "name of the coverage"}')
        assert raw.status_code == 201
        raw = self.get('/coverages')
        r = self.to_json(raw)
        assert len(r["coverages"]) == 1
        assert isinstance(r["coverages"], list)
        assert r["coverages"][0]["id"] == "id_test"
        assert r["coverages"][0]["name"] == "name of the coverage"

    def test_add_coverage_with_pre_env(self):
        raw = self.post('/coverages',
                   '''{"id": "id_test", "name": "name of the coverage",
                   "environments" : {"preproduction": {"name": "pre"}}}''')
        assert raw.status_code == 201
        raw = self.get('/coverages')
        r = self.to_json(raw)
        assert len(r["coverages"]) == 1
        assert isinstance(r["coverages"], list)
        coverage = r["coverages"][0]
        assert coverage["id"] == "id_test"
        assert coverage["name"] == "name of the coverage"
        assert 'environments' in coverage
        assert 'production' not in coverage['environments']
        assert 'preproduction' in coverage['environments']
        assert coverage['environments']['preproduction']['name'] == 'pre'

    def test_add_coverage_with_no_env(self):
        raw = self.post('/coverages',
                '''{"id": "id_test", "name": "name of the coverage",
                    "environments" : {"notvalidenv": {"name": "pre", "tyr_url": "http://foo.bar/"}}}''')

        assert raw.status_code == 400
        r = self.to_json(raw)
        assert 'error' in r
        assert 'Unknown field name notvalidenv' in r['error']['environments']['_schema']

    def test_add_coverage_with_all_env(self):
        raw = self.post('/coverages',
                        '''{"id": "id_test", "name": "name of the coverage",
                        "environments" : {
                        "preproduction": {"name": "pre"},
                        "production": {"name": "prod"},
                        "integration": {"name": "sim"}
                        }}''')
        assert raw.status_code == 201
        raw = self.get('/coverages')
        r = self.to_json(raw)
        assert len(r["coverages"]) == 1
        assert isinstance(r["coverages"], list)
        coverage = r["coverages"][0]
        assert coverage["id"] == "id_test"
        assert coverage["name"] == "name of the coverage"
        assert 'environments' in coverage
        assert 'production' in coverage['environments']
        assert 'preproduction' in coverage['environments']
        assert 'integration' in coverage['environments']
        assert coverage['environments']['preproduction']['name'] == 'pre'
        assert coverage['environments']['production']['name'] == 'prod'
        assert coverage['environments']['integration']['name'] == 'sim'

    def test_patch_simple_coverage(self):
        raw = self.post('/coverages',
                        '''{"id": "id_test", "name": "name of the coverage"}''')
        assert raw.status_code == 201
        raw = self.get('/coverages')
        r = self.to_json(raw)
        assert len(r["coverages"]) == 1
        assert isinstance(r["coverages"], list)
        assert r["coverages"][0]["id"] == "id_test"
        assert r["coverages"][0]["name"] == "name of the coverage"

        raw = self.patch('/coverages/id_test', '{"name": "new name"}')
        assert raw.status_code == 200
        r = self.to_json(raw)
        assert r["coverages"][0]["id"] == "id_test"
        assert r["coverages"][0]["name"] == "new name"

    def test_delete_coverage_returns_success(self):
        raw = self.get('/coverages/id_test')
        assert raw.status_code == 404

        raw = self.post('/coverages', '{"id": "id_test", "name": "name_test"}')
        assert raw.status_code == 201
        raw = self.delete('/coverages/id_test')
        assert raw.status_code == 204
        raw = self.get('/coverages/id_test')
        assert raw.status_code == 404

        raw = self.post('/coverages', '{"id": "id_test2", "name": "name_test2"}')
        assert raw.status_code == 201
        raw = self.get('/coverages')
        r = self.to_json(raw)
        assert len(r["coverages"]) == 1

    def test_update_coverage_returns_success_status(self):
        raw = self.post('/coverages', '{"id": "id_test", "name": "name_test"}')
        assert raw.status_code == 201

        raw = self.patch('/coverages/id_test', '{"name": "new_name_test"}')
        r = self.to_json(raw)

        assert raw.status_code == 200
        assert r["coverages"][0]['id'] == "id_test"
        assert r["coverages"][0]['name'] == "new_name_test"

    def test_update_unknown_coverage(self):
        raw = self.patch('/coverages/unknown', '{"name": "new_name_test"}')
        r = self.to_json(raw)
        assert 'message' in r
        assert raw.status_code == 404

    def test_update_id_impossible(self):
        """It should not be possible to update the id of an object"""
        raw = self.post('/coverages', '{"id": "id_test", "name": "name_test"}')
        assert raw.status_code == 201
        raw = self.patch('/coverages/id_test', '{"id": "bob"}')
        r = self.to_json(raw)
        assert 'error' in r
        assert raw.status_code == 400

    def test_update_coverage_forbid_unkown_field(self):
        raw = self.post('/coverages', '{"id": "id_test", "name": "name_test"}')
        assert raw.status_code == 201

        raw = self.patch('/coverages/id_test', '{"name": "new_name_test", "foo": "bar"}')
        r = self.to_json(raw)

        assert raw.status_code == 400
        assert 'error' in r

    def test_update_coverage_forbid_unkown_environments_type(self):
        raw = self.post('/coverages', '{"id": "id_test", "name": "name_test"}')
        assert raw.status_code == 201

        raw = self.patch('/coverages/id_test', '{"name": "new_name_test", "environments": '
                                               '{"integration": {"name": "bar"}}}')
        assert raw.status_code == 200

        raw = self.patch('/coverages/id_test', '{"name": "new_name_test", "environments": {"bar": {"name": "bar"}}}')
        assert raw.status_code == 400
        r = self.to_json(raw)
        assert 'error' in r

    def test_update_coverage_env(self):
        raw = self.post('/coverages', '{"id": "id_test", "name": "name_test"}')
        assert raw.status_code == 201

        raw = self.patch('/coverages/id_test',
                         '''{"environments" : {
                         "preproduction": {"name": "pre"},
                         "production": null
                        }}''')

        assert raw.status_code == 200
        raw = self.get('/coverages')
        r = self.to_json(raw)
        assert len(r["coverages"]) == 1
        assert isinstance(r["coverages"], list)
        coverage = r["coverages"][0]
        assert coverage["id"] == "id_test"
        assert coverage["name"] == "name_test"
        assert 'environments' in coverage
        assert 'production' not in coverage['environments']
        assert 'preproduction' in coverage['environments']
        assert coverage['environments']['preproduction']['name'] == 'pre'

        raw = self.patch('/coverages/id_test',
                         '''{"environments" : {
                         "preproduction": {"publication_platform":  [ { "options": { "authent": { "username": "test" }, "directory": "/" }}]},
                         "production": null
                        }}''')
        assert raw.status_code == 400
        r = self.to_json(raw)
        assert 'error' in r

    @pytest.mark.parametrize("license_url,license_name,expected_status_code", [
        ('http://license.org/mycompany', 'my license', 201),
        ('http://license.org/othercompany', 'my license full name', 201),
        ('http://license.org/othercompany', None, 400),
        (None, 'my license full name', 400),
        (None, None, 201),
    ])
    def test_post_with_license(self, license_url, license_name, expected_status_code):
        coverage = {
            "id": "id_test",
            "name": "name_test"
        }
        if license_name or license_url:
            coverage['license'] = {
                "url": license_url,
                "name": license_name
            }
        response = self.post('/coverages', self.dict_to_json(coverage))
        assert response.status_code == expected_status_code, print(response)
        if expected_status_code == 201:
            coverage_raw = self.get('/coverages/{cid}'.format(cid=coverage['id']))
            coverage_from_api = self.to_json(coverage_raw)['coverages'][0]

            with tartare.app.app_context():
                expected_url = license_url if license_url else tartare.app.config.get('DEFAULT_LICENSE_URL')
                expected_name = license_name if license_name else tartare.app.config.get('DEFAULT_LICENSE_NAME')
                assert coverage_from_api['license']['url'] == expected_url
                assert coverage_from_api['license']['name'] == expected_name

    def test_add_coverage_with_unknown_contributor(self):
        raw = self.post('/coverages',
                        '{"id": "id_test", "name": "name of the coverage", "contributors": ["unknown"]}')
        assert raw.status_code == 400
        r = self.to_json(raw)
        assert r['error'] == 'Contributor unknown not found.'

    def test_add_coverage_with_existing_contributor(self, contributor):
        raw = self.post('/coverages',
                        '{"id": "id_test", "name": "name of the coverage", "contributors": ["id_test"]}')
        assert raw.status_code == 201
        r = self.to_json(raw)
        assert len(r["coverages"][0]['contributors']) == 1
        assert r["coverages"][0]['contributors'][0] == 'id_test'

    def test_patch_coverage_with_unknown_contributor(self, coverage):
        raw = self.patch('/coverages/{}'.format(coverage['id']), '{"contributors": ["unknown"]}')
        assert raw.status_code == 400
        r = self.to_json(raw)
        assert r['error'] == 'Contributor unknown not found.'

    def test_patch_coverage_with_existing_contributor(self, coverage, contributor):
        raw = self.patch('/coverages/{}'.format(coverage['id']), '{"contributors": ["id_test"]}')
        assert raw.status_code == 200
        r = self.to_json(raw)
        assert len(r["coverages"][0]['contributors']) == 1
        assert r["coverages"][0]['contributors'][0] == 'id_test'
