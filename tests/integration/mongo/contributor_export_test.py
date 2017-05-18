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
from tests.utils import to_json, post

def test_contributor_export_contributor_not_found(app):
    raw = post(app, '/contributors/toto/actions/export', {})
    assert raw.status_code == 404
    r = to_json(raw)
    assert 'error' in r
    assert r.get('error') == 'Contributor not found'


def test_contributor_exportd(app):
    raw = post(app, '/contributors', '{"id": "id_test", "name":"name_test", "data_prefix":"AAA"}')
    assert raw.status_code == 201

    raw = post(app, '/contributors/id_test/actions/export', {})
    assert raw.status_code == 201
    r = to_json(raw)
    assert 'job' in r
    job = r.get('job')
    assert job.get('action_type') == 'contributor_export'

    raw_job = app.get('/jobs')
    assert raw_job.status_code == 200
    r_jobs = to_json(raw_job)
    assert len(r_jobs['jobs']) == 1
    assert r_jobs.get('jobs')[0]['id'] == job['id']

    raw_job = app.get('/jobs/{}'.format(job['id']))
    assert raw_job.status_code == 200
    r_jobs = to_json(raw_job)
    assert len(r_jobs['jobs']) == 1
    assert r_jobs.get('jobs')[0]['id'] == job['id']

    raw_job = app.get('/jobs/toto')
    assert raw_job.status_code == 404
