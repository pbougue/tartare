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
from io import StringIO

from mock import mock, ANY

from tartare.core.calendar_handler import dic_to_memory_csv


class TestCalendarHandler:
    def test_dic_to_memory_csv_none(self):
        assert None == dic_to_memory_csv([])

    @mock.patch('csv.DictWriter')
    def test_dic_to_memory_csv_argument_keys(self, dict_writer):
        csv = dic_to_memory_csv([{"att1": "val1", "att2": "val2"}], ['att1', 'att2'])
        assert dict_writer.call_args_list[0][0][1] == ['att1', 'att2']
        assert isinstance(csv, StringIO)

    @mock.patch('csv.DictWriter')
    def test_dic_to_memory_csv_keys(self, dict_writer):
        expected_keys = ['att_1', 'att_b', 'att_bob']
        dic_to_memory_csv([{"att_1": "val1", "att_b": "val2", "att_bob": "val2"}])
        assert dict_writer.call_args_list[0][0][1] == expected_keys

    def test_dic_to_memory_csv_return_type(self):
        csv = dic_to_memory_csv([{"att1": "val1", "att2": "val2"}])
        assert isinstance(csv, StringIO)
        csv = dic_to_memory_csv([{"att1": "val1", "att2": "val2"}], ['att1', 'att2'])
        assert isinstance(csv, StringIO)
