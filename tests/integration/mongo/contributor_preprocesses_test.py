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

from tartare.processes.contributor import GtfsAgencyFile
from tartare.core.context import Context, DataSourceContext, ContributorContext
from tartare.core.models import Contributor, ValidityPeriod
from tartare.core.gridfs_handler import GridFsHandler
from datetime import date
from tartare import app
from tartare.exceptions import ParameterException
from zipfile import ZipFile
from tartare.core.calendar_handler import get_dict_from_zip
from gridfs.errors import NoFile
import pytest
import os

preprocess = {
    "data_source_ids": ["id2"],
    "params": {
        "data": {
            "agency_id": "112",
            "agency_name": "stif",
            "agency_url": "http://stif.com"
        }
    }
}

excepted_headers = ["agency_id", "agency_name", "agency_url", "agency_timezone", "agency_lang",
                    "agency_phone", "agency_fare_url", "agency_email"]
excepted_headers.sort()


class TestContributorProcesses:

    def get_gridfs_id(self, filename, contributor_id='contrib_id'):
        fixtures_path = os.path.realpath('tests/fixtures/gtfs/{filename}')
        with open(fixtures_path.format(filename=filename), 'rb') as file:
            return GridFsHandler().save_file_in_gridfs(file, filename=filename, contributor_id=contributor_id)

    def manage_gtfs_and_get_context(self, gridfs_id, context, data_source_id='id2', contributor_preprocess=None):
            contributor = Contributor('123', 'ABC', 'abc')
            validity_period = ValidityPeriod(date(2018, 7, 1), date(2018, 7, 1))

            data_source_context = DataSourceContext(data_source_id, gridfs_id, validity_period)
            contributor_context = ContributorContext(contributor, [data_source_context], validity_period)
            context.contributor_contexts.append(contributor_context)
            pr = contributor_preprocess if contributor_preprocess else preprocess
            gtfs_agency_file = GtfsAgencyFile(context, pr)
            gtfs_agency_file.do()

    def test_gtfs_without_agency_file(self):
        with app.app_context():
            context = Context()
            gridfs_id = self.get_gridfs_id(filename="some_archive.zip")
            self.manage_gtfs_and_get_context(gridfs_id=gridfs_id, context=context)
            assert len(context.contributor_contexts) == 1
            assert len(context.contributor_contexts[0].data_source_contexts) == 1
            new_gridfs_id = context.contributor_contexts[0].data_source_contexts[0].gridfs_id

            assert gridfs_id != new_gridfs_id

            with pytest.raises(NoFile) as excinfo:
                    GridFsHandler().get_file_from_gridfs(gridfs_id)
            assert str(excinfo.value).startswith('no file in gridfs collection')

            new_gridfs_file = GridFsHandler().get_file_from_gridfs(new_gridfs_id)
            with ZipFile(new_gridfs_file, 'r') as gtfs_zip:
                assert 'agency.txt' in gtfs_zip.namelist()
                data = get_dict_from_zip(gtfs_zip, 'agency.txt')
                assert len(data) == 1

                keys = list(data[0].keys())
                keys.sort()
                assert keys == excepted_headers
                for key, value in preprocess.get("params").get("data").items():
                    assert value == data[0][key]

    def test_gtfs_with_agency_file(self):
        with app.app_context():
            context = Context()
            gridfs_id = self.get_gridfs_id(filename="gtfs_valid.zip")
            self.manage_gtfs_and_get_context(gridfs_id=gridfs_id, context=context)
            assert len(context.contributor_contexts) == 1
            assert len(context.contributor_contexts[0].data_source_contexts) == 1
            new_gridfs_id = context.contributor_contexts[0].data_source_contexts[0].gridfs_id

            assert gridfs_id == new_gridfs_id

            new_gridfs_file = GridFsHandler().get_file_from_gridfs(new_gridfs_id)
            with ZipFile(new_gridfs_file, 'r') as gtfs_zip:
                assert 'agency.txt' in gtfs_zip.namelist()
                data = get_dict_from_zip(gtfs_zip, 'agency.txt')
                assert len(data) == 2

    def test_gtfs_with_empty_agency_file(self):
        with app.app_context():
            context = Context()
            gridfs_id = self.get_gridfs_id(filename="gtfs_empty_agency_file.zip")
            self.manage_gtfs_and_get_context(gridfs_id=gridfs_id, context=context)
            assert len(context.contributor_contexts) == 1
            assert len(context.contributor_contexts[0].data_source_contexts) == 1
            new_gridfs_id = context.contributor_contexts[0].data_source_contexts[0].gridfs_id

            assert gridfs_id != new_gridfs_id

            with pytest.raises(NoFile) as excinfo:
                    GridFsHandler().get_file_from_gridfs(gridfs_id)
            assert str(excinfo.value).startswith('no file in gridfs collection')

            new_gridfs_file = GridFsHandler().get_file_from_gridfs(new_gridfs_id)
            with ZipFile(new_gridfs_file, 'r') as gtfs_zip:
                assert 'agency.txt' in gtfs_zip.namelist()
                data = get_dict_from_zip(gtfs_zip, 'agency.txt')
                assert len(data) == 1

                keys = list(data[0].keys())
                keys.sort()
                assert keys == excepted_headers
                for key, value in preprocess.get("params").get("data").items():
                    assert value == data[0][key]

    def test_gtfs_with_data_source_not_in_context(self):
        with app.app_context():
            context = Context()
            gridfs_id = self.get_gridfs_id(filename="gtfs_empty_agency_file.zip")
            with pytest.raises(ParameterException) as excinfo:
                    self.manage_gtfs_and_get_context(gridfs_id=gridfs_id, context=context, data_source_id='id15')
            assert str(excinfo.value).startswith('impossible to build preprocess GtfsAgencyFile : '
                                                 'data source id2 not exist for contributor 123')

    def test_gtfs_with_empty_agency_file_default_values(self):
        with app.app_context():
            context = Context()
            gridfs_id = self.get_gridfs_id(filename="gtfs_empty_agency_file.zip")
            contributor_preprocess = {
                "data_source_ids": ["id2"]
            }

            self.manage_gtfs_and_get_context(gridfs_id=gridfs_id, context=context,
                                             contributor_preprocess=contributor_preprocess)
            assert len(context.contributor_contexts) == 1
            assert len(context.contributor_contexts[0].data_source_contexts) == 1
            new_gridfs_id = context.contributor_contexts[0].data_source_contexts[0].gridfs_id

            assert gridfs_id != new_gridfs_id

            with pytest.raises(NoFile) as excinfo:
                    GridFsHandler().get_file_from_gridfs(gridfs_id)
            assert str(excinfo.value).startswith('no file in gridfs collection')

            new_gridfs_file = GridFsHandler().get_file_from_gridfs(new_gridfs_id)
            with ZipFile(new_gridfs_file, 'r') as gtfs_zip:
                assert 'agency.txt' in gtfs_zip.namelist()
                data = get_dict_from_zip(gtfs_zip, 'agency.txt')
                assert len(data) == 1

                keys = list(data[0].keys())
                keys.sort()
                assert keys == excepted_headers
                default_agency_data = {
                    "agency_id": '42',
                    "agency_name": "",
                    "agency_url": "",
                    "agency_timezone": "",
                    "agency_lang": "",
                    "agency_phone": "",
                    "agency_fare_url": "",
                    "agency_email": ""
                }
                for key, value in default_agency_data.items():
                    assert value == data[0][key]
