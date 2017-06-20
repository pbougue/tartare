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
import mock
from tests.utils import mock_urlretrieve, mock_requests_post
from tests.integration.test_mechanism import TartareFixture
import json


class TestDataPublisher(TartareFixture):
    def test_publish_unknwon_coverage(self):
        resp = self.post("/coverages/default/environments/production/actions/publish")
        assert resp.status_code == 404
        r = self.to_json(resp)
        assert r['message'] == 'Object Not Found'
        assert r['error'] == 'Coverage not found: default'

    def test_publish_unknwon_environment(self):
        coverage = {
            "contributors": [
                "fr-idf"
            ],
            "environments": {
                "production": {
                    "name": "production",
                    "publication_platforms": [
                        {
                            "name": "navitia",
                            "type": "http",
                            "url": "http://bob/v0/jobs"
                        }
                    ]
                }
            },
            "id": "default",
            "name": "default"
        }
        #Create Coverage
        resp = self.post("/coverages", json.dumps(coverage))
        assert resp.status_code == 201

        #Launch data update
        resp = self.post("/coverages/default/environments/bob/actions/publish")
        assert resp.status_code == 404
        r = self.to_json(resp)
        assert r['message'] == 'Object Not Found'
        assert r['error'] == 'Environment not found: bob'

    def test_publish_coverage_without_export(self):
        coverage = {
            "contributors": [
                "fr-idf"
            ],
            "environments": {
                "production": {
                    "name": "production",
                    "publication_platforms": [
                        {
                            "name": "navitia",
                            "type": "http",
                            "url": "http://bob/v0/jobs"
                        }
                    ]
                }
            },
            "id": "default",
            "name": "default"
        }
        #Create Coverage
        resp = self.post("/coverages", json.dumps(coverage))
        assert resp.status_code == 201

        #Launch data update
        resp = self.post("/coverages/default/environments/production/actions/publish")
        assert resp.status_code == 404
        r = self.to_json(resp)
        assert r['message'] == 'Object Not Found'
        assert r['error'] == 'Coverage default without export.'

    @mock.patch('urllib.request.urlretrieve', side_effect=mock_urlretrieve)
    def test_publish_ok(self, urlretrieve_func):
        contributor = {
            "id": "fr-idf",
            "name": "fr idf",
            "data_prefix": "AAA",
            "data_sources": [
                {
                    "name": "gtfs data",
                    "data_format": "gtfs",
                    "input": {
                        "type": "url",
                        "url": "bob"
                    }
                }
            ]
        }
        coverage = {
            "contributors": [
                "fr-idf"
            ],
            "environments": {
                "production": {
                    "name": "production",
                    "publication_platforms": [
                        {
                            "name": "navitia",
                            "type": "http",
                            "url": "http://bob/v0/jobs"
                        }
                    ]
                }
            },
            "id": "default",
            "name": "default"
        }
        # Create Contributor
        resp = self.post("/contributors", json.dumps(contributor))
        assert resp.status_code == 201

        #Create Coverage
        resp = self.post("/coverages", json.dumps(coverage))
        assert resp.status_code == 201

        # Launch contributor export
        resp = self.post("/contributors/fr-idf/actions/export")
        assert resp.status_code == 201

        # List contributor export
        r = self.to_json(self.get("/contributors/fr-idf/exports"))
        exports = r["exports"]
        assert len(exports) == 1
        assert exports[0]["validity_period"]["start_date"] == "2015-03-25"
        assert exports[0]["validity_period"]["end_date"] == "2015-08-26"

        assert exports[0]["gridfs_id"]
        data_sources = exports[0]["data_sources"]
        assert len(data_sources) == 1
        assert data_sources[0]["validity_period"]

        #Launch coverage export
        resp = self.post("/coverages/default/actions/export")
        assert resp.status_code == 201

        # List coverage export
        r = self.to_json(self.get("/coverages/default/exports"))
        exports = r["exports"]
        assert len(exports) == 1
        assert exports[0]["validity_period"]["start_date"] == "2015-03-25"
        assert exports[0]["validity_period"]["end_date"] == "2015-08-26"
        assert exports[0]["gridfs_id"]
        contributors = exports[0]["contributors"]
        assert len(contributors) == 1
        assert contributors[0]["validity_period"]
        assert len(contributors[0]["data_sources"]) == 1
        assert contributors[0]["data_sources"][0]["validity_period"]

        #Launch data update
        with mock.patch('requests.post', mock_requests_post):
            resp = self.post("/coverages/default/environments/production/actions/publish")
            assert resp.status_code == 200
