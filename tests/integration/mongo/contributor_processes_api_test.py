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
from copy import deepcopy

import pytest

from tartare.core.constants import DATA_FORMAT_DIRECTION_CONFIG, DATA_FORMAT_DEFAULT, DATA_FORMAT_TR_PERIMETER, \
    DATA_FORMAT_LINES_REFERENTIAL, DATA_FORMAT_PT_EXTERNAL_SETTINGS, DATA_FORMAT_GTFS, DATA_FORMAT_ODS
from tests.integration.test_mechanism import TartareFixture


class TestContributorProcessesApi(TartareFixture):
    @pytest.mark.parametrize("input_data_source_ids,message", [
        ('wrong_type', 'Not a valid list.'),
        ([], 'input_data_source_ids should contains one and only one data source id'),
        (['id1', 'id2'], 'input_data_source_ids should contains one and only one data source id'),
        (['id1', 'id2', 'id3'], 'input_data_source_ids should contains one and only one data source id'),
    ])
    def test_post_contributor_process_invalid_input_data_source_ids(self, input_data_source_ids, message):
        self.init_contributor('cid', 'dsid', 'whatever')
        self.add_data_source_to_contributor('cid', 'config-id', 'whatever', DATA_FORMAT_DIRECTION_CONFIG)
        raw = self.add_process_to_contributor({
            'type': 'ComputeDirections',
            'input_data_source_ids': input_data_source_ids,
            'configuration_data_sources': [
                {'name': 'directions', 'ids': ['config-id']}
            ],
            'sequence': 0
        }, 'cid', check_success=False)
        details = self.assert_failed_call(raw)
        assert details == {'error': {'processes': {'0': {'input_data_source_ids': [message]}}},
                           'message': 'Invalid arguments'}

    def test_post_contributor_process_unknown_input_data_source_ids(self):
        self.init_contributor('cid', 'dsid', 'whatever')
        self.add_data_source_to_contributor('cid', 'config-id', 'whatever', DATA_FORMAT_DIRECTION_CONFIG)
        raw = self.add_process_to_contributor({
            'type': 'ComputeDirections',
            'input_data_source_ids': ['unknown'],
            'configuration_data_sources': [
                {'name': 'directions', 'ids': ['config-id']}
            ],
            'sequence': 0
        }, 'cid', check_success=False)
        self.assert_process_validation_error_global(
            raw, 'input_data_source_ids',
            'data source referenced by "unknown" in process "ComputeDirections" not found')


class TestComputeDirectionContributorProcessesApi(TartareFixture):
    @pytest.mark.parametrize("configuration_data_sources", [
        [],
        [{'name': 'useless', 'ids': ['config-id']}],
        [{'name': 'useless', 'ids': ['config-id']}, {'name': 'other', 'ids': ['toto']}],
    ])
    def test_post_contributor_process_wrong_configuration_data_sources(self, configuration_data_sources):
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
            'configuration_data_sources should contain a "directions" data source')

    def test_post_contributor_process_wrong_config_format(self):
        self.init_contributor('cid', 'dsid', 'whatever')
        self.add_data_source_to_contributor('cid', 'config-id', 'whatever', DATA_FORMAT_DEFAULT)
        raw = self.add_process_to_contributor({
            'type': 'ComputeDirections',
            'input_data_source_ids': ['dsid'],
            'configuration_data_sources': [
                {'name': 'directions', 'ids': ['config-id']}
            ],
            'sequence': 0
        }, 'cid', check_success=False)
        self.assert_process_validation_error_global(
            raw, 'configuration_data_sources',
            'data source referenced by "directions" in process "ComputeDirections" should be of data format "{}", found "{}"'.format(
                DATA_FORMAT_DIRECTION_CONFIG, DATA_FORMAT_DEFAULT))

    def test_post_contributor_process_wrong_input(self):
        self.init_contributor('cid', 'dsid', 'whatever', DATA_FORMAT_DIRECTION_CONFIG)
        self.add_data_source_to_contributor('cid', 'config-id', 'whatever', DATA_FORMAT_DIRECTION_CONFIG)
        raw = self.add_process_to_contributor({
            'type': 'ComputeDirections',
            'input_data_source_ids': ['dsid'],
            'configuration_data_sources': [
                {'name': 'directions', 'ids': ['config-id']}
            ],
            'sequence': 0
        }, 'cid', check_success=False)
        self.assert_process_validation_error_global(
            raw, 'input_data_source_ids',
            'input data source in process "ComputeDirections" should be of data format "{}", found "{}"'.format(
                DATA_FORMAT_GTFS, DATA_FORMAT_DIRECTION_CONFIG))

    def test_post_contributor_process_ok(self):
        self.init_contributor('cid', 'dsid', 'whatever')
        self.add_data_source_to_contributor('cid', 'config-id', 'whatever', DATA_FORMAT_DIRECTION_CONFIG)
        self.add_process_to_contributor({
            'type': 'ComputeDirections',
            'input_data_source_ids': ['dsid'],
            'configuration_data_sources': [
                {'name': 'directions', 'ids': ['config-id']}
            ],
            'sequence': 0
        }, 'cid')

    def test_post_contributor_process_ok_on_create(self):
        raw = self.post('/contributors', self.dict_to_json({
            'id': 'cid',
            'name': 'cid',
            'data_prefix': 'prefix_',
            'data_sources': [
                {
                    'id': 'dsid',
                    'name': 'dsid',
                    'type': 'manual',
                    'data_format': DATA_FORMAT_DEFAULT
                },
                {
                    'id': 'config-id',
                    'name': 'config-id',
                    'type': 'manual',
                    'data_format': DATA_FORMAT_DIRECTION_CONFIG
                }
            ],
            'processes': [
                {
                    'type': 'ComputeDirections',
                    'input_data_source_ids': ['dsid'],
                    'configuration_data_sources': [
                        {'name': 'directions', 'ids': ['config-id']}
                    ],
                    'sequence': 0
                }
            ],
        }))
        self.assert_sucessful_create(raw)


class TestHeadSignShortNameContributorProcessesApi(TartareFixture):
    def test_post_contributor_process_wrong_input(self):
        self.init_contributor('cid', 'dsid', 'whatever', DATA_FORMAT_DIRECTION_CONFIG)
        raw = self.add_process_to_contributor({
            'type': 'HeadsignShortName',
            'input_data_source_ids': ['dsid'],
            'sequence': 0
        }, 'cid', check_success=False)
        self.assert_process_validation_error_global(
            raw, 'input_data_source_ids',
            'input data source in process "HeadsignShortName" should be of data format "{}", found "{}"'.format(
                DATA_FORMAT_GTFS, DATA_FORMAT_DIRECTION_CONFIG))

    def test_post_contributor_process_ok(self):
        self.init_contributor('cid', 'dsid', 'whatever')
        self.add_process_to_contributor({
            'type': 'HeadsignShortName',
            'input_data_source_ids': ['dsid'],
            'sequence': 0
        }, 'cid')


class TestComputeExternalSettingsContributorProcessesApi(TartareFixture):
    valid_process = {
        'type': 'ComputeExternalSettings',
        'input_data_source_ids': ['dsid'],
        'target_data_source_id': 'target_id',
        'sequence': 0,
        'configuration_data_sources': [
            {'name': 'perimeter', 'ids': ['perimeter_id']},
            {'name': 'lines_referential', 'ids': ['lines_referential_id']},
        ]
    }

    def test_post_contributor_process_wrong_input(self):
        self.init_contributor('cid', 'dsid', 'whatever', DATA_FORMAT_DIRECTION_CONFIG)
        self.add_data_source_to_contributor('cid', 'target_id', 'url', DATA_FORMAT_PT_EXTERNAL_SETTINGS)
        self.add_data_source_to_contributor('cid', 'perimeter_id', 'url', DATA_FORMAT_TR_PERIMETER)
        self.add_data_source_to_contributor('cid', 'lines_referential_id', 'url', DATA_FORMAT_LINES_REFERENTIAL)
        raw = self.add_process_to_contributor(self.valid_process, 'cid', check_success=False)
        self.assert_process_validation_error_global(
            raw, 'input_data_source_ids',
            'input data source in process "ComputeExternalSettings" should be of data format "{}", found "{}"'.format(
                DATA_FORMAT_GTFS, DATA_FORMAT_DIRECTION_CONFIG))

    def test_post_contributor_process_missing_tr_perimeter(self):
        self.init_contributor('cid', 'dsid', 'whatever')
        self.add_data_source_to_contributor('cid', 'lines_referential_id', 'url', DATA_FORMAT_LINES_REFERENTIAL)
        raw = self.add_process_to_contributor({
            'type': 'ComputeExternalSettings',
            'input_data_source_ids': ['dsid'],
            'target_data_source_id': 'target_id',
            'sequence': 0,
            'configuration_data_sources': [
                {'name': 'lines_referential', 'ids': ['lines_referential_id']},
            ]
        }, 'cid', check_success=False)
        self.assert_process_validation_error(
            raw, 'configuration_data_sources',
            'configuration_data_sources should contain a "perimeter" data source')

    def test_post_contributor_process_wrong_tr_perimeter(self):
        self.init_contributor('cid', 'dsid', 'whatever')
        self.add_data_source_to_contributor('cid', 'lines_referential_id', 'url', DATA_FORMAT_LINES_REFERENTIAL)
        self.add_data_source_to_contributor('cid', 'perimeter_id', 'url', DATA_FORMAT_DEFAULT)
        raw = self.add_process_to_contributor(self.valid_process, 'cid', check_success=False)
        self.assert_process_validation_error_global(
            raw, 'configuration_data_sources',
            'data source referenced by "perimeter" in process "ComputeExternalSettings" should be of data format "{}", found "{}"'.format(
                DATA_FORMAT_TR_PERIMETER, DATA_FORMAT_DEFAULT))

    def test_post_contributor_process_missing_lines_referential(self):
        self.init_contributor('cid', 'dsid', 'whatever')
        self.add_data_source_to_contributor('cid', 'perimeter_id', 'url', DATA_FORMAT_TR_PERIMETER)
        raw = self.add_process_to_contributor({
            'type': 'ComputeExternalSettings',
            'input_data_source_ids': ['dsid'],
            'target_data_source_id': 'target_id',
            'sequence': 0,
            'configuration_data_sources': [
                {'name': 'perimeter', 'ids': ['perimeter_id']},
            ]
        }, 'cid', check_success=False)
        self.assert_process_validation_error(
            raw, 'configuration_data_sources',
            'configuration_data_sources should contain a "lines_referential" data source')

    def test_post_contributor_process_wrong_lines_referential(self):
        self.init_contributor('cid', 'dsid', 'whatever')
        self.add_data_source_to_contributor('cid', 'lines_referential_id', 'url', DATA_FORMAT_DEFAULT)
        self.add_data_source_to_contributor('cid', 'perimeter_id', 'url', DATA_FORMAT_TR_PERIMETER)
        raw = self.add_process_to_contributor(self.valid_process, 'cid', check_success=False)
        self.assert_process_validation_error_global(
            raw, 'configuration_data_sources',
            'data source referenced by "lines_referential" in process "ComputeExternalSettings" should be of data format "{}", found "{}"'.format(
                DATA_FORMAT_LINES_REFERENTIAL, DATA_FORMAT_DEFAULT))

    def test_post_contributor_process_missing_target(self):
        self.init_contributor('cid', 'dsid', 'whatever')
        self.add_data_source_to_contributor('cid', 'lines_referential_id', 'url', DATA_FORMAT_LINES_REFERENTIAL)
        self.add_data_source_to_contributor('cid', 'perimeter_id', 'url', DATA_FORMAT_TR_PERIMETER)
        process = deepcopy(self.valid_process)
        del (process['target_data_source_id'])
        raw = self.add_process_to_contributor(process, 'cid', check_success=False)
        self.assert_process_validation_error(raw, 'target_data_source_id', 'Missing data for required field.')

    def test_post_contributor_process_ok(self):
        self.init_contributor('cid', 'dsid', 'whatever')
        self.add_data_source_to_contributor('cid', 'perimeter_id', 'url', DATA_FORMAT_TR_PERIMETER)
        self.add_data_source_to_contributor('cid', 'lines_referential_id', 'url', DATA_FORMAT_LINES_REFERENTIAL)
        self.add_process_to_contributor(self.valid_process, 'cid')
        contributor = self.get_contributor('cid')
        assert len(contributor['data_sources']) == 4
        assert next((data_source for data_source in contributor['data_sources'] if
                     data_source['id'] == contributor['processes'][0]['target_data_source_id']), None)


class TestGtfsAgencyFileContributorProcessesApi(TartareFixture):
    valid_process = {
        'type': 'GtfsAgencyFile',
        'input_data_source_ids': ['dsid'],
        'sequence': 0,
    }

    def test_post_contributor_process_wrong_input(self):
        self.init_contributor('cid', 'dsid', 'whatever', DATA_FORMAT_DIRECTION_CONFIG)
        raw = self.add_process_to_contributor(self.valid_process, 'cid', check_success=False)
        self.assert_process_validation_error_global(
            raw, 'input_data_source_ids',
            'input data source in process "GtfsAgencyFile" should be of data format "{}", found "{}"'.format(
                DATA_FORMAT_GTFS, DATA_FORMAT_DIRECTION_CONFIG))

    @pytest.mark.parametrize("field,value,error_message", [
        ('agency_id', 123, 'Not a valid string.'),
        ('agency_name', 123, 'Not a valid string.'),
        ('agency_url', 'plop', 'Not a valid URL.'),
        ('agency_timezone', 123, 'Not a valid string.'),
        ('agency_lang', 123, 'Not a valid string.'),
        ('agency_phone', 123, 'Not a valid string.'),
        ('agency_fare_url', 'tada', 'Not a valid URL.'),
        ('agency_email', 'pouet', 'Not a valid email address.'),
    ])
    def test_post_contributor_process_invalid_parameters(self, field, value, error_message):
        self.init_contributor('cid', 'dsid', 'whatever', DATA_FORMAT_GTFS)
        process = deepcopy(self.valid_process)
        process['parameters'] = {field: value}
        raw = self.add_process_to_contributor(process, 'cid', check_success=False)
        details = self.assert_failed_call(raw)
        assert details == {'error': {'processes': {'0': {'parameters': {field: [error_message]}}}},
                           'message': 'Invalid arguments'}

    @pytest.mark.parametrize("field,value", [
        ('agency_id', 'id_as_a_string'),
        ('agency_name', 'agency name'),
        ('agency_url', 'http://valid.url.com/toto'),
        ('agency_timezone', 'Europe/Paris'),
        ('agency_lang', 'en'),
        ('agency_phone', '0607080910'),
        ('agency_fare_url', 'https://valid.url.fr'),
        ('agency_email', 'name@domain.com'),
    ])
    def test_post_contributor_process_valid_parameters(self, field, value):
        self.init_contributor('cid', 'dsid', 'whatever', DATA_FORMAT_GTFS)
        process = deepcopy(self.valid_process)
        process['parameters'] = {field: value}
        self.add_process_to_contributor(process, 'cid')
        contributor = self.get_contributor('cid')
        assert contributor['processes'][0]['parameters'][field] == value

    def test_post_contributor_process_ok(self):
        self.init_contributor('cid', 'dsid', 'whatever')
        self.add_process_to_contributor(self.valid_process, 'cid')
