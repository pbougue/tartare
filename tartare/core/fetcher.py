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
import urllib.request
import zipfile
from abc import ABCMeta, abstractmethod
from typing import Tuple
from urllib.error import ContentTooShortError, URLError
from urllib.parse import urlparse

from requests import HTTPError

from tartare.core.constants import DATA_FORMAT_GTFS
from tartare.exceptions import ParameterException, FetcherException, GuessFileNameFromUrlException

logger = logging.getLogger(__name__)

http_scheme_start = 'http://'
https_scheme_start = 'https://'
ftp_scheme_start = 'ftp://'


class AbstractFetcher(metaclass=ABCMeta):
    @abstractmethod
    def fetch(self, url: str, destination_path: str, data_format: str = DATA_FORMAT_GTFS,
              expected_file_name: str = None) -> Tuple[str, str]:
        pass


class FetcherSelector:
    @classmethod
    def http_matches_url(cls, url: str) -> bool:
        return url.startswith(http_scheme_start) or url.startswith(https_scheme_start)

    @classmethod
    def select_from_url(cls, url: str) -> AbstractFetcher:
        if cls.http_matches_url(url):
            return HttpFetcher()
        elif url.startswith(ftp_scheme_start):
            raise ParameterException('url "{}" is not supported to fetch data from')
        raise ParameterException('url "{}" is not supported to fetch data from')


class HttpFetcher(AbstractFetcher):
    def guess_file_name_from_url(self, url: str) -> str:
        if FetcherSelector.http_matches_url(url):
            parsed = urlparse(url)
            if parsed.path:
                last_part = os.path.basename(parsed.path)
                filename, file_extension = os.path.splitext(last_part)
                if filename and file_extension:
                    return last_part
        raise GuessFileNameFromUrlException('unable to guess file name from url {}'.format(url))

    def fetch(self, url: str, destination_path: str, data_format: str = DATA_FORMAT_GTFS,
              expected_file_name: str = None) -> Tuple[str, str]:
        """
        :param url: url to fetch from
        :param destination_path: the existing directory to use as destination path
        :param data_format: data format of resource to fetch (see tartare/core/constants.py:DATA_FORMAT_VALUES)
        :param expected_file_name: the file_name to use to save the downloaded file (if None, will guess it from URL)
        :return: tuple(dest_full_file_name, expected_file_name) where
          - dest_full_file_name is full destination file name (/tmp/tmp123/config.json)
          - expected_file_name is destination file name (config.json)
        """
        expected_file_name = self.guess_file_name_from_url(url) if not expected_file_name else expected_file_name
        dest_full_file_name = os.path.join(destination_path, expected_file_name)
        try:
            urllib.request.urlretrieve(url, dest_full_file_name)
        except HTTPError as e:
            raise FetcherException('error during download of file: {}'.format(str(e)))
        except ContentTooShortError:
            raise FetcherException('downloaded file size was shorter than exepected for url {}'.format(url))
        except URLError as e:
            raise FetcherException('error during download of file: {}'.format(str(e)))
        if data_format == DATA_FORMAT_GTFS and not zipfile.is_zipfile(expected_file_name):
            raise FetcherException('downloaded file from url {} is not a zip file'.format(url))
        return dest_full_file_name, expected_file_name
