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

from tests.integration.test_mechanism import TartareFixture


class TestAutomaticUpdate(TartareFixture):
    def __run_automatic_update(self):
        raw = self.post('/actions/automatic_update?current_date=2015-08-10')
        self.assert_sucessful_call(raw, 204)
        raw = self.get('/jobs')
        self.assert_sucessful_call(raw, 200)
        return self.to_json(raw)['jobs']

    def test_automatic_update_nothing_done(self):
        jobs = self.__run_automatic_update()
        assert jobs == []

    def __create_contributor(self, ip):
        contributor = {
            "id": "auto_update_contrib",
            "name": "auto_update_contrib",
            "data_prefix": "auto_update_contrib_prefix",
            "data_sources": [
                {
                    "id": "ds_auto_update_contrib",
                    "name": "ds_auto_update_contrib",
                    "input": {
                        "type": "url",
                        "url": self.format_url(ip, 'some_archive.zip')
                    }
                }
            ]
        }
        raw = self.post('/contributors', json.dumps(contributor))
        self.assert_sucessful_call(raw, 201)

    def test_automatic_update_one_contributor(self, init_http_download_server):
        self.__create_contributor(init_http_download_server.ip_addr)
        jobs = self.__run_automatic_update()
        assert len(jobs) == 1
        job = jobs[0]
        assert job['state'] == 'done'
        assert job['error_message'] == ''
        assert job['coverage_id'] is None
        assert job['started_at'] is not None
        assert job['updated_at'] is not None
        assert job['contributor_id'] == 'auto_update_contrib'
        assert job['action_type'] == 'automatic_update_contributor_export'

    def __create_coverage(self, contributor_id):
        coverage = {
            'id': 'auto_update_coverage',
            'name': 'auto_update_coverage',
            'contributors': [contributor_id],
        }
        raw = self.post('coverages', json.dumps(coverage))
        self.assert_sucessful_call(raw, 201)

    def test_automatic_update_one_contributor_and_coverage(self, init_http_download_server):
        self.__create_contributor(init_http_download_server.ip_addr)
        self.__create_coverage('auto_update_contrib')
        jobs = self.__run_automatic_update()
        assert len(jobs) == 2
        for job in jobs:
            if job['action_type'] == 'automatic_update_contributor_export':
                assert job['state'] == 'done'
                assert job['step'] == 'save_contributor_export'
                assert job['error_message'] == ''
                assert job['coverage_id'] is None
                assert job['started_at'] is not None
                assert job['updated_at'] is not None
                assert job['contributor_id'] == 'auto_update_contrib'
                assert job['action_type'] == 'automatic_update_contributor_export'
            elif job['action_type'] == 'automatic_update_coverage_export':
                assert job['state'] == 'done'
                assert job['step'] == 'save_coverage_export'
                assert job['error_message'] == ''
                assert job['coverage_id'] == 'auto_update_coverage'
                assert job['started_at'] is not None
                assert job['updated_at'] is not None
                assert job['contributor_id'] is None
                assert job['action_type'] == 'automatic_update_coverage_export'
            else:
                assert False, print('action type should be either {} or {}, found {}'.format(
                    'automatic_update_coverage_export', 'automatic_update_contributor_export', job['action_type']
                ))
