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
from datetime import date
from io import StringIO

import pytest
import requests_mock
from mock import mock

from tartare.helper import to_doted_notation, _make_doted_key, get_values_by_key, date_from_string, \
    dic_to_memory_csv


def test_to_doted_notation_flat():
    data = {'a': 1, 'b': 2}
    assert data == to_doted_notation(data)


def test_to_doted_notation_one():
    data = {'a': 1, 'b': {'a': 3}}
    assert to_doted_notation(data) == {'a': 1, 'b.a': 3}


def test_to_doted_notation_one_multiple():
    data = {'a': 1, 'b': {'a': 3, 'b': 5}}
    assert to_doted_notation(data) == {'a': 1, 'b.a': 3, 'b.b': 5}


def test_to_doted_notation_two():
    data = {'a': 1, 'b': {'a': 3, 'b': {'c': 9, 'd': 10}}}
    assert to_doted_notation(data) == {'a': 1, 'b.a': 3, 'b.b.c': 9, 'b.b.d': 10}


def test_to_doted_notation_array():
    data = {'a': [{'b': 1}, {'c': 2}]}
    assert to_doted_notation(data) == {'a.0.b': 1, 'a.1.c': 2}


def test_to_doted_notation_with_list_of_scalars():
    data = {'a': 1, 'b': {'a': 3, 'b': {'c': 9, 'd': 10}}, 'e': [1, 2.6, "bar", True]}
    assert to_doted_notation(data) == {'a': 1, 'b.a': 3, 'b.b.c': 9, 'b.b.d': 10, 'e': [1, 2.6, "bar", True]}


def test_make_doted_key():
    assert _make_doted_key('a') == 'a'
    assert _make_doted_key('a', 'b') == 'a.b'
    assert _make_doted_key(None, 'a', 'b') == 'a.b'
    assert _make_doted_key('a', None, 'b') == 'a.b'
    assert _make_doted_key(None, 'a', None, 'b', None) == 'a.b'


def test_get_values_by_key_list():
    t = [{"gridfs_id": 1}, {"a": {"gridfs_id": 2}}]
    out = []
    get_values_by_key(t, out)
    assert len(out) == 2


def test_get_values_by_key_dict():
    t = {"a": {"gridfs_id": 1},
         "b": {
             "c": {"gridfs_id": 2}
         }}
    out = []
    get_values_by_key(t, out)
    assert len(out) == 2
    assert out.sort() == [1, 2].sort()


def test_get_values_by_key_list_doublon():
    t = [{"gridfs_id": 1}, {"a": {"gridfs_id": 1}}]
    out = []
    get_values_by_key(t, out)
    assert len(out) == 1


def test_get_values_by_key_dict_doublon():
    t = {"a": {"gridfs_id": 1},
         "b": {
             "c": {"gridfs_id": 1}
         }}
    out = []
    get_values_by_key(t, out)
    assert len(out) == 1


def test_date_from_string():
    assert date_from_string('2017-02-02', 'aa') == date(year=2017, month=2, day=2)


def test_date_from_string_invalid():
    with pytest.raises(ValueError) as exec_value:
        date_from_string('ee', 'current_date')
    assert str(exec_value.value) == 'the current_date argument value is not valid, you gave: ee'


def test_dic_to_memory_csv_none():
    assert not dic_to_memory_csv([])


@mock.patch('csv.DictWriter')
def test_dic_to_memory_csv_argument_keys(dict_writer):
    csv = dic_to_memory_csv([{"att1": "val1", "att2": "val2"}], ['att1', 'att2'])
    assert dict_writer.call_args_list[0][0][1] == ['att1', 'att2']
    assert isinstance(csv, StringIO)


@mock.patch('csv.DictWriter')
def test_dic_to_memory_csv_keys(dict_writer):
    expected_keys = ['att_1', 'att_b', 'att_bob']
    dic_to_memory_csv([{"att_1": "val1", "att_b": "val2", "att_bob": "val2"}])
    assert dict_writer.call_args_list[0][0][1] == expected_keys


def test_dic_to_memory_csv_return_type():
    csv = dic_to_memory_csv([{"att1": "val1", "att2": "val2"}])
    assert isinstance(csv, StringIO)
    csv = dic_to_memory_csv([{"att1": "val1", "att2": "val2"}], ['att1', 'att2'])
    assert isinstance(csv, StringIO)
