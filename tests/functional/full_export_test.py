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
import json
import os
from time import sleep

import pytest
import requests


@pytest.mark.functional
class TestFullExport:
    def __get_url(self):
        return 'http://{host}:5666/'.format(host=os.getenv('TARTARE_HOST_IP'))

    def __path_in_functional_folder(self, rel_path):
        return '{}/{}'.format('{}/{}'.format(os.path.dirname(os.path.dirname(__file__)), 'functional'),
                              rel_path)

    def __fixture_path(self, rel_path):
        return '{}/{}'.format('{}/{}'.format(os.path.dirname(os.path.dirname(__file__)), 'fixtures'),
                              rel_path)

    def __get(self, uri):
        return requests.get(self.__get_url() + uri)

    def __delete(self, uri):
        return requests.delete(self.__get_url() + uri)

    def __post(self, uri, payload=None):
        return requests.post(self.__get_url() + uri, json=payload)

    def __get_dict_from_response(self, response):
        return json.loads(response.content)

    def test_contrib_export_with_compute_directions(self):
        raw = self.__get('contributors')
        contributors = self.__get_dict_from_response(raw)['contributors']

        for contributor in contributors:
            raw = self.__delete('contributors/' + contributor['id'])
            assert raw.status_code == 204, print(raw.content)

        with open(self.__path_in_functional_folder('contributor.json'), 'rb') as file:
            json_file = json.load(file)
            for data_source in json_file['data_sources']:
                if data_source['input'] and 'url' in data_source['input']:
                    data_source['input']['url'] = data_source['input']['url'].format(
                        HTTP_SERVER_IP=os.getenv('HTTP_SERVER_IP'))
            raw = self.__post('contributors', json_file)
            assert raw.status_code == 201, print(raw.content)

        with open(self.__fixture_path('compute_directions/config.json'), 'rb') as file:
            raw = requests.post(
                self.__get_url() + '/contributors/contributor_with_preprocess_id/data_sources/compute_direction_config_id/data_sets',
                files={'file': file}, headers={})
            assert raw.status_code == 201, print(self.__get_dict_from_response(raw))

        raw = self.__post('contributors/contributor_with_preprocess_id/actions/export')
        job_id = self.__get_dict_from_response(raw)['job']['id']
        nb_retries_max = 10
        retry = 0
        while retry < nb_retries_max:
            raw = self.__get('jobs/' + job_id)
            job = self.__get_dict_from_response(raw)['jobs'][0]
            status = job['state']
            assert status != 'failed', print(job)
            if status != 'done':
                sleep(1)
                retry += 1
            else:
                break
        raw = self.__get('jobs/' + job_id)
        job = self.__get_dict_from_response(raw)['jobs'][0]
        assert job['state'] == 'done'
        assert job['step'] == 'save_contributor_export'
