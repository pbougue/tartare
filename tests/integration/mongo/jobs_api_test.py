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
import datetime

import pytest

from tartare import app
from tartare.core.constants import ACTION_TYPE_CONTRIBUTOR_EXPORT, ACTION_TYPE_COVERAGE_EXPORT
from tartare.core.models import Job
from tartare.helper import datetime_from_string
from tests.integration.test_mechanism import TartareFixture


class TestJobsApi(TartareFixture):
    def test_get_one_job_found(self):
        job_id = 'my_id'
        with app.app_context():
            Job(id=job_id).save()
        job = self.get_job_details(job_id)
        assert job['id'] == job_id

    def test_get_one_job_not_found(self):
        raw = self.get('jobs/{}'.format('unknown'))
        self.assert_failed_call(raw, 404)

    def test_get_job_contributor(self):
        contributor_id = 'cid'
        with app.app_context():
            Job(contributor_id=contributor_id).save()
            Job().save()
            Job(contributor_id=contributor_id).save()
        _, all_jobs = self.get_jobs()
        assert len(all_jobs) == 3
        pagination, contributor_jobs = self.get_jobs(contributor_id=contributor_id)
        assert len(contributor_jobs) == 2
        assert pagination == {'page': 1, 'per_page': 20, 'total': 2}

    def test_get_job_coverage(self):
        coverage_id = 'covid'
        with app.app_context():
            Job(coverage_id=coverage_id).save()
            Job().save()
            Job(coverage_id=coverage_id).save()
        _, all_jobs = self.get_jobs()
        assert len(all_jobs) == 3
        pagination, coverage_jobs = self.get_jobs(coverage_id=coverage_id)
        assert len(coverage_jobs) == 2
        assert pagination == {'page': 1, 'per_page': 20, 'total': 2}

    def test_get_job_with_details(self):
        now = datetime_from_string('2014-04-15 15:37:44 UTC')
        update = now + datetime.timedelta(days=1)
        update2 = now + datetime.timedelta(days=10)
        with app.app_context():
            Job(ACTION_TYPE_CONTRIBUTOR_EXPORT, 'cid1', None, None, 'pending', 'my-step', 'job1-id', now, update, "",
                'dsid').save()
            Job(ACTION_TYPE_COVERAGE_EXPORT, None, 'covid', None, 'failed', 'failed-step', 'job2-id', now, update2,
                "boom",
                'dsid').save()

        _, jobs = self.get_jobs()
        assert len(jobs) == 2

        job1 = self.get_job_details('job1-id')
        assert job1['id'] == 'job1-id'
        assert job1['action_type'] == ACTION_TYPE_CONTRIBUTOR_EXPORT
        assert job1['step'] == 'my-step'
        assert job1['state'] == 'pending'
        assert job1['started_at'] == '2014-04-15T15:37:44+00:00'
        assert job1['updated_at'] == '2014-04-16T15:37:44+00:00'
        assert job1['error_message'] == ''
        assert job1['contributor_id'] == 'cid1'
        assert not job1['coverage_id']
        assert not job1['parent_id']

        job2 = self.get_job_details('job2-id')
        assert job2['id'] == 'job2-id'
        assert job2['action_type'] == ACTION_TYPE_COVERAGE_EXPORT
        assert job2['step'] == 'failed-step'
        assert job2['state'] == 'failed'
        assert job2['started_at'] == '2014-04-15T15:37:44+00:00'
        assert job2['updated_at'] == '2014-04-25T15:37:44+00:00'
        assert job2['error_message'] == 'boom'
        assert job2['coverage_id'] == 'covid'
        assert not job2['contributor_id']
        assert not job2['parent_id']

    def test_get_jobs_sorted_by_updated_date(self):
        with app.app_context():
            Job(id='job-1', updated_at=datetime_from_string('2014-04-15 15:37:44 UTC')).save()
            Job(id='job-2', updated_at=datetime_from_string('2014-04-20 15:37:44 UTC')).save()
            Job(id='job-3', updated_at=datetime_from_string('2014-04-10 15:37:44 UTC')).save()
            Job(id='job-4', updated_at=datetime_from_string('2014-05-01 15:37:44 UTC')).save()

        _, jobs = self.get_jobs()
        assert jobs[0]['id'] == 'job-4'
        assert jobs[1]['id'] == 'job-2'
        assert jobs[2]['id'] == 'job-1'
        assert jobs[3]['id'] == 'job-3'

    def test_get_jobs_paginated(self):
        start = datetime_from_string('2014-04-15 15:37:44 UTC')
        with app.app_context():
            for i in range(1, 30 + 1):
                Job(id='job-{}'.format(i), started_at=start + datetime.timedelta(minutes=i)).save()
        # default pagination
        pagination, jobs = self.get_jobs()
        assert pagination == {'page': 1, 'per_page': 20, 'total': 30}
        assert len(jobs) == 20
        # with page
        pagination, jobs = self.get_jobs(page=2)
        assert pagination == {'page': 2, 'per_page': 20, 'total': 30}
        assert len(jobs) == 10
        # with per_page
        pagination, jobs = self.get_jobs(per_page=5)
        assert pagination == {'page': 1, 'per_page': 5, 'total': 30}
        assert len(jobs) == 5
        # with both
        pagination, jobs = self.get_jobs(page=2, per_page=5)
        assert pagination == {'page': 2, 'per_page': 5, 'total': 30}
        assert len(jobs) == 5
        # sorted by date
        assert [job['id'] for job in jobs] == ['job-25', 'job-24', 'job-23', 'job-22', 'job-21']
        pagination, jobs = self.get_jobs(page=4, per_page=5)
        assert len(jobs) == 5
        assert [job['id'] for job in jobs] == ['job-15', 'job-14', 'job-13', 'job-12', 'job-11']
        # last page with less than per_page elements
        pagination, jobs = self.get_jobs(page=7, per_page=4)
        assert len(jobs) == 4
        pagination, jobs = self.get_jobs(page=8, per_page=4)
        assert len(jobs) == 2
        # page with no elements
        pagination, jobs = self.get_jobs(page=9, per_page=4)
        assert len(jobs) == 0
        assert pagination == {'page': 9, 'per_page': 4, 'total': 30}

    @pytest.mark.parametrize(
        "page,per_page,message", [
            (0, None, 'page should be 1 or more'),
            (-5, 5, 'page should be 1 or more'),
            (1, 0, 'per_page should be 1 or more'),
            (None, -10, 'per_page should be 1 or more'),
            (-1, -2, 'page should be 1 or more'),
        ])
    def test_get_jobs_wrong_pagination(self, page, per_page, message):
        raw = self.get_jobs(page=page, per_page=per_page, check_success=False)
        details = self.assert_failed_call(raw)
        assert details == {'error': message, 'message': 'Invalid arguments'}
