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
from tartare.core.constants import ACTION_TYPE_COVERAGE_EXPORT
from tests.integration.test_mechanism import TartareFixture
import mock
from tests.utils import mock_requests_post


class TestCoverageExport(TartareFixture):
    def test_coverage_export_coverage_not_found(self):
        raw = self.post('/coverages/toto/actions/export', {})
        assert raw.status_code == 404
        r = self.json_to_dict(raw)
        assert 'error' in r
        assert r.get('error') == "coverage 'toto' not found"

    def test_coverage_export(self):
        raw = self.post('/coverages', '{"id": "id_test", "name":"name_test"}')
        assert raw.status_code == 201

        raw = self.post('/coverages/id_test/actions/export', {})
        assert raw.status_code == 201
        r = self.json_to_dict(raw)
        assert 'job' in r
        job = r.get('job')
        assert job.get('action_type') == ACTION_TYPE_COVERAGE_EXPORT

        raw_job = self.get('/jobs')
        assert raw_job.status_code == 200
        r_jobs = self.json_to_dict(raw_job)
        assert len(r_jobs['jobs']) == 1
        assert r_jobs.get('jobs')[0]['id'] == job['id']

        raw_job = self.get('/jobs/{}'.format(job['id']))
        assert raw_job.status_code == 200
        r_jobs = self.json_to_dict(raw_job)
        assert len(r_jobs['jobs']) == 1
        assert r_jobs.get('jobs')[0]['id'] == job['id']

        raw_job = self.get('/jobs/toto')
        assert raw_job.status_code == 404

    def test_get_coverage_export(self, coverage_export_obj):
        self.post('/coverages', '{"id": "coverage1", "name":"name_test"}')
        self.post('/coverages', '{"id": "coverage2", "name":"name_test"}')

        # Exports for coverage1, one export
        exports = self.get('/coverages/coverage1/exports')
        assert exports.status_code == 200
        r = self.json_to_dict(exports)
        assert len(r["exports"]) == 1
        assert r["exports"][0]["gridfs_id"] == "1234"
        assert r["exports"][0]["coverage_id"] == "coverage1"
        assert r["exports"][0]['validity_period']['start_date'] == '2017-01-01'
        assert r["exports"][0]['validity_period']['end_date'] == '2017-01-30'

        # Exports for coverage2, 0 export
        exports = self.get('/coverages/coverage2/exports')
        assert exports.status_code == 200
        r = self.json_to_dict(exports)
        assert len(r["exports"]) == 0

        # Exports for unknown coverage, 0 export
        exports = self.get('/coverages/bob/exports')
        assert exports.status_code == 404
        r = self.json_to_dict(exports)
        assert r['message'] == 'Object Not Found. You have requested this URI [/coverages/bob/exports] but did you mean /coverages/<string:coverage_id>/exports or /coverages/<string:coverage_id>/actions/export or /coverages/<string:coverage_id>/jobs ?'
        assert r['error'] == "coverage 'bob' not found"
