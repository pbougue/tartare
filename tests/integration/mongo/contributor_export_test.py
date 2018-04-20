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
from time import sleep

import pytest

from tartare import app
from tartare.core.constants import DATA_FORMAT_OSM_FILE, DATA_FORMAT_BANO_FILE, ACTION_TYPE_CONTRIBUTOR_EXPORT, \
    ACTION_TYPE_DATA_SOURCE_FETCH
from tartare.core.gridfs_handler import GridFsHandler
from tests.integration.test_mechanism import TartareFixture


class TestContributorExport(TartareFixture):
    def test_contributor_export_contributor_not_found(self):
        raw = self.post('/contributors/toto/actions/export', {})
        assert raw.status_code == 404
        r = self.json_to_dict(raw)
        assert 'error' in r
        assert r.get('error') == 'contributor not found: toto'

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
        raw = self.post('/contributors/id_test/data_sources',
                        params='{"name": "bobette", "data_format": "gtfs", '
                               '"input": {"type": "url", "url": "' + url + '"}}')
        assert raw.status_code == 201

        resp = self.contributor_export(contributor['id'], check_done=False)
        job = self.get_job_from_export_response(resp)
        assert job['state'] == state
        assert job['step'] == step
        if error_message:
            assert job['error_message'] == error_message

    def test_contributor_export_with_preprocesses_called(self, init_http_download_server, contributor):
        url = self.format_url(ip=init_http_download_server.ip_addr, filename='some_archive.zip')

        raw = self.post('/contributors/id_test/data_sources',
                        params='{"id": "to_process", "name": "bobette", "data_format": "gtfs", '
                               '"input": {"type": "url", "url": "' + url + '"}}')
        assert raw.status_code == 201
        raw = self.post('/contributors/id_test/preprocesses',
                        params='{"type":"GtfsAgencyFile","sequence":0,"data_source_ids":["to_process"],'
                               '"params":{"data":{"agency_id":"112","agency_name":"stif",'
                               '"agency_url":"http://stif.com"}}}')
        assert raw.status_code == 201

        job = self.contributor_export(contributor['id'])
        assert job['state'] == 'done', print(job)

    def test_contributor_export_cleans_files(self, contributor, init_http_download_server):
        url = self.format_url(ip=init_http_download_server.ip_addr, filename='sample_1.zip')
        raw = self.post('/contributors/id_test/data_sources',
                        params='{"name": "bobette", "data_format": "gtfs", "input": {"type": "url", "url": "' + url + '"}}')
        assert raw.status_code == 201

        self.contributor_export(contributor['id'])
        with app.app_context():
            grid_fs_list = GridFsHandler().gridfs.find()
            assert grid_fs_list.count() == 2, print(grid_fs_list)

    def test_contributor_and_coverage_export_cleans_files(self, contributor, init_http_download_server):
        url = self.format_url(ip=init_http_download_server.ip_addr, filename='sample_1.zip')
        raw = self.post('/contributors/id_test/data_sources',
                        params='{"name": "bobette", "data_format": "gtfs", "input": {"type": "url", "url": "' + url + '"}}')
        self.assert_sucessful_create(raw)
        raw = self.post('/coverages',
                        params='{"id": "jdr", "name": "name of the coverage jdr", "contributors": ["id_test"]}')
        self.assert_sucessful_create(raw)

        self.contributor_export(contributor['id'])
        self.coverage_export('jdr')
        with app.app_context():
            grid_fs_list = GridFsHandler().gridfs.find()
            assert grid_fs_list.count() == 4

    @pytest.mark.parametrize("filename,path,data_format", [
        ('bano-75.csv', 'ruspell', DATA_FORMAT_BANO_FILE),
        ('empty_pbf.osm.pbf', 'geo_data', DATA_FORMAT_OSM_FILE),
    ])
    def test_contributor_export_geographic(self, init_http_download_server, filename, path, data_format):
        cid = 'contrib-' + data_format
        url = self.format_url(ip=init_http_download_server.ip_addr, filename=filename, path=path)
        raw = self.post('/contributors',
                        '{"id": "' + cid + '", "name":"geographic", "data_prefix":"BBB", "data_type": "geographic"}')
        assert raw.status_code == 201
        raw = self.post('/contributors/{}/data_sources'.format(cid),
                        params='{"name": "bobette", "data_format": "' + data_format + '", "input": {"type": "url", "url": "' + url + '"}}')
        assert raw.status_code == 201

        job = self.contributor_export(cid)
        assert job['state'] == 'done', print(job)
        with app.app_context():
            grid_fs_list = GridFsHandler().gridfs.find()
            assert grid_fs_list.count() == 2

    def test_contributor_export_generates_jobs(self, init_http_download_server):
        contrib_id = 'cid'
        ds_id = 'dsid'
        self.init_contributor(contrib_id, ds_id, self.format_url(init_http_download_server.ip_addr, 'some_archive.zip'))
        self.contributor_export(contrib_id)
        jobs = self.json_to_dict(self.get('/jobs'))['jobs']
        job_export = next((job for job in jobs if job['action_type'] == ACTION_TYPE_CONTRIBUTOR_EXPORT), None)
        job_fetch = next((job for job in jobs if job['action_type'] == ACTION_TYPE_DATA_SOURCE_FETCH), None)
        assert job_fetch['parent_id'] == job_export['id']
        assert job_fetch['id'] != job_export['id']
        assert job_fetch['contributor_id'] == contrib_id
        assert job_fetch['data_source_id'] == ds_id
        assert job_fetch['updated_at'] is not None
        assert job_fetch['started_at'] is not None
        assert job_fetch['step'] == 'save'
        assert job_fetch['state'] == 'done'
        assert job_fetch['coverage_id'] is None
