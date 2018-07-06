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

from tartare.core.constants import DATA_FORMAT_DIRECTION_CONFIG, DATA_FORMAT_BANO_FILE
from tests.integration.test_mechanism import TartareFixture


class TestContributorProcessesApi(TartareFixture):
    @pytest.mark.parametrize("input_data_source_ids,message", [
        ('wrong_type', 'Not a valid list.'),
        ([], 'input_data_source_ids should contains one and only one data source id'),
        (['id1', 'id2'], 'input_data_source_ids should contains one and only one data source id'),
        (['id1', 'id2', 'id3'], 'input_data_source_ids should contains one and only one data source id'),
        (['unknown'], 'input_data_source_ids should reference an existing data source'),
    ])
    def test_post_contributor_preprocess_invalid_input_data_source_ids(self, input_data_source_ids, message):
        self.init_contributor('cid', 'dsid', 'whatever')
        self.add_data_source_to_contributor('cid', 'config-id', 'whatever', DATA_FORMAT_DIRECTION_CONFIG)
        raw = self.add_process_to_contributor({
            'type': 'ComputeDirections',
            'input_data_source_ids': input_data_source_ids,
            'configuration_data_sources': {
                'compute_direction': 'config-id',
            },
            'sequence': 0
        }, 'cid', check_success=False)
        details = self.assert_failed_call(raw)
        assert details == {'error': {'processes': {'0': {'input_data_source_ids': [message]}}},
                           'message': 'Invalid arguments'}


class TestComputeDirectionContributorProcessesApi(TartareFixture):
    @pytest.mark.parametrize("configuration_data_sources", [
        {},
        {'useless': 'config-id'},
        {'useless': 'config-id', 'other': 'toto'},
    ])
    def test_post_contributor_preprocess_wrong_configuration_data_sources(self, configuration_data_sources):
        self.init_contributor('cid', 'dsid', 'whatever')
        self.add_data_source_to_contributor('cid', 'config-id', 'whatever', DATA_FORMAT_DIRECTION_CONFIG)
        raw = self.add_process_to_contributor({
            'type': 'ComputeDirections',
            'input_data_source_ids': ['dsid'],
            'configuration_data_sources': configuration_data_sources,
            'sequence': 0
        }, 'cid', check_success=False)
        self.assert_process_validation_error(
            raw, 'configuration_data_sources',
            'configuration_data_sources should contain a data source for compute directions')

    def test_post_contributor_preprocess_wrong_config_format(self):
        self.init_contributor('cid', 'dsid', 'whatever')
        self.add_data_source_to_contributor('cid', 'config-id', 'whatever', DATA_FORMAT_BANO_FILE)
        raw = self.add_process_to_contributor({
            'type': 'ComputeDirections',
            'input_data_source_ids': ['dsid'],
            'configuration_data_sources': {
                'compute_direction': 'config-id',
            },
            'sequence': 0
        }, 'cid', check_success=False)
        self.assert_process_validation_error(
            raw, 'configuration_data_sources',
            'configuration_data_sources should contain a direction_config data source for compute directions')

    def test_post_contributor_preprocess_ok(self):
        self.init_contributor('cid', 'dsid', 'whatever')
        self.add_data_source_to_contributor('cid', 'config-id', 'whatever', DATA_FORMAT_DIRECTION_CONFIG)
        self.add_process_to_contributor({
            'type': 'ComputeDirections',
            'input_data_source_ids': ['dsid'],
            'configuration_data_sources': {
                'compute_direction': 'config-id',
            },
            'sequence': 0
        }, 'cid')
