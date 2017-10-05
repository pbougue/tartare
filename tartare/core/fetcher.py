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
import os
import tempfile
import urllib.request
import zipfile
from abc import ABCMeta, abstractmethod
from urllib.error import ContentTooShortError, URLError

from requests import HTTPError

from tartare.core.constants import DATA_FORMAT_GTFS
from tartare.exceptions import ParameterException

logger = logging.getLogger(__name__)


class AbstractFetcher(metaclass=ABCMeta):
    def guess_file_name_from_url(self, url: str) -> str:
        pass

    @abstractmethod
    def fetch(self, url: str, data_format: str, expected_file_name: str = None) -> str:
        pass


class HttpFetcher(AbstractFetcher):
    def fetch(self, url: str, data_format: str, expected_file_name: str = None) -> str:
        with tempfile.TemporaryDirectory() as tmp_dir_name:
            expected_file_name = self.guess_file_name_from_url(url) if not expected_file_name else expected_file_name
            tmp_file_name = os.path.join(tmp_dir_name, expected_file_name)
            try:
                urllib.request.urlretrieve(url, tmp_file_name)
            except HTTPError as e:
                logger.error('error during download of file: {}'.format(str(e)))
                raise
            except ContentTooShortError:
                logger.error('downloaded file size was shorter than exepected for url {}'.format(url))
                raise
            except URLError as e:
                logger.error('error during download of file: {}'.format(str(e)))
                raise
            if data_format == DATA_FORMAT_GTFS and not zipfile.is_zipfile(expected_file_name):
                raise Exception('downloaded file from url {} is not a zip file'.format(url))
        return tmp_file_name


class FetcherSelecter:
    @classmethod
    def select_from_url(cls, url: str) -> AbstractFetcher:
        if url.startswith('http://'):
            return HttpFetcher()
        elif url.startswith('ftp://'):
            raise ParameterException('url "{}" is not supported to fetch data from')
        raise ParameterException('url "{}" is not supported to fetch data from')
