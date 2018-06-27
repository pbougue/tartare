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

import pytest

from tartare import app
from tartare.core.constants import DATA_FORMAT_OSM_FILE, DATA_FORMAT_BANO_FILE, ACTION_TYPE_CONTRIBUTOR_EXPORT, \
    ACTION_TYPE_DATA_SOURCE_FETCH, JOB_STATUS_FAILED
from tartare.core.gridfs_handler import GridFsHandler
from tests.integration.test_mechanism import TartareFixture


class TestContributorExport(TartareFixture):
    def test_contributor_export_contributor_not_found(self):
        raw = self.post('/contributors/toto/actions/export', {})
        assert raw.status_code == 404
        r = self.json_to_dict(raw)
        assert 'error' in r
        assert r.get('error') == "contributor 'toto' not found"

    def test_get_contributor_export_contributor_not_found(self):
        raw = self.get('/contributors/toto/actions/export')
        r = self.assert_failed_call(raw, 404)
        assert r.get('error') == "contributor 'toto' not found"

    def test_contributor_export(self):
        raw = self.post('/contributors', '{"id": "id_test", "name":"name_test", "data_prefix":"AAA"}')
        assert raw.status_code == 201

        raw = self.post('/contributors/id_test/actions/export', {})
        assert raw.status_code == 201
        r = self.json_to_dict(raw)
        assert 'job' in r
        job = r.get('job')
        assert job.get('action_type') == ACTION_TYPE_CONTRIBUTOR_EXPORT

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

    def test_contributor_export_find_job_by_contributor(self):
        raw = self.post('/contributors', '{"id": "id_test", "name":"name_test", "data_prefix":"AAA"}')
        assert raw.status_code == 201

        raw = self.post('/contributors/id_test/actions/export', {})
        assert raw.status_code == 201
        r = self.json_to_dict(raw)
        assert 'job' in r
        job = r.get('job')
        assert job.get('action_type') == ACTION_TYPE_CONTRIBUTOR_EXPORT

        raw_job = self.get('/jobs')
        assert raw_job.status_code == 200
        r_jobs = self.json_to_dict(raw_job)
        assert len(r_jobs['jobs']) == 1
        assert r_jobs.get('jobs')[0]['id'] == job['id']

        raw_job = self.get('contributors/id_test/jobs/{}'.format(job['id']))
        assert raw_job.status_code == 200
        r_jobs = self.json_to_dict(raw_job)
        assert len(r_jobs['jobs']) == 1
        assert r_jobs.get('jobs')[0]['id'] == job['id']

    @pytest.mark.parametrize("method,filename,state,step,error_message", [
        ('http', 'some_archive.zip', 'done', 'save_contributor_export', None),
        ('http', 'unexisting_file.zip', 'failed', 'fetching data',
         'error during download of file: HTTP Error 404: Not Found'),
        ('http', 'not_a_zip_file.zip', 'failed', 'fetching data', 'downloaded file from url %url% is not a zip file'),
        ('ftp', 'some_archive.zip', 'done', 'save_contributor_export', None),
        ('ftp', 'unexisting_file.zip', 'failed', 'fetching data',
         """error during download of file: <urlopen error ftp error: URLError('ftp error: error_perm("550 Can\\'t change directory to unexisting_file.zip: No such file or directory",)',)>"""),
        ('ftp', 'not_a_zip_file.zip', 'failed', 'fetching data', 'downloaded file from url %url% is not a zip file')
    ])
    def test_contributor_export_with_http_download(self, init_http_download_server, init_ftp_download_server,
                                                   contributor, method, filename, state, step,
                                                   error_message):
        ip = init_http_download_server.ip_addr if method == 'http' else init_ftp_download_server.ip_addr
        url = self.format_url(method=method, ip=ip, filename=filename)
        if error_message and '%url%' in error_message:
            error_message = error_message.replace('%url%', url)

        contributor['data_sources'].append({
            "name": "bobette",
            "data_format": "gtfs",
            "input": {
                "type": "auto",
                "url": url,
                "frequency": {
                    "type": "daily",
                    "hour_of_day": 20
                }}
        })
        raw = self.put('/contributors/id_test', params=self.dict_to_json(contributor))
        self.assert_sucessful_call(raw)

        resp = self.contributor_export(contributor['id'], check_done=False)
        job = self.get_job_from_export_response(resp)
        assert job['state'] == state
        assert job['step'] == step
        if error_message:
            assert job['error_message'] == error_message

    def test_contributor_export_with_preprocesses_called(self, init_http_download_server, contributor):
        url = self.format_url(ip=init_http_download_server.ip_addr, filename='some_archive.zip')

        contributor['data_sources'].append({
            "id": "to_process",
            "name": "bobette",
            "data_format": "gtfs",
            "export_data_source_id": "export_id",
            "input": {
                "type": "auto",
                "url": url,
                "frequency": {
                    "type": "daily",
                    "hour_of_day": 20
                }}
        })
        contributor['preprocesses'].append({
            "type": "GtfsAgencyFile",
            "sequence": 0,
            "data_source_ids": ["to_process"],
            "params": {"data": {
                "agency_id": "112",
                "agency_name": "stif",
                "agency_url": "http://stif.com"
            }}
        })
        raw = self.put('/contributors/id_test', params=self.dict_to_json(contributor))
        self.assert_sucessful_call(raw)

        job = self.contributor_export(contributor['id'])
        assert job['state'] == 'done', print(job)

    def test_contributor_export_generates_jobs(self, init_http_download_server):
        contrib_id = 'cid'
        ds_id = 'dsid'
        self.init_contributor(contrib_id, ds_id, self.format_url(init_http_download_server.ip_addr, 'some_archive.zip'))
        self.contributor_export(contrib_id)
        jobs = self.json_to_dict(self.get('/jobs'))['jobs']
        job_export = self.filter_job_of_action_type(jobs, ACTION_TYPE_CONTRIBUTOR_EXPORT)
        assert job_export['contributor_id'] == contrib_id
        assert job_export['updated_at'] is not None
        assert job_export['started_at'] is not None
        assert job_export['step'] == 'save_contributor_export'
        assert job_export['state'] == 'done'
        assert job_export['coverage_id'] is None

    def test_contributor_export_no_data_set(self):
        self.init_contributor('cid', 'dsid', manual=True)
        resp = self.contributor_export('cid', check_done=False)
        job = self.get_job_from_export_response(resp)
        assert job['step'] == 'building preprocesses context'
        assert job['state'] == JOB_STATUS_FAILED
        assert job['error_message'] == "data source 'dsid' has no data sets"
