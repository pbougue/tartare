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

import pytest
import requests

from tests.functional.abstract_request_client import AbstractRequestClient


@pytest.mark.functional
class TestFullExport(AbstractRequestClient):
    def test_contrib_export_with_compute_directions(self):
        self.reset_api()
        json_file = self.replace_server_id_in_input_data_source_fixture('contributor.json')
        raw = self.post('contributors', json_file)
        assert raw.status_code == 201, print(raw.content)

        with open(self.fixture_path('compute_directions/config.json'), 'rb') as file:
            raw = requests.post(
                self.get_url() + '/contributors/contributor_with_preprocess_id/data_sources/compute_direction_config_id/data_sets',
                files={'file': file})
            assert raw.status_code == 201, print(self.get_dict_from_response(raw))

        raw = self.post('contributors/contributor_with_preprocess_id/actions/export')
        job_id = self.get_dict_from_response(raw)['job']['id']
        self.wait_for_job_to_be_done(job_id, 'save_contributor_export')

    def test_contrib_export_with_ruspell(self):
        # contributor with: config ruspell, bano data, gtfs and preprocess ruspell
        contributor = {
            "data_prefix": "bob",
            "data_sources": [
                {
                    "data_format": "gtfs",
                    "id": "Google-1",
                    "input": {
                        "type": "url",
                        "url": "http://{HTTP_SERVER_IP}/ruspell/gtfs.zip".format(
                            HTTP_SERVER_IP=os.getenv('HTTP_SERVER_IP'))
                    },
                    "name": "données gtfs"
                },
                {
                    "data_format": "ruspell_config",
                    "id": "ruspell-config",
                    "input": {},
                    "name": "Configuration Ruspell"
                },
                {
                    "data_format": "bano_file",
                    "id": "ruspell-bano_file",
                    "input": {},
                    "name": "Bano Ruspell"
                }
            ],
            "id": "AMI",
            "name": "AMI",
            "preprocesses": [
                {
                    "id": "ruspell_id",
                    "type": "Ruspell",
                    "sequence": 1,
                    "data_source_ids": ["Google-1"],
                    "params": {
                        "links": {
                            "config": "ruspell-config",
                            "bano": [
                                "ruspell-bano_file"
                            ]
                        }
                    }
                }
            ]
        }

        raw = self.post('contributors', contributor)
        assert raw.status_code == 201, print(raw.content)

        # post config ruspell
        with open(self.fixture_path('ruspell/config-fr_idf.yml'), 'rb') as file:
            raw = self.post(
                '/contributors/AMI/data_sources/ruspell-config/data_sets',
                files={'file': file})
            assert raw.status_code == 201, print(self.__get_dict_from_response(raw))

        # post bano data
        with open(self.fixture_path('ruspell//bano-75.csv'), 'rb') as file:
            raw = self.post(
                '/contributors/AMI/data_sources/ruspell-bano_file/data_sets',
                files={'file': file})
            assert raw.status_code == 201, print(self.__get_dict_from_response(raw))

        # launch ruspell preprocess
        raw = self.post('contributors/contributor_with_preprocess_id/actions/export')
        job_id = self.get_dict_from_response(raw)['job']['id']
        self.wait_for_job_to_be_done(job_id, 'save_contributor_export')

    def test_exports_combined(self):
        self.reset_api()
        json_file = self.replace_server_id_in_input_data_source_fixture('contributor_light.json')
        raw = self.post('contributors', json_file)
        assert raw.status_code == 201, print(raw.content)

        with open(self.path_in_functional_folder('coverage.json'), 'rb') as file:
            json_file = json.load(file)
            raw = self.post('coverages', json_file)
            assert raw.status_code == 201, print(raw.content)

        raw = self.post('contributors/contributor_id/actions/export')
        job_id = self.get_dict_from_response(raw)['job']['id']
        self.wait_for_job_to_be_done(job_id, 'save_coverage_export')

    def test_exports_combined_two_coverages(self):
        self.reset_api()
        json_file = self.replace_server_id_in_input_data_source_fixture('contributor_light.json')
        raw = self.post('contributors', json_file)
        assert raw.status_code == 201, print(raw.content)

        with open(self.path_in_functional_folder('coverage.json'), 'rb') as file:
            json_file = json.load(file)
            raw = self.post('coverages', json_file)
            assert raw.status_code == 201, print(raw.content)

        with open(self.path_in_functional_folder('other_coverage.json'), 'rb') as file:
            json_file = json.load(file)
            raw = self.post('coverages', json_file)
            assert raw.status_code == 201, print(raw.content)

        raw = self.post('contributors/contributor_id/actions/export')
        job_id = self.get_dict_from_response(raw)['job']['id']
        self.wait_for_job_to_be_done(job_id, 'save_coverage_export')
