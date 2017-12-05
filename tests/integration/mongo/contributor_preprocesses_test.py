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
from zipfile import ZipFile
import pytest


from tartare import app
from tartare.core.constants import DATA_FORMAT_PT_EXTERNAL_SETTINGS
from tartare.core.gridfs_handler import GridFsHandler
from tartare.core.models import ContributorExport
from tartare.helper import get_dict_from_zip
from tests.integration.test_mechanism import TartareFixture
from tests.utils import _get_file_fixture_full_path, assert_files_equals, assert_zip_contains_only_txt_files, \
    assert_zip_contains_only_files_with_extensions


class TestGtfsAgencyProcess(TartareFixture):
    excepted_headers = ["agency_id", "agency_name", "agency_url", "agency_timezone", "agency_lang",
                        "agency_phone", "agency_fare_url", "agency_email"]
    excepted_headers.sort()

    def __contributor_creator(self, data_set_url, contrib_id='contrib_id', data_source_id='id2'):
        contrib_payload = {
            "id": contrib_id,
            "name": "name_test",
            "data_prefix": "AAA",
            "data_sources": [
                {
                    "input": {
                        "type": "url",
                        "url": data_set_url
                    },
                    "id": data_source_id,
                    "name": "data_source_to_process_name",
                    "data_format": "gtfs"
                }
            ],
            "preprocesses": [
                {
                    "sequence": 0,
                    "data_source_ids": [data_source_id],
                    "type": "GtfsAgencyFile",
                    "params": {
                        "data": {
                            "agency_id": "112",
                            "agency_name": "stif",
                            "agency_url": "http://stif.com"
                        }
                    }
                }
            ]
        }
        return contrib_payload

    def test_gtfs_without_agency_file(self, init_http_download_server):
        url = self.format_url(ip=init_http_download_server.ip_addr, filename='some_archive.zip')
        contrib_payload = self.__contributor_creator(url)

        raw = self.post('/contributors', json.dumps(contrib_payload))
        self.assert_sucessful_call(raw, 201)
        r = self.json_to_dict(raw)
        assert len(r["contributors"]) == 1
        preprocesses = r["contributors"][0]["preprocesses"]
        assert len(preprocesses) == 1


        raw = self.post('/contributors/contrib_id/actions/export?current_date=2015-08-23')
        self.assert_sucessful_call(raw, 201)
        r = self.json_to_dict(raw)


        job = self.get('/jobs/{jid}'.format(jid=r['job']['id']))
        self.assert_sucessful_call(job)
        r = self.json_to_dict(job)
        assert r["jobs"][0]['state'] == 'done', print(job)

        exports = self.get('/contributors/contrib_id/exports')
        self.assert_sucessful_call(exports)
        r = self.json_to_dict(exports)
        assert len(r["exports"]) == 1
        gridfs_id = r["exports"][0]["data_sources"][0]['gridfs_id']

        with app.app_context():
            new_gridfs_file = GridFsHandler().get_file_from_gridfs(gridfs_id)
            with ZipFile(new_gridfs_file, 'r') as gtfs_zip:
                assert_zip_contains_only_txt_files(gtfs_zip)
                assert 'agency.txt' in gtfs_zip.namelist()
                data = get_dict_from_zip(gtfs_zip, 'agency.txt')
                assert len(data) == 1

                keys = list(data[0].keys())
                keys.sort()
                assert keys == self.excepted_headers
                conf = preprocesses[0].get('params').get("data")
                for key, value in conf.items():
                    assert value == data[0][key]

    def test_gtfs_with_agency_file(self, init_http_download_server):
        url = self.format_url(ip=init_http_download_server.ip_addr, filename='gtfs_valid.zip')
        contrib_payload = self.__contributor_creator(url)

        raw = self.post('/contributors', json.dumps(contrib_payload))
        self.assert_sucessful_call(raw, 201)
        r = self.json_to_dict(raw)
        assert len(r["contributors"]) == 1
        preprocesses = r["contributors"][0]["preprocesses"]
        assert len(preprocesses) == 1

        raw = self.post('/contributors/contrib_id/actions/export?current_date=2017-03-30')
        self.assert_sucessful_call(raw, 201)
        r = self.json_to_dict(raw)

        job = self.get('/jobs/{jid}'.format(jid=r['job']['id']))
        self.assert_sucessful_call(job)
        r = self.json_to_dict(job)
        assert r["jobs"][0]['state'] == 'done', print(job)

        exports = self.get('/contributors/contrib_id/exports')
        self.assert_sucessful_call(exports)
        r = self.json_to_dict(exports)
        assert len(r["exports"]) == 1
        gridfs_id = r["exports"][0]["data_sources"][0]['gridfs_id']

        with app.app_context():
            new_gridfs_file = GridFsHandler().get_file_from_gridfs(gridfs_id)
            with ZipFile(new_gridfs_file, 'r') as gtfs_zip:
                assert_zip_contains_only_txt_files(gtfs_zip)
                assert 'agency.txt' in gtfs_zip.namelist()
                data = get_dict_from_zip(gtfs_zip, 'agency.txt')
                assert len(data) == 2

    def test_gtfs_with_empty_agency_file(self, init_http_download_server):
        url = self.format_url(ip=init_http_download_server.ip_addr, filename='gtfs_empty_agency_file.zip')
        contrib_payload = self.__contributor_creator(url)

        raw = self.post('/contributors', json.dumps(contrib_payload))
        self.assert_sucessful_call(raw, 201)
        r = self.json_to_dict(raw)
        assert len(r["contributors"]) == 1
        preprocesses = r["contributors"][0]["preprocesses"]
        assert len(preprocesses) == 1

        raw = self.post('/contributors/contrib_id/actions/export?current_date=2017-03-30')
        self.assert_sucessful_call(raw, 201)
        r = self.json_to_dict(raw)

        job = self.get('/jobs/{jid}'.format(jid=r['job']['id']))
        self.assert_sucessful_call(job)
        r = self.json_to_dict(job)
        assert r["jobs"][0]['state'] == 'done', print(job)

        exports = self.get('/contributors/contrib_id/exports')
        self.assert_sucessful_call(exports)
        r = self.json_to_dict(exports)
        assert len(r["exports"]) == 1
        gridfs_id = r["exports"][0]["data_sources"][0]['gridfs_id']

        with app.app_context():
            new_gridfs_file = GridFsHandler().get_file_from_gridfs(gridfs_id)
            with ZipFile(new_gridfs_file, 'r') as gtfs_zip:
                assert_zip_contains_only_txt_files(gtfs_zip)
                assert 'agency.txt' in gtfs_zip.namelist()
                data = get_dict_from_zip(gtfs_zip, 'agency.txt')
                assert len(data) == 1

                keys = list(data[0].keys())
                keys.sort()
                assert keys == self.excepted_headers
                conf = preprocesses[0].get('params').get("data")
                for key, value in conf.items():
                    assert value == data[0][key]

    def test_gtfs_header_only_in_agency_file(self, init_http_download_server):
        url = self.format_url(ip=init_http_download_server.ip_addr, filename='gtfs_header_only_in_agency_file.zip')

        contrib_payload = self.__contributor_creator(url)

        raw = self.post('/contributors', json.dumps(contrib_payload))
        self.assert_sucessful_call(raw, 201)
        r = self.json_to_dict(raw)
        assert len(r["contributors"]) == 1
        preprocesses = r["contributors"][0]["preprocesses"]
        assert len(preprocesses) == 1

        raw = self.post('/contributors/contrib_id/actions/export?current_date=2017-03-30')
        self.assert_sucessful_call(raw, 201)
        r = self.json_to_dict(raw)


        job = self.get('/jobs/{jid}'.format(jid=r['job']['id']))
        self.assert_sucessful_call(job)
        r = self.json_to_dict(job)
        assert r["jobs"][0]['state'] == 'done', print(job)

        exports = self.get('/contributors/contrib_id/exports')
        self.assert_sucessful_call(exports)
        r = self.json_to_dict(exports)
        assert len(r["exports"]) == 1
        gridfs_id = r["exports"][0]["data_sources"][0]['gridfs_id']

        with app.app_context():

            new_gridfs_file = GridFsHandler().get_file_from_gridfs(gridfs_id)
            with ZipFile(new_gridfs_file, 'r') as gtfs_zip:
                assert_zip_contains_only_txt_files(gtfs_zip)
                assert 'agency.txt' in gtfs_zip.namelist()
                data = get_dict_from_zip(gtfs_zip, 'agency.txt')
                assert len(data) == 1

                keys = list(data[0].keys())
                keys.sort()
                assert keys == self.excepted_headers
                default_agency_data = {
                    "agency_id": '112',
                    "agency_name": "stif",
                    "agency_url": "http://stif.com",
                    "agency_timezone": "",
                    "agency_lang": "",
                    "agency_phone": "",
                    "agency_fare_url": "",
                    "agency_email": ""
                }
                for key, value in default_agency_data.items():
                    assert value == data[0][key]


class TestComputeDirectionsProcess(TartareFixture):
    def __do_export(self):
        raw = self.post('/contributors/id_test/actions/export?current_date=2017-01-15')
        r = self.json_to_dict(raw)
        self.assert_sucessful_call(raw, 201)

        raw = self.get('/jobs/{jid}'.format(jid=r['job']['id']))
        r = self.json_to_dict(raw)
        self.assert_sucessful_call(raw)
        return r['jobs'][0]

    def __setup_contributor_export_environment(self, init_http_download_server, params, add_data_source_config=True,
                                               add_data_source_target=True,
                                               data_set_filename='unsorted_stop_sequences.zip',
                                               do_export=True):
        url = self.format_url(ip=init_http_download_server.ip_addr, filename=data_set_filename,
                              path='compute_directions')
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
        self.assert_sucessful_call(raw, 201)

        if add_data_source_config:
            with open(_get_file_fixture_full_path('compute_directions/config.json'), 'rb') as file:
                raw = self.post('/contributors/id_test/data_sources/ds-config/data_sets',
                                params={'file': file},
                                headers={})
                self.assert_sucessful_call(raw, 201)

        if do_export:
            return self.__do_export()

    @pytest.mark.parametrize(
        "params, expected_error_message", [
            ({}, "links missing in preprocess"),
            ({"links": []}, "empty links in preprocess"),
            ({"links": [{"contributor_id": "something", "data_source_id": "bob"}]},
             "link bob is not a data_source id present in contributor something")
        ])
    def test_compute_directions_invalid_params(self, params, expected_error_message, init_http_download_server):
        job = self.__setup_contributor_export_environment(init_http_download_server, params)
        assert job['state'] == 'failed', print(job)
        assert job['step'] == 'preprocess', print(job)
        assert job['error_message'] == expected_error_message, print(job)

    def test_compute_directions_missing_ds_config(self, init_http_download_server):
        job = self.__setup_contributor_export_environment(init_http_download_server,
                                                          {"links": [{"contributor_id": "id_test",
                                                                      "data_source_id": "ds-config"}]},
                                                          add_data_source_config=False)
        assert job['state'] == 'failed', print(job)
        assert job['step'] == 'preprocess', print(job)
        assert job['error_message'] == \
               'link ds-config is not a data_source id present in contributor id_test', print(job)

    #
    # Test that:
    # - direction_id not filled and present in config file are filled with corresponding values
    # - missing direction_id column case is handled
    # - if rows in stop_times.txt are not sorted by stop_sequence for each trip_id, the case is handled
    # - if trips line is not present in config file, old direction_id values are kept
    # - 0 is normal direction and 1 is reverse
    # - if not enough stops found to determine direction_id from config and stop_times, nothing is done
    #
    @pytest.mark.parametrize(
        "data_set_filename, expected_trips_file_name", [
            # stop_sequence not in order
            ('unsorted_stop_sequences.zip', 'compute_directions/expected_trips.txt'),
            # missing column, stop_sequence in order
            ('missing_column.zip', 'compute_directions/expected_trips_missing_column.txt'),
        ])
    def test_compute_directions(self, init_http_download_server, data_set_filename,
                                expected_trips_file_name):
        job = self.__setup_contributor_export_environment(init_http_download_server,
                                                          {"links": [{"contributor_id": "id_test",
                                                                      "data_source_id": "ds-config"}]},
                                                          data_set_filename=data_set_filename)

        assert job['state'] == 'done', print(job)
        assert job['step'] == 'save_contributor_export', print(job)
        assert job['error_message'] == '', print(job)

        with app.app_context():
            export = ContributorExport.get_last('id_test')
            new_zip_file = GridFsHandler().get_file_from_gridfs(export.data_sources[0].gridfs_id)
            with ZipFile(new_zip_file, 'r') as new_zip_file:
                with tempfile.TemporaryDirectory() as tmp_dir_name:
                    assert_zip_contains_only_txt_files(new_zip_file)
                    new_zip_file.extractall(tmp_dir_name)
                    assert_files_equals(os.path.join(tmp_dir_name, 'trips.txt'),
                                        _get_file_fixture_full_path(expected_trips_file_name))


class TestComputeExternalSettings(TartareFixture):
    def __setup_contributor_export_environment(self, init_http_download_server, params, links={}):
        url = self.format_url(ip=init_http_download_server.ip_addr,
                              filename='fr-idf-custo-post-fusio-sample.zip',
                              path='prepare_external_settings')
        contrib_payload = {
            "id": "id_test",
            "name": "name_test",
            "data_prefix": "OIF",
            "preprocesses": [{
                "sequence": 0,
                "data_source_ids": ["ds-to-process"],
                "type": "ComputeExternalSettings",
                "params": params
            }]
        }
        data_sources = [
            {
                "id": "ds-to-process",
                "name": "ds-to-process",
                "data_format": "gtfs",
                "input": {"type": "url", "url": url}
            },
            {
                "id": "ds-target",
                "name": "ds-target",
                "data_format": DATA_FORMAT_PT_EXTERNAL_SETTINGS,
                "input": {"type": "computed"}
            }
        ]

        for name, value in links.items():
            data_sources.append(
                {
                    "id": value,
                    "name": value,
                    "data_format": name,
                    "input": {"type": "manual"}
                })

        contrib_payload['data_sources'] = data_sources
        raw = self.post('/contributors', json.dumps(contrib_payload))
        self.assert_sucessful_call(raw, 201)

        for name, value in links.items():
            with open(_get_file_fixture_full_path('prepare_external_settings/{id}.json'.format(id=value)),
                      'rb') as file:
                raw = self.post('/contributors/id_test/data_sources/{id}/data_sets'.format(id=value),
                                params={'file': file},
                                headers={})
                self.assert_sucessful_call(raw, 201)

        raw = self.post('/contributors/id_test/actions/export?current_date=2017-09-11')
        r = self.json_to_dict(raw)
        self.assert_sucessful_call(raw, 201)

        raw = self.get('/jobs/{jid}'.format(jid=r['job']['id']))
        r = self.json_to_dict(raw)
        self.assert_sucessful_call(raw)
        return r['jobs'][0]

    @pytest.mark.parametrize(
        "params, expected_message", [
            ({}, 'target_data_source_id missing in preprocess config'),
            ({'target_data_source_id': 'ds-target'}, 'links missing in preprocess'),
            ({'target_data_source_id': 'ds-target', 'links': []}, 'empty links in preprocess'),
            ({'target_data_source_id': 'ds-target', 'links': [{'lines_referential': 'something'}]},
             'contributor_id missing in links'),
            (
                    {'target_data_source_id': 'ds-target',
                     'links': [{'contributor_id': 'id_test', 'data_source_id': 'whatever'}]},
                    'link whatever is not a data_source id present in contributor id_test'),
        ])
    def test_prepare_external_settings_missing_config(self, init_http_download_server, params,
                                                      expected_message):
        job = self.__setup_contributor_export_environment(init_http_download_server, params)
        assert job['state'] == 'failed', print(job)
        assert job['step'] == 'preprocess', print(job)
        assert job['error_message'] == expected_message, print(job)

    @pytest.mark.parametrize(
        "links, expected_message", [
            ({}, 'link tr_perimeter_id is not a data_source id present in contributor id_test'),
            ({'tr_perimeter': 'tr_perimeter_id'},
             'link lines_referential_id is not a data_source id present in contributor id_test'),
            ({'lines_referential': 'lines_referential_id'},
             'link tr_perimeter_id is not a data_source id present in contributor id_test'),
        ])
    def test_prepare_external_settings_invalid_links(self, init_http_download_server, links,
                                                     expected_message):
        params = {'target_data_source_id': 'ds-target',
                  'links': [
                      {'contributor_id': 'id_test', 'data_source_id': 'tr_perimeter_id'},
                      {'contributor_id': 'id_test', 'data_source_id': 'lines_referential_id'}
                  ]}
        job = self.__setup_contributor_export_environment(init_http_download_server, params, links)
        assert job['state'] == 'failed', print(job)
        assert job['step'] == 'preprocess', print(job)
        assert job['error_message'] == expected_message, print(job)

    def test_prepare_external_settings(self, init_http_download_server):
        params = {'target_data_source_id': 'ds-target',
                  'links': [
                      {'contributor_id': 'id_test', 'data_source_id': 'tr_perimeter_id'},
                      {'contributor_id': 'id_test', 'data_source_id': 'lines_referential_id'}
                  ]}
        links = {'lines_referential': 'lines_referential_id', 'tr_perimeter': 'tr_perimeter_id'}
        job = self.__setup_contributor_export_environment(init_http_download_server,
                                                          params, links)
        assert job['state'] == 'done', print(job)
        assert job['step'] == 'save_contributor_export', print(job)
        assert job['error_message'] == '', print(job)

        with app.app_context():
            export = ContributorExport.get_last('id_test')
            target_grid_fs_id = next((data_source.gridfs_id
                                      for data_source in export.data_sources
                                      if data_source.data_source_id == 'ds-target'), None)
            fusio_settings_zip_file = GridFsHandler().get_file_from_gridfs(target_grid_fs_id)
            with ZipFile(fusio_settings_zip_file, 'r') as fusio_settings_zip_file:
                with tempfile.TemporaryDirectory() as tmp_dir_name:
                    assert_zip_contains_only_files_with_extensions(fusio_settings_zip_file, ['txt'])
                    fusio_settings_zip_file.extractall(tmp_dir_name)
                    assert_files_equals(os.path.join(tmp_dir_name, 'fusio_object_codes.txt'),
                                        _get_file_fixture_full_path(
                                            'prepare_external_settings/expected_fusio_object_codes.txt'))
                    assert_files_equals(os.path.join(tmp_dir_name, 'fusio_object_properties.txt'),
                                        _get_file_fixture_full_path(
                                            'prepare_external_settings/expected_fusio_object_properties.txt'))


class TestHeadsignShortNameProcess(TartareFixture):
    def __contributor_creator(self, data_set_url, contrib_id='contrib_id', data_source_id='id2'):
        contrib_payload = {
            "id": contrib_id,
            "name": "name_test",
            "data_prefix": "AAA",
            "data_sources": [
                {
                    "input": {
                        "type": "url",
                        "url": data_set_url
                    },
                    "id": data_source_id,
                    "name": "data_source_to_process_name",
                    "data_format": "gtfs"
                }
            ],
            "preprocesses": [
                {
                    "sequence": 0,
                    "data_source_ids": [data_source_id],
                    "type": "HeadsignShortName"
                }
            ]
        }
        return contrib_payload

    def test_headsign_short_name(self, init_http_download_server):
        url = self.format_url(ip=init_http_download_server.ip_addr, filename='headsign_short_name.zip')
        contrib_payload = self.__contributor_creator(url)

        raw = self.post('/contributors', json.dumps(contrib_payload))
        self.assert_sucessful_call(raw, 201)
        r = self.json_to_dict(raw)
        assert len(r["contributors"]) == 1
        preprocesses = r["contributors"][0]["preprocesses"]
        assert len(preprocesses) == 1

        raw = self.post('/contributors/contrib_id/actions/export?current_date=2015-08-23')
        self.assert_sucessful_call(raw, 201)
