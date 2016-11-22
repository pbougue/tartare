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

from tartare.helper import to_doted_notation, _make_doted_key, upload_file
import requests_mock
from io import StringIO

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
    data = {'a': [{'b':1}, {'c':2}]}
    assert to_doted_notation(data) == {'a.0.b': 1, 'a.1.c':2}

def test_make_doted_key():
    assert _make_doted_key('a') == 'a'
    assert _make_doted_key('a', 'b') == 'a.b'
    assert _make_doted_key(None, 'a', 'b') == 'a.b'
    assert _make_doted_key('a', None, 'b') == 'a.b'
    assert _make_doted_key(None, 'a', None, 'b', None) == 'a.b'

def test_upload_file():
    with requests_mock.Mocker() as m, StringIO('myfile') as stream:
        m.post('http://test.com/', text='ok')
        upload_file('http://test.com/', 'test.txt', stream)
        assert m.called
        assert len(m.request_history) == 1
        request = m.request_history[0]
        assert request.method == 'POST'
        assert request.url == 'http://test.com/'
        #we can't really check the upload: we can only check how it's implemented in requests
