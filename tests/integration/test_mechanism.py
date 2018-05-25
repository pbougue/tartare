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
import ftplib
import json
import os
import tempfile
from zipfile import ZipFile

from tartare import app
from tartare.core.constants import DATA_FORMAT_DEFAULT, DATA_TYPE_DEFAULT
from tests.utils import _get_file_fixture_full_path, assert_files_equals


class TartareFixture(object):
    tester = app.test_client()

    def post(self, url, params=None, headers={'Content-Type': 'application/json'}):
        data = params if params else {}
        return self.tester.post(url,
                                headers=headers,
                                data=data)

    def get(self, url, **kwargs):
        return self.tester.get(url, **kwargs)

    def dict_to_json(self, dict):
        return json.dumps(dict)

    def json_to_dict(self, response):
        return json.loads(response.data.decode('utf-8'))

    def patch(self, url, params=None, headers={'Content-Type': 'application/json'}):
        data = params if params else {}
        return self.tester.patch(url,
                                 headers=headers,
                                 data=data)

    def put(self, url, params=None, headers={'Content-Type': 'application/json'}):
        data = params if params else {}
        return self.tester.put(url,
                               headers=headers,
                               data=data)

    def delete(self, url):
        return self.tester.delete(url)

    def is_json(self, data):
        try:
            self.json_to_dict(data)
        except ValueError:
            return False
        return True

    def format_url(self, ip, filename, path='gtfs', method='http'):
        return "{method}://{ip}/{path}/{filename}".format(method=method, ip=ip, filename=filename, path=path)

    def assert_sucessful_create(self, raw):
        self.assert_sucessful_call(raw, 201)

    def assert_sucessful_call(self, raw, status_code_expected=200):
        debug = self.json_to_dict(raw) if status_code_expected != 204 else 'no body'
        assert raw.status_code == status_code_expected, print(debug)
        return debug

    def assert_failed_call(self, raw, status_code_expected=400):
        assert raw.status_code == status_code_expected, print(self.json_to_dict(raw))
        return self.json_to_dict(raw)

    def get_job_details(self, id):
        raw = self.get('/jobs/{}'.format(id))
        self.assert_sucessful_call(raw, 200)
        return self.json_to_dict(raw)['jobs'][0]

    def contributor_export(self, contributor_id, check_done=True):
        resp = self.post("/contributors/{}/actions/export".format(contributor_id))
        self.assert_sucessful_call(resp, 201)
        if check_done:
            job = self.get_job_from_export_response(resp)
            assert job['state'] == 'done', print(job)
            assert job['step'] == 'save_contributor_export', print(job)
            assert job['error_message'] == '', print(job)
            return job
        return resp

    def get_job_from_export_response(self, response):
        self.assert_sucessful_call(response, 201)
        resp = self.get("/jobs/{}".format(self.json_to_dict(response)['job']['id']))
        return self.json_to_dict(resp)['jobs'][0]

    def coverage_export(self, coverage_id, current_date=None):
        date_option = '?current_date=' + current_date if current_date else ''
        resp = self.post("/coverages/{}/actions/export{}".format(coverage_id, date_option))
        self.assert_sucessful_call(resp, 201)
        return resp

    def full_export(self, contributor_id, coverage_id, current_date=None):
        self.contributor_export(contributor_id)
        return self.coverage_export(coverage_id, current_date)

    def init_contributor(self, contributor_id, data_source_id, url=None, data_format=DATA_FORMAT_DEFAULT,
                         data_type=DATA_TYPE_DEFAULT, manual=False, service_id=None, data_prefix=None, export_id=None):
        input = {'type': 'manual'} if manual else {
            "type": "url",
            "url": url
        }
        data_prefix = data_prefix if data_prefix else contributor_id + '_prefix'

        data_source = {
            "id": data_source_id,
            "name": data_source_id,
            "data_format": data_format,
            "service_id": service_id,
            "input": input
        }
        if export_id:
            data_source['export_data_source_id'] = export_id
        contributor = {
            "data_type": data_type,
            "id": contributor_id,
            "name": contributor_id + '_name',
            "data_prefix": data_prefix,
            "data_sources": [data_source]
        }
        raw = self.post('/contributors', self.dict_to_json(contributor))
        self.assert_sucessful_create(raw)
        return self.json_to_dict(raw)['contributors'][0]

    def init_coverage(self, id, contributors_ids=None, preprocesses=None, environments=None, license=None):
        contributors_ids = contributors_ids if contributors_ids else []
        preprocesses = preprocesses if preprocesses else []
        environments = environments if environments else {}
        coverage = {
            "id": id,
            "name": id,
            "contributors_ids": contributors_ids,
            "preprocesses": preprocesses,
            "environments": environments,
            "short_description": "description of coverage {}".format(id)
        }
        if license:
            coverage['license'] = license
        raw = self.post('/coverages', json.dumps(coverage))
        self.assert_sucessful_create(raw)
        return self.json_to_dict(raw)

    def add_preprocess_to_coverage(self, preprocess, coverage_id):
        raw = self.post('coverages/{}/preprocesses'.format(coverage_id), self.dict_to_json(preprocess))
        self.assert_sucessful_create(raw)

    def add_preprocess_to_contributor(self, preprocess, contributor_id):
        raw = self.post('contributors/{}/preprocesses'.format(contributor_id), self.dict_to_json(preprocess))
        self.assert_sucessful_create(raw)

    def add_data_source_to_contributor(self, contrib_id, data_source_id, url, data_format=DATA_FORMAT_DEFAULT):
        data_source = {
            "id": data_source_id,
            "name": data_source_id,
            "data_format": data_format,
            "input": {
                "type": "url",
                "url": url
            }
        }
        raw = self.post('/contributors/{}/data_sources'.format(contrib_id), self.dict_to_json(data_source))
        self.assert_sucessful_create(raw)

    def update_data_source_url(self, contrib_id, ds_id, url):
        contributor = self.get_contributor(contrib_id)
        data_source = next(data_source for data_source in contributor['data_sources'] if data_source['id'] == ds_id)
        data_source['input']['url'] = url
        raw = self.put('/contributors/{}'.format(contrib_id), self.dict_to_json(contributor))
        return self.assert_sucessful_call(raw, 200)

    def run_automatic_update(self):
        raw = self.post('/actions/automatic_update')
        self.assert_sucessful_call(raw, 204)
        raw = self.get('/jobs')
        self.assert_sucessful_call(raw, 200)
        return self.json_to_dict(raw)['jobs']

    def get_fusio_export_url_response_from_action_id(self, action_id, export_url):
        return """<?xml version="1.0" encoding="ISO-8859-1"?>
        <Info>
            <ActionList ActionCount="1" TerminatedCount="1" WaitingCount="0" AbortedCount="0" WorkingCount="0"
                        ThreadSuspended="True">
                <Action ActionType="Export" ActionCaption="export" ActionDesc="" Contributor="" ContributorId="-1"
                        ActionId="{}" LastError="">
                    <ActionProgression Status="Terminated"
                                       Description="{}"
                                       StepCount="10" CurrentStep="10"/>
                </Action>
            </ActionList>
        </Info>""".format(action_id, export_url)

    def get_fusio_response_from_action_id(self, action_id):
        return """<?xml version="1.0" encoding="ISO-8859-1"?>
                            <serverfusio>
                                <ActionId>{action_id}</ActionId>
                            </serverfusio>""".format(action_id=action_id)

    def post_manual_data_set(self, cid, dsid, path):
        with open(_get_file_fixture_full_path(path), 'rb') as file:
            raw = self.post('/contributors/{}/data_sources/{}/data_sets'.format(cid, dsid),
                            params={'file': file},
                            headers={})
            self.assert_sucessful_create(raw)
            return raw

    def assert_ods_uploaded_ok(self, init_ftp_upload_server, coverage_id):
        metadata_file_name = '{coverage_id}.txt'.format(coverage_id=coverage_id)
        expected_filename = '{coverage_id}.zip'.format(coverage_id=coverage_id)
        session = ftplib.FTP(init_ftp_upload_server.ip_addr, init_ftp_upload_server.user,
                             init_ftp_upload_server.password)

        directory_content = session.nlst()
        assert len(directory_content) == 1
        assert expected_filename in directory_content
        # check that meta data from file on ftp server are correct
        with tempfile.TemporaryDirectory() as tmp_dirname:
            transfered_full_name = os.path.join(tmp_dirname, 'transfered_file.zip')
            with open(transfered_full_name, 'wb') as dest_file:
                session.retrbinary('RETR {expected_filename}'.format(expected_filename=expected_filename),
                                   dest_file.write)
                session.delete(expected_filename)
            with ZipFile(transfered_full_name, 'r') as ods_zip:
                ods_zip.extract(metadata_file_name, tmp_dirname)
                fixture = _get_file_fixture_full_path('metadata/' + metadata_file_name)
                metadata = os.path.join(tmp_dirname, metadata_file_name)
                assert_files_equals(metadata, fixture)
        session.quit()

    def fetch_data_source(self, contributor_id, data_source_id, check_success=True):
        response = self.post('/contributors/{}/data_sources/{}/actions/fetch'.format(contributor_id, data_source_id))
        if check_success:
            self.assert_sucessful_call(response, 204)
        else:
            return response

    @classmethod
    def filter_job_of_action_type(cls, jobs, action_type, return_first=True):
        jobs = (job for job in jobs if job['action_type'] == action_type)
        if return_first:
            return next(jobs, None)
        return jobs

    def get_coverage(self, coverage_id):
        raw = self.get('coverages/{}'.format(coverage_id))
        self.assert_sucessful_call(raw)
        return self.json_to_dict(raw)['coverages'][0]

    def get_contributor(self, contributor_id):
        raw = self.get('contributors/{}'.format(contributor_id))
        self.assert_sucessful_call(raw)
        return self.json_to_dict(raw)['contributors'][0]
