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

from tartare.core.models import Job
from tartare.core.mailer import Mailer
from tartare import app
import datetime


class TestMailer():
    def _same_list(self, list1, list2):
        list1.sort()
        list2.sort()
        for index, value in enumerate(list1):
            assert value == list2[index]

    def test_contributor_export(self):
        now = datetime.datetime(2017, 5, 6, 16, 29, 43, tzinfo=datetime.timezone.utc)
        with app.app_context():
            job = Job('contributor_export', contributor_id='fr-idf', state='failed',
                      id='8422cadb-4e68-4142-be27-f2ec32af49a3',
                      started_at=now)
            job.save()
            mailer = Mailer({}, False)
            t = mailer.get_message(Job.get(job_id=job.id))
            result = t.split('\n')

            excepted = [
                'Problem Tartare',
                '',
                '',
                'Start execution : {}'.format(now.isoformat(sep=' ')),
                'End execution : None',
                'Action type: contributor_export',
                'Job: 8422cadb-4e68-4142-be27-f2ec32af49a3',
                'Step: None',
                'Contributor: fr-idf',
                'Error Message : ',
                '',
                '',
                '===========================================================================',
                'Automatic email from Tartare',
                '==========================================================================='
            ]
        self._same_list(excepted, result)

    def test_coverage_export(self):
        now = datetime.datetime(2017, 5, 6, 16, 29, 43, tzinfo=datetime.timezone.utc)
        with app.app_context():
            job = Job('coverage_export', coverage_id='fr-idf', state='failed',
                      id='8422cadb-4e68-4142-be27-f2ec32af49a3',
                      started_at=now)
            job.save()
            mailer = Mailer({}, False)
            t = mailer.get_message(Job.get(job_id=job.id))
            result = t.split('\n')
            excepted = [
                'Problem Tartare',
                '',
                '',
                'Start execution : {}'.format(now.isoformat(sep=' ')),
                'End execution : None',
                'Action type: coverage_export',
                'Job: 8422cadb-4e68-4142-be27-f2ec32af49a3',
                'Step: None',
                'Coverage: fr-idf',
                'Error Message : ',
                '',
                '',
                '===========================================================================',
                'Automatic email from Tartare',
                '==========================================================================='
            ]
            self._same_list(excepted, result)

    def test_automatic_update(self):
        now = datetime.datetime(2017, 5, 6, 16, 29, 43, tzinfo=datetime.timezone.utc)
        with app.app_context():
            job = Job('automatic_update', contributor_id='fr-idf', state='failed',
                      id='8422cadb-4e68-4142-be27-f2ec32af49a3',
                      started_at=now)
            job.save()
            mailer = Mailer({}, False)
            t = mailer.get_message(Job.get(job_id=job.id))
            result = t.split('\n')
            excepted = [
                'Problem Tartare',
                '',
                '',
                'Start execution : {}'.format(now.isoformat(sep=' ')),
                'End execution : None',
                'Action type: automatic_update',
                'Job: 8422cadb-4e68-4142-be27-f2ec32af49a3',
                'Step: None',
                'Contributor: fr-idf',
                'Error Message : ',
                '',
                '',
                '===========================================================================',
                'Automatic email from Tartare',
                '==========================================================================='
            ]
            self._same_list(excepted, result)
