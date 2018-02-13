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
from tartare import app
from tartare.processes.fusio import is_running


def test_is_running_none_status():
    with pytest.raises(FusioException) as excinfo:
        is_running(status=None)
    assert str(excinfo.value) == "error publishing data on fusio: action not found"
    assert str(excinfo.typename) == "FusioException"


def test_is_running_abort_status():
    with pytest.raises(FusioException) as excinfo:
        is_running(status='aborted')
    assert str(excinfo.value) == "error publishing data on fusio: action aborted"
    assert str(excinfo.typename) == "FusioException"


def test_is_running_terminated_status():
    assert not is_running(status='terminated')


def test_is_running_action():
    assert is_running(status='working')


def test_get_action_id_none_xml():
    with pytest.raises(FusioException) as excinfo:
        Fusio(url=None).get_action_id(raw_xml=bytes())
    assert str(excinfo.value).startswith('invalid xml:')
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


wait_for_action_terminated_retry_count = 0


def action_status(*args, **kwargs):
    global wait_for_action_terminated_retry_count
    wait_for_action_terminated_retry_count += 1
    response = mock.MagicMock()
    response.content = """<?xml version="1.0" encoding="ISO-8859-1"?>
        <Info title="Information sur projet régional">
            <ActionList ActionCount="1" TerminatedCount="0" WaitingCount="0" AbortedCount="0" WorkingCount="1" \
            ThreadSuspended="False">
                <Action ActionType="Mise à jour" ActionCaption="dataupdate" \
                ActionDesc="" Contributor="NAN - Nantes Métropole (TAN)" ContributorId="5" \
                ActionId="1607281547155684" LastError="">
                    <PostDate><Year>2016</Year><Month>07</Month><Day>28</Day></PostDate>
                    <PostTime><Hour>15</Hour><Minute>47</Minute><Second>15</Second></PostTime>
                    <WorkStartDate><Year>2016</Year><Month>07</Month><Day>28</Day></WorkStartDate>
                    <WorkStartTime><Hour>15</Hour><Minute>47</Minute><Second>17</Second></WorkStartTime>
                    <MiddleDuration><Day>0</Day><Hour>00</Hour><Minute>00</Minute><Second>00</Second></MiddleDuration>
                    <WorkDuration><Day>0</Day><Hour>00</Hour><Minute>03</Minute><Second>09</Second></WorkDuration>
                    <ActionProgression Status="Working" Description="" StepCount="5" CurrentStep="5"/>
                </Action>
            </ActionList>
        </Info>"""
    response.status_code = 200

    return response
from retrying import RetryError
@mock.patch('requests.get',  side_effect=action_status)
def test_wait_for_action_terminated_retry(action_status):
    with pytest.raises(RetryError) as excinfo:
        Fusio(url='bob').wait_for_action_terminated('1607281547155684')
    assert wait_for_action_terminated_retry_count == app.config['FUSIO_STOP_MAX_ATTEMPT_NUMBER']


@pytest.mark.parametrize("export_url,fusio_url,expected_url", [
        ("http://fusio.fr/file/ntfs.zip", "http://new_fusio.com/cgi-bin/fusio.dll/", "http://new_fusio.com/file/ntfs.zip"),
        ("https://fusio.fr/file/ntfs.zip", "http://new_fusio.com:8080/cgi-bin/fusio.dll/", "https://new_fusio.com:8080/file/ntfs.zip"),
        ("http://fusio.fr/file/download", "http://new_fusio.com/cgi-bin/fusio.dll/", "http://new_fusio.com/file/download"),
        ("http://fusio.fr/file/download?param1=1&param2=2", "https://new_fusio.com/cgi-bin/fusio.dll/", "http://new_fusio.com/file/download?param1=1&param2=2"),
    ])
def test_replace_url_hostname(export_url, fusio_url, expected_url):
    assert Fusio.replace_url_hostname_from_url(export_url, fusio_url) == expected_url
