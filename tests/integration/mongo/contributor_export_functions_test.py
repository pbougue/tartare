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

from urllib.error import ContentTooShortError

import mock
import pytest

from tartare import app
from tartare.core.constants import ACTION_TYPE_CONTRIBUTOR_EXPORT
from tartare.core.context import ContributorExportContext
from tartare.core.contributor_export_functions import fetch_datasets_and_return_updated_number
from tartare.core.models import DataSource, Contributor, Input, Job
from tartare.exceptions import ParameterException, FetcherException
from tests.utils import mock_urlretrieve


class TestFetcher:
    @mock.patch('urllib.request.urlretrieve', side_effect=mock_urlretrieve)
    def test_build_no_data_set(self, urlretrieve_func):
        data_source = DataSource(666, 'Bib', 'gtfs', Input('url', 'bob'))
        contrib = Contributor('contribId', 'contribName', 'bob', [data_source])
        context = ContributorExportContext(Job(ACTION_TYPE_CONTRIBUTOR_EXPORT))
        with app.app_context():
            with pytest.raises(ParameterException) as excinfo:
                context.fill_context(contrib)
            assert str(excinfo.value) == 'data source 666 has no data set'

    @mock.patch('urllib.request.urlretrieve', side_effect=ContentTooShortError("http://bob.com/config.json", "bib"))
    def test_fetcher_raises_url_not_found(self, urlretrieve_func):
        data_source = DataSource(666, 'Bib', 'gtfs', Input('url', "http://bob.com/config.json"))
        contrib = Contributor('contribId', 'contribName', 'bob', [data_source])
        with app.app_context():
            contrib.save()
            with pytest.raises(FetcherException) as excinfo:
                fetch_datasets_and_return_updated_number(contrib)
            assert str(
                excinfo.value) == "downloaded file size was shorter than exepected for url http://bob.com/config.json"
