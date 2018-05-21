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
from datetime import datetime, timedelta

from tartare import app
from tartare.core.constants import ACTION_TYPE_CONTRIBUTOR_EXPORT, ACTION_TYPE_COVERAGE_EXPORT, \
    ACTION_TYPE_AUTO_COVERAGE_EXPORT, ACTION_TYPE_AUTO_CONTRIBUTOR_EXPORT, JOB_STATUS_RUNNING, JOB_STATUS_PENDING
from tartare.core.models import Job
from tests.integration.test_mechanism import TartareFixture


class TestJobs(TartareFixture):
    def test_cancel_pending_updated_before(self):
        with app.app_context():
            job1 = Job(ACTION_TYPE_CONTRIBUTOR_EXPORT, 'cid1', None, None, 'pending', 'my-step', 'job1-id',
                       datetime.now() - timedelta(hours=10), datetime.now() - timedelta(hours=8))

            job2 = Job(ACTION_TYPE_COVERAGE_EXPORT, None, 'covida', None, 'done', 'my-step', 'job2-id',
                       datetime.now() - timedelta(hours=10), datetime.now() - timedelta(hours=8))

            job3 = Job(ACTION_TYPE_AUTO_COVERAGE_EXPORT, 'covidb', None, None, 'running', 'my-step', 'job3-id',
                       datetime.now() - timedelta(hours=15), datetime.now() - timedelta(hours=6))

            job4 = Job(ACTION_TYPE_AUTO_CONTRIBUTOR_EXPORT, 'cid2', None, None, 'failed', 'my-step', 'job4-id',
                       datetime.now() - timedelta(hours=10), datetime.now() - timedelta(hours=8))

            job5 = Job(ACTION_TYPE_CONTRIBUTOR_EXPORT, 'cid3', None, None, 'running', 'my-step', 'job5-id',
                       datetime.now() - timedelta(hours=2), datetime.now())
            jobs = [
                job1, job2, job3, job4, job5
            ]

            for job in jobs:
                job.save()

            cancelled_jobs = Job.cancel_pending_updated_before(4, [JOB_STATUS_RUNNING, JOB_STATUS_PENDING])
            assert len(cancelled_jobs) == 2
            assert [job.id for job in cancelled_jobs] == ['job1-id', 'job3-id']
