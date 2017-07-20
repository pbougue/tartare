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

import logging
from datetime import date
from retrying import retry
import requests
from types import MethodType
from tartare.exceptions import FusioException
import xml.etree.cElementTree as ElementTree
from xml.etree.cElementTree import Element
from tartare import app
from typing import Optional, Any


def is_running(status: str) -> bool:
    if not status:
        raise FusioException('Error publishing data on fusio: action not found')

    if status.lower() == 'aborted':
        raise FusioException('Error publishing data on fusio: action aborted')
    return status.lower() != 'terminated'


class Fusio(object):
    @staticmethod
    def format_date(date: date, format: str='%d/%m/%Y') -> str:
        return date.strftime(format)

    def __init__(self, url: str) -> None:
        self.url = url

    @staticmethod
    def __parse_xml(raw_xml: bytes) -> Element:
        try:
            root = ElementTree.fromstring(raw_xml)
        except (ElementTree.ParseError, TypeError) as e:
            raise FusioException("invalid xml: {}".format(str(e)))
        return root

    def get_action_id(self, raw_xml: bytes) -> Optional[str]:
        root = self.__parse_xml(raw_xml)
        action_id_element = root.find('ActionId')
        return None if action_id_element is None else action_id_element.text

    def get_export_url(self, action_id):
        response = self.call(requests.get, api='info')
        if response.status_code != 200:
            raise FusioException('fusio query failed: {}'.format(response))
        root = self.__parse_xml(response.content)
        return next((action.find('ActionProgression').get('Description') for action in root.iter('Action')
                     if action.get('ActionId') == action_id), None)

    def __get_status_by_action_id(self, action_id: str, raw_xml: bytes) -> str:
        root = self.__parse_xml(raw_xml)
        return next((action.find('ActionProgression').get('Status') for action in root.iter('Action')
                     if action.get('ActionId') == action_id), None)

    def call(self, method: Any, api: str = 'api',
             data: Optional[dict] = None,
             files: Optional[dict] = None) -> requests.Response:
        try:
            response = method(self.url.rstrip('/') + '/' + api, data=data, files=files)
        except requests.exceptions.Timeout as e:
            msg = 'call to fusio timeout, error: {}'.format(str(e))
            logging.getLogger(__name__).error(msg)
            raise FusioException(msg)
        except requests.exceptions.RequestException as e:
            msg = 'call to fusio failed, error: {}'.format(str(e))
            logging.getLogger(__name__).exception(msg)
            raise FusioException(msg)

        if response.status_code != 200:
            raise FusioException('fusio query failed: {}'.format(response))
        return response

    @retry(retry_on_result=is_running,
           stop_max_attempt_number=app.config['FUSIO_STOP_MAX_ATTEMPT_NUMBER'],
           wait_fixed=app.config['FUSIO_WAIT_FIXED'])
    def wait_for_action_terminated(self, action_id: str) -> Optional[str]:
        response = self.call(requests.get, api='info')
        return self.__get_status_by_action_id(action_id, response.content)
