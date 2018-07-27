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

from tests.integration.test_mechanism import TartareFixture


class TestComputeODSCoverageProcessesApi(TartareFixture):
    @pytest.mark.parametrize("input_data_source_ids,message", [
        ('wrong_type', 'Not a valid list.'),
        ([], 'input_data_source_ids should contains more than one data source id'),
    ])
    def test_post_coverage_with_process_invalid_input_data_source_ids(self, input_data_source_ids, message):
        process = {
            'id': 'compute-ods',
            'type': 'ComputeODS',
            'input_data_source_ids': input_data_source_ids,
            "target_data_source_id": "ods",
            'sequence': 0
        }
        raw = self.init_coverage('cov_id', processes=[process], check_success=False)
        self.assert_process_validation_error(raw, 'input_data_source_ids', message)

    def test_post_coverage_with_process_no_target_data_source_id(self):
        process = {
            'id': 'compute-ods',
            'type': 'ComputeODS',
            'input_data_source_ids': ['ds_1'],
            'sequence': 0
        }
        raw = self.init_coverage('cov_id', processes=[process], check_success=False)

        self.assert_process_validation_error(raw, 'target_data_source_id', 'Missing data for required field.')
