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
from time import sleep

import requests


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

    def patch(self, url, params=None, headers={'Content-Type': 'application/json'}):
        data = params if params else {}
        return requests.patch(url, data=data, headers=headers)

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
                assert raw.status_code == 204, print(raw.content)

    def replace_server_id_in_input_data_source_fixture(self, fixture_path):
        with open(self.get_api_fixture_path(fixture_path), 'rb') as file:
            json_file = json.load(file)
            for data_source in json_file['data_sources']:
                if data_source['input'] and 'url' in data_source['input']:
                    data_source['input']['url'] = data_source['input']['url'].format(
                        HTTP_SERVER_IP=os.getenv('HTTP_SERVER_IP'))
        return json_file

    def wait_for_job_to_be_done(self, job_id, step, nb_retries_max=10, break_if='done'):
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
        assert job['step'] == step

    def assert_status_is(self, raw, status):
        assert raw.status_code == status, print(self.get_dict_from_response(raw))

    def assert_sucessful_call(self, raw):
        self.assert_status_is(raw, 200)

    def assert_sucessful_create(self, raw):
        self.assert_status_is(raw, 201)
