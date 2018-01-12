# Copyright (c) 2001-2015, Canal TP and/or its affiliates. All rights reserved.
#
# This file is part of Navitia,
#     the software to build cool stuff with public transport.
#
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
import os
import tempfile
from time import sleep
from zipfile import ZipFile

import requests

from tests.utils import assert_files_equals


class AbstractRequestClient:
    def get_url(self):
        return 'http://{host}:5666/'.format(host=os.getenv('TARTARE_HOST_IP'))

    def get_test_relative_path(self, relative_path):
        return '{}/{}'.format(os.path.dirname(os.path.dirname(__file__)), relative_path)

    def get_functional_relative_path(self, relative_path):
        return self.get_test_relative_path(os.path.join('functional', relative_path))

    def get_fixtures_relative_path(self, relative_path):
        return self.get_test_relative_path(os.path.join('fixtures', relative_path))

    def get_api_fixture_path(self, relative_path):
        return self.get_fixtures_relative_path(os.path.join('api', relative_path))

    def get(self, uri):
        return requests.get(self.get_url() + uri)

    def delete(self, uri):
        return requests.delete(self.get_url() + uri)

    def post(self, uri, payload=None, files=None, headers=None):
        return requests.post(self.get_url() + uri, json=payload, files=files, headers=headers)

    def patch(self, uri, params=None, headers={'Content-Type': 'application/json'}):
        data = params if params else {}
        return requests.patch(self.get_url() + uri, data=data, headers=headers)

    def get_json_from_dict(self, dict):
        return json.dumps(dict)

    def get_dict_from_response(self, response):
        return json.loads(response.content)

    def reset_api(self):
        for resource in ['contributors', 'coverages']:
            raw = self.get(resource)
            contributors = self.get_dict_from_response(raw)[resource]

            for contributor in contributors:
                raw = self.delete(resource + '/' + contributor['id'])
                self.assert_sucessful_call(raw, 204)

    def assert_export_file_equals_ref_file(self, contributor_id, data_source_id, ref_file):
        # list of exports
        raw = self.get('contributors/{contributor_id}/exports'.format(contributor_id=contributor_id))
        self.assert_sucessful_call(raw)
        exports = self.get_dict_from_response(raw)
        assert "exports" in exports
        assert len(exports["exports"]) == 1
        gridfs_id = next(
            ds['gridfs_id'] for ds in exports["exports"][0]['data_sources'] if ds['data_source_id'] == data_source_id)
        assert gridfs_id
        export_id = exports["exports"][0]["id"]
        assert export_id

        # get export file
        raw = self.get('contributors/{contributor_id}/exports/{export_id}/files/{gridfs_id}'.format(export_id=export_id,
                                                                                                    gridfs_id=gridfs_id,
                                                                                                    contributor_id=contributor_id))

        self.assert_content_equals_ref_file(raw.content, ref_file)

    def assert_content_equals_ref_file(self, content, ref_zip_file):
        with tempfile.TemporaryDirectory() as extarct_result_tmp, tempfile.TemporaryDirectory() as ref_tmp:
            dest_zip_res = '{}/gtfs.zip'.format(extarct_result_tmp)
            with open(dest_zip_res, 'wb') as f:
                f.write(content)

            with ZipFile(dest_zip_res, 'r') as files_zip_res, ZipFile(self.get_fixtures_relative_path(ref_zip_file),
                                                                      'r') as files_zip:
                except_files_list = files_zip.namelist()
                response_files_list = files_zip_res.namelist()

                assert len(except_files_list) == len(response_files_list)
                files_zip_res.extractall(extarct_result_tmp)
                files_zip.extractall(ref_tmp)

                for f in except_files_list:
                    assert_files_equals('{}/{}'.format(ref_tmp, f), '{}/{}'.format(extarct_result_tmp, f))

    def replace_server_id_in_input_data_source_fixture(self, fixture_path):
        with open(self.get_api_fixture_path(fixture_path), 'rb') as file:
            json_file = json.load(file)
            for data_source in json_file['data_sources']:
                if data_source['input'] and 'url' in data_source['input']:
                    data_source['input']['url'] = data_source['input']['url'].format(
                        HTTP_SERVER_IP=os.getenv('HTTP_SERVER_IP'))
        return json_file

    def wait_for_all_jobs_to_be_done(self):
        jobs = self.get_dict_from_response(self.get('/jobs'))['jobs']
        for job in jobs:
            self.wait_for_job_to_be_done(job['id'])

    def wait_for_job_to_be_done(self, job_id, step=None, nb_retries_max=15, break_if='done'):
        retry = 0
        while retry < nb_retries_max:
            raw = self.get('jobs/' + job_id)
            job = self.get_dict_from_response(raw)['jobs'][0]
            status = job['state']
            if status == break_if:
                break
            else:
                sleep(1)
                retry += 1

        raw = self.get('jobs/' + job_id)
        job = self.get_dict_from_response(raw)['jobs'][0]
        assert job['state'] == break_if
        if step:
            assert job['step'] == step

    def assert_status_is(self, raw, status):
        assert raw.status_code == status, print(self.get_dict_from_response(raw))

    def assert_sucessful_call(self, raw):
        self.assert_status_is(raw, 200)

    def assert_sucessful_create(self, raw):
        self.assert_status_is(raw, 201)

    def full_export(self, contributor_id, coverage_id, current_date=None):
        date_option = '?current_date=' + current_date if current_date else ''
        resp = self.post("/contributors/{}/actions/export{}".format(contributor_id, date_option))
        self.assert_sucessful_create(resp)
        job_id = self.get_dict_from_response(resp)['job']['id']
        self.wait_for_job_to_be_done(job_id, 'save_contributor_export')
        resp = self.post("/coverages/{}/actions/export{}".format(coverage_id, date_option))
        self.assert_sucessful_create(resp)
        job_id = self.get_dict_from_response(resp)['job']['id']
        self.wait_for_job_to_be_done(job_id, 'save_coverage_export')
        return resp
