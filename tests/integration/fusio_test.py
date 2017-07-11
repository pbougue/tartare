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

from tartare.processes.fusio import Fusio
from tartare.exceptions import FusioException
import pytest
import mock
import requests
from tests.utils import get_response


def test_get_action_id_none_xml():
    with pytest.raises(FusioException) as excinfo:
        Fusio(url=None).get_action_id(raw_xml=None)
    assert str(excinfo.value) == "invalid xml: 'NoneType' does not support the buffer interface"
    assert str(excinfo.typename) == "FusioException"


def test_get_action_id_valid_xml():
    raw_xml = """<?xml version="1.0" encoding="ISO-8859-1"?>
        <serverfusio>
            <address/>
            <version>Version 1.10.85.200</version>
            <sendaction>dataupdate</sendaction>
            <result>-1</result>
            <ActionId>1607281547155684</ActionId>
        </serverfusio>"""
    action_id = Fusio(url=None).get_action_id(raw_xml=raw_xml)
    assert action_id == "1607281547155684"


def test_get_action_id_xml_without_action_id():
    raw_xml = """<?xml version="1.0" encoding="ISO-8859-1"?>
        <serverfusio>
            <address/>
            <version>Version 1.10.85.200</version>
            <sendaction>dataupdate</sendaction>
            <result>-1</result>
        </serverfusio>"""
    assert Fusio(url=None).get_action_id(raw_xml=raw_xml) == None


@mock.patch('requests.post',  side_effect=requests.exceptions.Timeout('Bob'))
def test_call_fusio_timeout(timeout):
    with pytest.raises(FusioException) as excinfo:
        Fusio(url='bob').call(requests.post, api='api')
    assert str(excinfo.value) == "call to fusio timeout, error: Bob"
    assert str(excinfo.typename) == "FusioException"


@mock.patch('requests.post',  side_effect=requests.exceptions.RequestException('Bob'))
def test_call_fusio_RequestException(RequestException):
    with pytest.raises(FusioException) as excinfo:
        Fusio(url='bob').call(requests.post, api='api')
    assert str(excinfo.value) == "call to fusio failed, error: Bob"
    assert str(excinfo.typename) == "FusioException"


@mock.patch('requests.post',  side_effect=get_response(404))
def test_call_fusio_status_404(RequestException):
    with pytest.raises(FusioException) as excinfo:
        Fusio(url='bob').call(requests.post, api='api')
    assert str(excinfo.typename) == "FusioException"
