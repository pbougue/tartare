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
import os
import tempfile
from datetime import date
from zipfile import ZipFile

import pytest
from gridfs.errors import NoFile

from tartare import app
from tartare.core.context import Context, DataSourceContext, ContributorContext
from tartare.core.gridfs_handler import GridFsHandler
from tartare.core.models import Contributor, ValidityPeriod, DataSource, PreProcess
from tartare.exceptions import ParameterException
from tartare.helper import get_dict_from_zip
from tartare.processes.contributor import GtfsAgencyFile, ComputeDirections
from tests.utils import _get_file_fixture_full_path, assert_files_equals


class TestGtfsAgencyProcess:
    preprocess = PreProcess(sequence=0, data_source_ids=["id2"], type="GtfsAgencyFile", params={
            "data": {
                "agency_id": "112",
                "agency_name": "stif",
                "agency_url": "http://stif.com"
            }
        }
    )

    excepted_headers = ["agency_id", "agency_name", "agency_url", "agency_timezone", "agency_lang",
                        "agency_phone", "agency_fare_url", "agency_email"]
    excepted_headers.sort()


    def get_gridfs_id(self, filename, contributor_id='contrib_id'):
        with open(_get_file_fixture_full_path('gtfs/{filename}'.format(filename=filename)), 'rb') as file:
            return GridFsHandler().save_file_in_gridfs(file, filename=filename, contributor_id=contributor_id)


    def manage_gtfs_and_get_context(self, gridfs_id, context, data_source_id='id2', contributor_preprocess=None):
        contributor = Contributor('123', 'ABC', 'abc')
        validity_period = ValidityPeriod(date(2018, 7, 1), date(2018, 7, 1))
        data_source_context = DataSourceContext(data_source_id, gridfs_id, validity_period)
        contributor_context = ContributorContext(contributor, [data_source_context], validity_period)
        context.contributor_contexts.append(contributor_context)
        pr = contributor_preprocess if contributor_preprocess else self.preprocess
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
                assert keys == self.excepted_headers

                for key, value in self.preprocess.params.get("data").items():
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
                assert keys == self.excepted_headers
                for key, value in self.preprocess.params.get("data").items():
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
            contributor_preprocess = PreProcess(data_source_ids=["id2"])

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
                assert keys == self.excepted_headers
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


class TestComputeDirectionsProcess():
    @pytest.mark.parametrize(
        "params", [
            ({}),
            ({"config": {}}),
            ({"config": {"something": "bob"}}),
        ])
    def test_compute_directions_invalid_params(self, params):
        contrib_id = 'fr-idf'
        with app.app_context():
            contributor = Contributor(contrib_id, contrib_id, contrib_id)
            contributor_context = ContributorContext(contributor)
            compute_directions = ComputeDirections(context=Context(contributor_contexts=[contributor_context]),
                                                   preprocess=PreProcess(params=params))
            with pytest.raises(ParameterException) as excinfo:
                compute_directions.do()
            assert str(excinfo.value) == "data_source_id missing in preprocess config"

    def test_compute_directions_missing_ds_config(self):
        contrib_id = 'fr-idf'
        data_source_config_id = 'wrong-ds-conf-id'
        with app.app_context():
            contributor = Contributor(contrib_id, contrib_id, contrib_id)
            contributor.save()
            data_source_to_process = DataSource(id='whatever', data_format='gtfs')
            data_source_to_process.save(contrib_id)

            data_source_context = DataSourceContext(data_source_to_process.id, '')
            contributor_context = ContributorContext(contributor, [data_source_context])

            context = Context('contributor', contributor_contexts=[contributor_context])
            compute_directions = ComputeDirections(context=context,
                                                   preprocess=PreProcess(
                                                       params={"config": {"data_source_id": data_source_config_id}}))
            with pytest.raises(ParameterException) as excinfo:
                compute_directions.do()
            assert str(
                excinfo.value) == 'data_source_id "{ds_conf}" in preprocess config does not belong to contributor'.format(
                ds_conf=data_source_config_id)

    def test_compute_directions_missing_ds_target(self):
        contrib_id = 'fr-idf'
        data_source_config_id = 'ds-conf-id'
        data_source_to_process = 'missing'
        compute_directions_config_file_name = _get_file_fixture_full_path('compute_directions_config.json')
        with app.app_context():
            contributor = Contributor(contrib_id, contrib_id, contrib_id)
            contributor.save()
            data_source_config = DataSource(id=data_source_config_id, name=data_source_config_id, data_format='json')
            data_source_config.save(contrib_id)
            with open(compute_directions_config_file_name, 'rb') as compute_directions_config_file:
                compute_directions_gridfs_id = GridFsHandler().save_file_in_gridfs(compute_directions_config_file,
                                                                                   filename='config.json')
                data_source_config_context = DataSourceContext(data_source_config.id, compute_directions_gridfs_id)
                contributor_context = ContributorContext(contributor, [data_source_config_context])

                context = Context('contributor', contributor_contexts=[contributor_context])
                compute_directions = ComputeDirections(context=context,
                                                       preprocess=PreProcess(data_source_ids=[data_source_to_process],
                                                                             params={"config": {
                                                                                 "data_source_id": data_source_config_id}}))
                with pytest.raises(ParameterException) as excinfo:
                    compute_directions.do()
                assert str(
                    excinfo.value) == 'data_source_id to preprocess "{data_source_id_to_process}" does not belong to contributor'.format(
                    data_source_id_to_process=data_source_to_process)

    @pytest.mark.parametrize(
        "data_set_filename", [
            ('compute_directions.zip'),
            ('compute_directions_missing_column.zip'),
        ])
    def test_compute_directions(self, data_set_filename):
        compute_directions_file_name = _get_file_fixture_full_path(data_set_filename)
        compute_directions_config_file_name = _get_file_fixture_full_path('compute_directions_config.json')
        contrib_id = 'fr-idf'
        data_source_config_id = 'ds-conf-id'
        data_source_to_process_id = 'ds-to-process-id'
        with app.app_context():
            contributor = Contributor(contrib_id, contrib_id, contrib_id)
            contributor.save()
            gsh = GridFsHandler()
            with open(compute_directions_file_name, 'rb') as compute_directions_file:
                with open(compute_directions_config_file_name, 'rb') as compute_directions_config_file:
                    compute_directions_gridfs_id = gsh.save_file_in_gridfs(compute_directions_file, filename='gtfs.zip')
                    compute_directions_config_gridfs_id = gsh.save_file_in_gridfs(compute_directions_config_file,
                                                                                  filename='config.json')
                    data_source_config = DataSource(id=data_source_config_id, name=data_source_config_id,
                                                    data_format='json')
                    data_source_config.save(contrib_id)
                    data_source_to_process = DataSource(id=data_source_to_process_id)
                    data_source_to_process.save(contrib_id)
                    validity_period = ValidityPeriod(date(2017, 11, 11),
                                                     date(2018, 8, 11))
                    data_source_context = DataSourceContext(data_source_to_process.id, compute_directions_gridfs_id,
                                                            validity_period)
                    data_source_config_context = DataSourceContext(data_source_config.id,
                                                                   compute_directions_config_gridfs_id)
                    contributor_context = ContributorContext(contributor,
                                                             [data_source_context, data_source_config_context],
                                                             validity_period)
                    context = Context('contributor', contributor_contexts=[contributor_context])
                    compute_directions = ComputeDirections(context=context,
                                                           preprocess=PreProcess(
                                                               data_source_ids=[data_source_to_process_id],
                                                               params={
                                                                   "config": {
                                                                       "data_source_id": data_source_config_id}}))
                    compute_directions.do()
                    data_source_to_process_context = [dsc for dsc in compute_directions.context.contributor_contexts[
                        0].data_source_contexts if dsc.data_source_id == data_source_to_process_id]

                    new_zip_file = gsh.get_file_from_gridfs(data_source_to_process_context[0].gridfs_id)
                    with ZipFile(new_zip_file, 'r') as new_zip_file:
                        with tempfile.TemporaryDirectory() as tmp_dir_name:
                            new_zip_file.extractall(tmp_dir_name)
                            assert_files_equals(os.path.join(tmp_dir_name, 'trips.txt'),
                                                _get_file_fixture_full_path('expected_compute_directions_trips.txt'))
