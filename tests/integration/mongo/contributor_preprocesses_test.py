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
import json
import os
import tempfile
from datetime import date
from zipfile import ZipFile

import pytest
from freezegun import freeze_time
from gridfs.errors import NoFile

from tartare import app
from tartare.core.context import Context, DataSourceContext, ContributorContext
from tartare.core.gridfs_handler import GridFsHandler
from tartare.core.models import Contributor, ValidityPeriod, PreProcess, ContributorExport
from tartare.exceptions import ParameterException
from tartare.helper import get_dict_from_zip
from tartare.processes.contributor.GtfsAgencyFile import GtfsAgencyFile
from tests.integration.test_mechanism import TartareFixture
from tests.utils import _get_file_fixture_full_path, assert_files_equals, assert_zip_contains_only_txt_files


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
                assert_zip_contains_only_txt_files(gtfs_zip)
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
                assert_zip_contains_only_txt_files(gtfs_zip)
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
                assert_zip_contains_only_txt_files(gtfs_zip)
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
                assert_zip_contains_only_txt_files(gtfs_zip)
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


class TestComputeDirectionsProcess(TartareFixture):
    def __setup_contributor_export_environment(self, init_http_download_server, params, add_data_source_config=True,
                                               add_data_source_target=True,
                                               data_set_filename='unsorted_stop_sequences.zip'):
        url = "http://{ip}/compute_directions/{data_set}".format(ip=init_http_download_server.ip_addr,
                                                                 data_set=data_set_filename)
        contrib_payload = {
            "id": "id_test",
            "name": "name_test",
            "data_prefix": "AAA",
            "preprocesses": [{
                "sequence": 0,
                "data_source_ids": ["ds-to-process"],
                "type": "ComputeDirections",
                "params": params
            }]
        }
        data_sources = []
        if add_data_source_target:
            data_sources.append(
                {
                    "id": "ds-to-process",
                    "name": "ds-to-process",
                    "data_format": "gtfs",
                    "input": {"type": "url", "url": url}
                })
        if add_data_source_config:
            data_sources.append({
                "id": "ds-config",
                "name": "ds-config",
                "data_format": "direction_config",
                "input": {"type": "manual"}
            })
        contrib_payload['data_sources'] = data_sources
        raw = self.post('/contributors', json.dumps(contrib_payload))
        r = self.to_json(raw)
        self.assert_sucessful_call(raw, 201)

        if add_data_source_config:
            with open(_get_file_fixture_full_path('compute_directions/config.json'), 'rb') as file:
                raw = self.post('/contributors/id_test/data_sources/ds-config/data_sets',
                                params={'file': file},
                                headers={})
                r = self.to_json(raw)
                self.assert_sucessful_call(raw, 201)

        raw = self.post('/contributors/id_test/actions/export')
        r = self.to_json(raw)
        self.assert_sucessful_call(raw, 201)

        raw = self.get('/jobs/{jid}'.format(jid=r['job']['id']))
        r = self.to_json(raw)
        self.assert_sucessful_call(raw)
        return r['jobs'][0]

    @pytest.mark.parametrize(
        "params", [
            ({}),
            ({"config": {}}),
            ({"config": {"something": "bob"}}),
        ])
    def test_compute_directions_invalid_params(self, params, init_http_download_server_global_fixtures):
        job = self.__setup_contributor_export_environment(init_http_download_server_global_fixtures, params)
        assert job['state'] == 'failed', print(job)
        assert job['step'] == 'preprocess', print(job)
        assert job['error_message'] == 'data_source_id missing in preprocess config', print(job)

    def test_compute_directions_missing_ds_config(self, init_http_download_server_global_fixtures):
        job = self.__setup_contributor_export_environment(init_http_download_server_global_fixtures,
                                                          {"config": {"data_source_id": "ds-config"}},
                                                          add_data_source_config=False)
        assert job['state'] == 'failed', print(job)
        assert job['step'] == 'preprocess', print(job)
        assert job['error_message'] == \
               'data_source_id "ds-config" in preprocess config does not belong to contributor', print(job)

    #
    # Test that:
    # - direction_id not filled and present in config file are filled with corresponding values
    # - missing direction_id column case is handled
    # - if rows in stop_times.txt are not sorted by stop_sequence for each trip_id, the case is handled
    # - if trips line is not present in config file, old direction_id values are kept
    # - 0 is normal direction and 1 is reverse
    # - if not enough stops found to determine direction_id from config and stop_times, nothing is done
    #
    @freeze_time("2017-01-15")
    @pytest.mark.parametrize(
        "data_set_filename, expected_trips_file_name", [
            # stop_sequence not in order
            ('unsorted_stop_sequences.zip', 'compute_directions/expected_trips.txt'),
            # missing column, stop_sequence in order
            ('missing_column.zip', 'compute_directions/expected_trips_missing_column.txt'),
        ])
    def test_compute_directions(self, init_http_download_server_global_fixtures, data_set_filename,
                                expected_trips_file_name):
        job = self.__setup_contributor_export_environment(init_http_download_server_global_fixtures,
                                                          {"config": {"data_source_id": "ds-config"}},
                                                          data_set_filename=data_set_filename)

        assert job['state'] == 'done', print(job)
        assert job['step'] == 'save_contributor_export', print(job)
        assert job['error_message'] == '', print(job)

        with app.app_context():
            export = ContributorExport.get_last('id_test')
            new_zip_file = GridFsHandler().get_file_from_gridfs(export.gridfs_id)
            with ZipFile(new_zip_file, 'r') as new_zip_file:
                with tempfile.TemporaryDirectory() as tmp_dir_name:
                    assert_zip_contains_only_txt_files(new_zip_file)
                    new_zip_file.extractall(tmp_dir_name)
                    assert_files_equals(os.path.join(tmp_dir_name, 'trips.txt'),
                                        _get_file_fixture_full_path(expected_trips_file_name))
