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
import ftplib
import logging
import os
import re
import shutil
import urllib.request
from abc import ABCMeta, abstractmethod
from http.client import HTTPResponse
from typing import Tuple, Optional
from urllib.error import ContentTooShortError, URLError
from urllib.parse import urlparse, urlunparse, ParseResult

from requests import HTTPError

from tartare.core.models import Input
from tartare.exceptions import ParameterException, FetcherException, GuessFileNameFromUrlException

logger = logging.getLogger(__name__)

http_scheme_start = 'http://'
https_scheme_start = 'https://'
ftp_scheme_start = 'ftp://'


class AbstractFetcher(metaclass=ABCMeta):
    @abstractmethod
    def fetch(self, input: Input, destination_path: str) -> Tuple[str, str]:
        """
        :param input: input to fetch from (contains url, options, expected_file_name)
        :param destination_path: the existing directory to use as destination path
        :return: tuple(dest_full_file_name, expected_file_name) where
          - dest_full_file_name is full destination file name (/tmp/tmp123/config.json)
          - expected_file_name is destination file name (config.json)
        """
        pass

    @classmethod
    def check_authent_and_fetch_to_target(cls, input: Input, dest_full_file_name: str) -> None:
        pass

    @classmethod
    def recompose_url_without_authent_from_parsed_result(cls, parsed: ParseResult) -> str:
        return urlunparse(tuple([parsed[0], parsed.hostname]) + parsed[2:6])

    @classmethod
    def get_url_and_credentials(cls, input: Input) \
            -> Tuple[str, Optional[str], Optional[str], Optional[ParseResult]]:
        parsed = urlparse(input.url)
        if not ((input.options and input.options.authent) or parsed.username):
            return input.url, None, None, None
        else:
            url = input.url
            if input.options and input.options.authent:
                username = input.options.authent.username
                password = input.options.authent.password
            else:
                username = parsed.username
                password = parsed.password
                url = cls.recompose_url_without_authent_from_parsed_result(parsed)
            return url, username, password, parsed

    @classmethod
    def fetch_to_target(cls, url: str, dest_full_file_name: str) -> None:
        try:
            urllib.request.urlretrieve(url, dest_full_file_name)
        except ContentTooShortError:
            raise FetcherException('downloaded file size was shorter than exepected for url {}'.format(url))
        except (HTTPError, URLError) as e:
            raise FetcherException('error during download of file: {}'.format(str(e)))

    @classmethod
    def guess_file_name_from_url(cls, url: str) -> str:
        if FetcherManager.http_matches_url(url) or FetcherManager.ftp_matches_url(url):
            parsed = urlparse(url)
            if parsed.path:
                last_part = os.path.basename(parsed.path)
                filename, file_extension = os.path.splitext(last_part)
                if filename and file_extension and not parsed.query:
                    return last_part
            request = urllib.request.Request(method='HEAD', url=url)
            response = urllib.request.build_opener().open(request)
            if isinstance(response, HTTPResponse) and response.status is 200:
                content_disposition = response.getheader('Content-Disposition')
                if content_disposition and 'filename=' in content_disposition:
                    match = re.search(r"attachment; filename=(.+)", content_disposition)
                    if match and len(match.groups()) == 1:
                        return match.groups()[0]

        raise GuessFileNameFromUrlException('unable to guess file name from url {}'.format(url))


class FetcherManager:
    @classmethod
    def http_matches_url(cls, url: str) -> bool:
        return url.startswith(http_scheme_start) or url.startswith(https_scheme_start)

    @classmethod
    def ftp_matches_url(cls, url: str) -> bool:
        return url.startswith(ftp_scheme_start)

    @classmethod
    def select_from_url(cls, url: str) -> AbstractFetcher:
        if cls.http_matches_url(url):
            return HttpFetcher()
        elif cls.ftp_matches_url(url):
            return FtpFetcher()
        raise ParameterException('url "{}" is not supported to fetch data from'.format(url))


class FtpFetcher(AbstractFetcher):
    def fetch(self, input: Input, destination_path: str) -> Tuple[str, str]:
        expected_file_name = self.guess_file_name_from_url(input.url)
        dest_full_file_name = os.path.join(destination_path, expected_file_name)
        self.check_authent_and_fetch_to_target(input, dest_full_file_name)
        return dest_full_file_name, expected_file_name

    @classmethod
    def check_authent_and_fetch_to_target(cls, input: Input, dest_full_file_name: str) -> None:
        url, username, password, parsed = cls.get_url_and_credentials(input)
        if username and password:
            try:
                session = ftplib.FTP(parsed.hostname, username, password)
                with open(dest_full_file_name, 'wb') as dest_file:
                    session.retrbinary('RETR {expected_filename}'.format(expected_filename=parsed.path), dest_file.write)  # type: ignore
                    session.quit()
            except Exception as e:
                raise FetcherException('error during download of file: {}'.format(str(e)))
        else:
            cls.fetch_to_target(url, dest_full_file_name)


class HttpFetcher(AbstractFetcher):
    @classmethod
    def check_authent_and_fetch_to_target(cls, input: Input, dest_full_file_name: str) -> None:
        url, username, password, parsed = cls.get_url_and_credentials(input)
        if username and password:
            try:
                password_manager = urllib.request.HTTPPasswordMgrWithDefaultRealm()
                top_level = '{}://{}'.format(parsed.scheme, parsed.hostname)
                password_manager.add_password(None, top_level, username, password)
                opener = urllib.request.build_opener(urllib.request.HTTPBasicAuthHandler(password_manager))
                with opener.open(url) as response, open(dest_full_file_name, 'wb') as out_file:
                    shutil.copyfileobj(response, out_file)  # type: ignore
            except urllib.error.HTTPError as e:
                raise FetcherException('error during download of file: {}'.format(str(e)))
        else:
            cls.fetch_to_target(url, dest_full_file_name)

    def fetch(self, input: Input, destination_path: str) -> Tuple[str, str]:
        expected_file_name = self.guess_file_name_from_url(input.url) if not input.expected_file_name else \
            input.expected_file_name
        dest_full_file_name = os.path.join(destination_path, expected_file_name)
        self.check_authent_and_fetch_to_target(input, dest_full_file_name)
        return dest_full_file_name, expected_file_name
