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
from urllib.error import ContentTooShortError, URLError

import mock
import pytest
from requests import HTTPError

from tartare.core.constants import DATA_FORMAT_DIRECTION_CONFIG
from tartare.core.fetcher import HttpFetcher, FetcherSelecter
from tartare.exceptions import FetcherException, GuessFileNameFromUrlException


class TestFetcher:
    @pytest.mark.parametrize(
        "url,res", [
            ('http://download.wherever.fr/resources/my_file.txt', True),
            ('https://download.wherever.fr', True),
            ('https://download.wherever.fr/resources', True),
            ('boom.com', False),
            ('ftp://boom.com', False),
            ('smtp://canaltp.fr', False),
        ])
    def test_http_matches_url(self, url, res):
        assert FetcherSelecter.http_matches_url(url) == res

    @pytest.mark.parametrize(
        "url,expected_file_name", [
            ('http://download.wherever.fr/resources/my_file.txt', 'my_file.txt'),
            ('http://download.canaltp.fr/resources/my_file.gtfs', 'my_file.gtfs'),
            ('http://google.com/config.json', 'config.json')
        ])
    def test_guess_file_name_from_url_ok(self, url, expected_file_name):
        file_name = HttpFetcher().guess_file_name_from_url(url)
        assert expected_file_name == file_name, print(file_name)

    @pytest.mark.parametrize(
        "url", [
            '123',
            'bob',
            'ftp://upload.canaltp.fr',
            'http://download.canaltp.fr',
            'http://download.canaltp.fr/resources',
            'http://download.wherever.fr/resources/my_file_without_extension',
        ])
    def test_guess_file_name_from_url_error(self, url):
        with pytest.raises(GuessFileNameFromUrlException) as excinfo:
            HttpFetcher().guess_file_name_from_url(url)
        assert str(excinfo.value) == 'unable to guess file name from url {}'.format(url)

    @mock.patch('urllib.request.urlretrieve')
    def test_fetch_http_error(self, mock_url_retrieve):
        with pytest.raises(FetcherException) as excinfo:
            mock_url_retrieve.side_effect = HTTPError('404 not found')
            HttpFetcher().fetch('http://whatever.com/config.json')
        assert str(excinfo.value) == 'error during download of file: 404 not found'

    @mock.patch('urllib.request.urlretrieve')
    def test_fetch_content_too_short_error(self, mock_url_retrieve):
        url = 'http://whatever.com/config.json'
        with pytest.raises(FetcherException) as excinfo:
            mock_url_retrieve.side_effect = ContentTooShortError('', '')
            HttpFetcher().fetch(url)
        assert str(excinfo.value) == 'downloaded file size was shorter than exepected for url {}'.format(url)

    @mock.patch('urllib.request.urlretrieve')
    def test_fetch_url_error(self, mock_url_retrieve):
        with pytest.raises(FetcherException) as excinfo:
            mock_url_retrieve.side_effect = URLError('details')
            HttpFetcher().fetch('http://whatever.com/config.json')
        assert str(excinfo.value) == 'error during download of file: <urlopen error details>'

    @mock.patch('urllib.request.urlretrieve')
    @mock.patch('zipfile.is_zipfile')
    def test_fetch_zip_error(self, mock_is_zipfile, mock_url_retrieve):
        url = 'http://whatever.com/config.json'
        with pytest.raises(FetcherException) as excinfo:
            mock_is_zipfile.return_value = False
            HttpFetcher().fetch(url)
        assert str(excinfo.value) == 'downloaded file from url {} is not a zip file'.format(url)

    @mock.patch('urllib.request.urlretrieve')
    @mock.patch('zipfile.is_zipfile')
    def test_fetch_ok(self, mock_is_zipfile, mock_url_retrieve):
        url = 'http://whatever.com/data.gtfs'
        mock_is_zipfile.return_value = True
        assert HttpFetcher().fetch(url).endswith('data.gtfs')

    @mock.patch('urllib.request.urlretrieve')
    def test_fetch_ok_data_format(self, mock_url_retrieve):
        url = 'http://whatever.com/config.json'
        assert HttpFetcher().fetch(url, DATA_FORMAT_DIRECTION_CONFIG).endswith('config.json')

    @mock.patch('urllib.request.urlretrieve')
    def test_fetch_ok_expected_file_name(self, mock_url_retrieve):
        url = 'http://whatever.com/resource'
        assert HttpFetcher().fetch(url, DATA_FORMAT_DIRECTION_CONFIG, 'config.json').endswith('config.json')

    @mock.patch('urllib.request.urlretrieve')
    def test_fetch_ok_expected_file_name_missing(self, mock_url_retrieve):
        url = 'http://whatever.com/resource'
        with pytest.raises(GuessFileNameFromUrlException) as excinfo:
            HttpFetcher().fetch(url)
        assert str(excinfo.value) == 'unable to guess file name from url {}'.format(url)
