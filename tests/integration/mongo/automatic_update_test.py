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

from tartare import app, mongo
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

    def __create_contributor(self, ip, id="auto_update_contrib"):
        contributor = {
            "id": id,
            "name": id,
            "data_prefix": id + "_prefix",
            "data_sources": [
                {
                    "id": "ds_" + id,
                    "name": "ds_" + id,
                    "input": {
                        "type": "url",
                        "url": self.format_url(ip, 'some_archive.zip')
                    }
                }
            ]
        }
        raw = self.post('/contributors', json.dumps(contributor))
        self.assert_sucessful_call(raw, 201)

    def __assert_job_is_automatic_update_contributor_export(self, job):
        assert job['state'] == 'done'
        assert job['step'] == 'save_contributor_export'
        assert job['error_message'] == ''
        assert job['coverage_id'] is None
        assert job['started_at'] is not None
        assert job['updated_at'] is not None
        assert job['contributor_id'] == 'auto_update_contrib'
        assert job['action_type'] == 'automatic_update_contributor_export'

    def __assert_job_is_automatic_update_contributor_export_unchanged(self, job):
        assert job['state'] == 'done'
        assert job['step'] == 'fetching data'
        assert job['error_message'] == ''
        assert job['coverage_id'] is None
        assert job['started_at'] is not None
        assert job['updated_at'] is not None
        assert job['contributor_id'] == 'auto_update_contrib'
        assert job['action_type'] == 'automatic_update_contributor_export'

    def __assert_job_is_automatic_update_coverage_export(self, job):
        assert job['state'] == 'done'
        assert job['step'] == 'save_coverage_export'
        assert job['error_message'] == ''
        assert job['coverage_id'] == 'auto_update_coverage'
        assert job['started_at'] is not None
        assert job['updated_at'] is not None
        assert job['contributor_id'] is None
        assert job['action_type'] == 'automatic_update_coverage_export'

    def test_automatic_update_one_contributor(self, init_http_download_server):
        self.__create_contributor(init_http_download_server.ip_addr)
        jobs = self.__run_automatic_update()
        assert len(jobs) == 1
        job = jobs[0]
        self.__assert_job_is_automatic_update_contributor_export(job)

    def __create_coverage(self, contributor_ids, coverage_id='auto_update_coverage'):
        coverage = {
            'id': coverage_id,
            'name': coverage_id,
            'contributors': contributor_ids,
        }
        raw = self.post('coverages', json.dumps(coverage))
        self.assert_sucessful_call(raw, 201)

    def test_automatic_update_one_contributor_and_coverage(self, init_http_download_server):
        self.__create_contributor(init_http_download_server.ip_addr)
        self.__create_coverage(['auto_update_contrib'])
        jobs = self.__run_automatic_update()
        assert len(jobs) == 2
        for job in jobs:
            if job['action_type'] == 'automatic_update_contributor_export':
                self.__assert_job_is_automatic_update_contributor_export(job)
            elif job['action_type'] == 'automatic_update_coverage_export':
                self.__assert_job_is_automatic_update_coverage_export(job)
            else:
                assert False, print('action type should be either {} or {}, found {}'.format(
                    'automatic_update_coverage_export', 'automatic_update_contributor_export', job['action_type']
                ))

    def test_automatic_update_twice_one_contributor_and_coverage(self, init_http_download_server):
        self.__create_contributor(init_http_download_server.ip_addr)
        self.__create_coverage(['auto_update_contrib'])
        jobs_first_run = self.__run_automatic_update()
        jobs_second_run = self.__run_automatic_update()
        assert len(jobs_first_run) == 2
        assert len(jobs_second_run) == 3
        for job in jobs_second_run:
            if job['action_type'] == 'automatic_update_contributor_export':
                if job['step'] == 'save_contributor_export':
                    self.__assert_job_is_automatic_update_contributor_export(job)
                else:
                    self.__assert_job_is_automatic_update_contributor_export_unchanged(job)
            elif job['action_type'] == 'automatic_update_coverage_export':
                self.__assert_job_is_automatic_update_coverage_export(job)
            else:
                assert False, print('action type should be either {} or {}, found {}'.format(
                    'automatic_update_coverage_export', 'automatic_update_contributor_export', job['action_type']
                ))

    #
    # associations contributors ---> coverages:
    #
    # c1 ----> cA
    #       /
    # c2 ---
    # c3 ----> cB
    # c4 ----> x        (x == nothing)
    # x  ----> cC
    def test_automatic_update_twice_multi_contributor_and_multi_coverage(self, init_http_download_server):
        contributors = ['c1', 'c2', 'c3', 'c4']
        coverages = {'cA': ['c1', 'c2'], 'cB': ['c3'], 'cC': []}
        for contributor in contributors:
            self.__create_contributor(init_http_download_server.ip_addr, contributor)
        for cov, contribs in coverages.items():
            self.__create_coverage(contribs, cov)
        jobs_first_run = self.__run_automatic_update()
        assert len(jobs_first_run) == 6
        contributor_export_jobs = list(
            filter(lambda job: job['action_type'] == 'automatic_update_contributor_export' and job['step'] == 'save_contributor_export', jobs_first_run))
        coverage_export_jobs = list(
            filter(lambda job: job['action_type'] == 'automatic_update_coverage_export' and job['step'] == 'save_coverage_export', jobs_first_run))
        assert len(contributor_export_jobs) == 4  # all contributor_export are launched
        assert len(coverage_export_jobs) == 2  # cA and cB launched (not cC because no contributors attached)

        # remove old jobs
        with app.app_context():
            mongo.db['jobs'].delete_many({})

        # update c1 data source
        self.patch('/contributors/{}/data_sources/{}'.format('c1', 'ds_c1'),
                   json.dumps({'input': {'url': self.format_url(init_http_download_server.ip_addr, 'sample_1.zip')}}))
        jobs_second_run = self.__run_automatic_update()
        contributor_export_jobs = list(
            filter(lambda job: job['action_type'] == 'automatic_update_contributor_export', jobs_second_run))
        coverage_export_jobs = list(
            filter(lambda job: job['action_type'] == 'automatic_update_coverage_export', jobs_second_run))
        assert len(contributor_export_jobs) == 4  # all contributor_export are launched
        assert len(coverage_export_jobs) == 1  # cA launched because c1 was updated
        contributor_export_unchanged_jobs = list(
            filter(lambda job: job['step'] == 'fetching data', contributor_export_jobs))
        # when data source url does not change it will not generate a coverage export
        assert len(contributor_export_unchanged_jobs) == 3

