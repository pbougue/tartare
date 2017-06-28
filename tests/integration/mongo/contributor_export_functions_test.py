# coding=utf-8

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

from tartare.core.contributor_export_functions import fetch_datasets
from tartare.core.models import DataSource, Contributor, DataSourceFetched
import mock
from tests.utils import mock_urlretrieve, mock_zip_file
from tartare import app
import pytest
from urllib.error import ContentTooShortError
from tartare.exceptions import InvalidFile
from datetime import date
from tartare.core.context import Context

def test_fetch_data_from_input_failed(mocker):
    url = "http://whatever.com/gtfs.zip"
    data_source = DataSource('myDSId', 'myDS', 'gtfs', {"type": "ftp", "url": url})
    contrib = Contributor('contribId', 'contribName', 'bob', [data_source])

    mock_dl = mocker.patch('urllib.request.urlretrieve', autospec=True)
    mock_check = mocker.patch('zipfile.is_zipfile', autospec=True)
    mock_check.return_value = True

    #following test needs to be improved to handle file creation on local drive
    with pytest.raises(InvalidFile) as excinfo:
        with app.app_context():
            fetch_datasets(contrib, Context())
    assert str(excinfo.typename) == 'InvalidFile'


class TestFetcher():
    @mock.patch('urllib.request.urlretrieve', side_effect=mock_urlretrieve)
    def test_fetcher(self, urlretrieve_func):
        data_source = DataSource(666, 'Bib', 'gtfs', {"type": "ftp", "url": "bob"})
        contrib = Contributor('contribId', 'contribName', 'bob', [data_source])
        context = Context()
        with app.app_context():
            fetch_datasets(contrib, context)
            assert context
            assert len(context.data_sources_fetched) == 1
            assert context.data_sources_fetched[0].data_source_id == 666
            assert context.data_sources_fetched[0].gridfs_id
            assert context.data_sources_fetched[0].validity_period.end_date == date(2015, 8, 26)
            assert context.data_sources_fetched[0].validity_period.start_date == date(2015, 3, 25)

    @mock.patch('urllib.request.urlretrieve', side_effect=ContentTooShortError("http://bob.com", "bib"))
    def test_fetcher_raises_url_not_found(self, urlretrieve_func):
        data_source = DataSource(666, 'Bib', 'gtfs', {"type": "ftp", "url": "bob"})
        contrib = Contributor('contribId', 'contribName', 'bob', [data_source])
        with app.app_context():
            with pytest.raises(ContentTooShortError) as excinfo:
                fetch_datasets(contrib, Context())
            assert str(excinfo.value) == "<urlopen error http://bob.com>"

    @mock.patch('urllib.request.urlretrieve', side_effect=mock_zip_file)
    def test_fetcher_raises_not_zip_file(self, urlretrieve_func):
        data_source = DataSource(666, 'Bib', 'gtfs', {"type": "ftp", "url": "http://bob.com"})
        contrib = Contributor('contribId', 'contribName', 'bob', [data_source])
        with app.app_context():
            with pytest.raises(Exception) as excinfo:
                fetch_datasets(contrib, Context())
            assert str(excinfo.value) == 'downloaded file from url http://bob.com is not a zip file'
