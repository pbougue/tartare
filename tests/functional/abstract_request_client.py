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

    def path_in_functional_folder(self, rel_path):
        return '{}/{}'.format('{}/{}'.format(os.path.dirname(os.path.dirname(__file__)), 'functional'),
                              rel_path)

    def fixture_path(self, rel_path):
        return '{}/{}'.format('{}/{}'.format(os.path.dirname(os.path.dirname(__file__)), 'fixtures'),
                              rel_path)

    def get(self, uri):
        return requests.get(self.get_url() + uri)

    def delete(self, uri):
        return requests.delete(self.get_url() + uri)

    def post(self, uri, payload=None):
        return requests.post(self.get_url() + uri, json=payload)

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
        with open(self.path_in_functional_folder(fixture_path), 'rb') as file:
            json_file = json.load(file)
            for data_source in json_file['data_sources']:
                if data_source['input'] and 'url' in data_source['input']:
                    data_source['input']['url'] = data_source['input']['url'].format(
                        HTTP_SERVER_IP=os.getenv('HTTP_SERVER_IP'))
        return json_file

    def wait_for_job_to_be_done(self, job_id, step, nb_retries_max=10):
        retry = 0
        while retry < nb_retries_max:
            raw = self.get('jobs/' + job_id)
            job = self.get_dict_from_response(raw)['jobs'][0]
            status = job['state']
            assert status != 'failed', print(job)
            if status != 'done':
                sleep(1)
                retry += 1
            else:
                break
        raw = self.get('jobs/' + job_id)
        job = self.get_dict_from_response(raw)['jobs'][0]
        assert job['state'] == 'done'
        assert job['step'] == step
