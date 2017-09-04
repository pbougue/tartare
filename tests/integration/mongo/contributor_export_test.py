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
from freezegun import freeze_time

from tests.utils import to_json, post
import pytest

from tests.integration.test_mechanism import TartareFixture


class TestContributorExport(TartareFixture):
    def test_contributor_export_contributor_not_found(self):
        raw = self.post('/contributors/toto/actions/export', {})
        assert raw.status_code == 404
        r = self.to_json(raw)
        assert 'error' in r
        assert r.get('error') == 'Contributor not found: toto'

    def test_contributor_export(self):
        raw = self.post('/contributors', '{"id": "id_test", "name":"name_test", "data_prefix":"AAA"}')
        assert raw.status_code == 201

        raw = self.post('/contributors/id_test/actions/export', {})
        assert raw.status_code == 201
        r = self.to_json(raw)
        assert 'job' in r
        job = r.get('job')
        assert job.get('action_type') == 'contributor_export'

        raw_job = self.get('/jobs')
        assert raw_job.status_code == 200
        r_jobs = self.to_json(raw_job)
        assert len(r_jobs['jobs']) == 1
        assert r_jobs.get('jobs')[0]['id'] == job['id']

        raw_job = self.get('/jobs/{}'.format(job['id']))
        assert raw_job.status_code == 200
        r_jobs = self.to_json(raw_job)
        assert len(r_jobs['jobs']) == 1
        assert r_jobs.get('jobs')[0]['id'] == job['id']

        raw_job = self.get('/jobs/toto')
        assert raw_job.status_code == 404

    def test_contributor_export_find_job_by_contributor(self):
        raw = self.post('/contributors', '{"id": "id_test", "name":"name_test", "data_prefix":"AAA"}')
        assert raw.status_code == 201

        raw = self.post('/contributors/id_test/actions/export', {})
        assert raw.status_code == 201
        r = self.to_json(raw)
        assert 'job' in r
        job = r.get('job')
        assert job.get('action_type') == 'contributor_export'

        raw_job = self.get('/jobs')
        assert raw_job.status_code == 200
        r_jobs = self.to_json(raw_job)
        assert len(r_jobs['jobs']) == 1
        assert r_jobs.get('jobs')[0]['id'] == job['id']

        raw_job = self.get('contributors/id_test/jobs/{}'.format(job['id']))
        assert raw_job.status_code == 200
        r_jobs = self.to_json(raw_job)
        assert len(r_jobs['jobs']) == 1
        assert r_jobs.get('jobs')[0]['id'] == job['id']

    @freeze_time("2015-08-10")
    @pytest.mark.parametrize("method,filename,state,step,error_message", [
        ('http', 'some_archive.zip', 'done', 'save_contributor_export', None),
        ('http', 'unexisting_file.zip', 'failed', 'fetching data', 'HTTP Error 404: Not Found'),
        ('http', 'not_a_zip_file.zip', 'failed', 'fetching data', 'downloaded file from url %url% is not a zip file'),
        ('ftp', 'some_archive.zip', 'done', 'save_contributor_export', None),
        ('ftp', 'unexisting_file.zip', 'failed', 'fetching data',
         """<urlopen error ftp error: URLError('ftp error: error_perm("550 Can\\'t change directory to unexisting_file.zip: No such file or directory",)',)>"""
         ),
        ('ftp', 'not_a_zip_file.zip', 'failed', 'fetching data', 'downloaded file from url %url% is not a zip file')
    ])
    def test_contributor_export_with_http_download(self, init_http_download_server, init_ftp_download_server,
                                                   contributor, method, filename, state, step,
                                                   error_message):
        ip = init_http_download_server.ip_addr if method == 'http' else init_ftp_download_server.ip_addr
        url = "{method}://{ip}/{filename}".format(method=method, ip=ip, filename=filename)
        if error_message and '%url%' in error_message:
            error_message = error_message.replace('%url%', url)
        raw = self.post('/contributors/id_test/data_sources',
                        params='{"name": "bobette", "data_format": "gtfs", "input": {"url": "' + url + '"}}')
        assert raw.status_code == 201

        raw = self.post('/contributors/{}/actions/export'.format(contributor['id']), {})
        assert raw.status_code == 201
        job = to_json(raw).get('job')

        raw_job = self.get(
            'contributors/{contrib_id}/jobs/{job_id}'.format(contrib_id=contributor['id'], job_id=job['id']))
        job = to_json(raw_job)['jobs'][0]
        assert job['state'] == state
        assert job['step'] == step
        if error_message:
            assert job['error_message'] == error_message

    @freeze_time("2015-08-10")
    def test_contributor_export_with_preprocesses_called(self, init_http_download_server, contributor):
        ip = init_http_download_server.ip_addr
        url = "http://{ip}/{filename}".format(ip=ip, filename='some_archive.zip')
        raw = self.post('/contributors/id_test/data_sources',
                        params='{"id": "to_process", "name": "bobette", "data_format": "gtfs", "input": {"url": "' + url + '"}}')
        assert raw.status_code == 201
        raw = self.post('/contributors/id_test/preprocesses',
                        params='{"type":"GtfsAgencyFile","sequence":0,"data_source_ids":["to_process"],"params":{"data":{"agency_id":"112","agency_name":"stif","agency_url":"http://stif.com"}}}')
        assert raw.status_code == 201

        raw = self.post('/contributors/{}/actions/export'.format(contributor['id']), {})
        assert raw.status_code == 201
        job = to_json(raw).get('job')

        raw_job = self.get(
            'contributors/{contrib_id}/jobs/{job_id}'.format(contrib_id=contributor['id'], job_id=job['id']))
        job = to_json(raw_job)['jobs'][0]
        assert job['state'] == 'done', print(job)
