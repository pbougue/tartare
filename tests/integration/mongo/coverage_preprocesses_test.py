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
import json
import os
import tempfile
from zipfile import ZipFile

import mock
import pytest

from tartare.core.constants import DATA_FORMAT_OBITI, DATA_FORMAT_TITAN, DATA_FORMAT_NEPTUNE, \
    DATA_FORMAT_PT_EXTERNAL_SETTINGS, DATA_FORMAT_TR_PERIMETER, DATA_FORMAT_LINES_REFERENTIAL
from tests.integration.test_mechanism import TartareFixture
from tests.utils import get_response, assert_text_files_equals, _get_file_fixture_full_path, \
    assert_zip_contains_only_files_with_extensions


class TestFusioDataUpdatePreprocess(TartareFixture):
    def __create_data_source(self, data_source_id, url, service_id='Google-1', name=None):
        if not name:
            name = data_source_id

        return {
            "id": data_source_id,
            "name": name,
            "service_id": service_id,
            "input": {
                "type": "url",
                "url": url
            }
        }

    def __init_contributor(self, contributor_id, data_sources, data_prefix='AAA'):
        contributor = {
            "id": contributor_id,
            "name": "name_test",
            "data_prefix": data_prefix,
            "data_sources": data_sources
        }
        raw = self.post('/contributors', json.dumps(contributor))
        self.assert_sucessful_create(raw)

    def __init_coverage(self, coverage_id, contributors_ids, input_data_source_ids):
        coverage = {
            "id": coverage_id,
            "name": "name of the coverage jdr",
            "contributors_ids": contributors_ids,
            "input_data_source_ids": input_data_source_ids,
            "preprocesses": [
                {
                    "id": "fusio_dataupdate",
                    "type": "FusioDataUpdate",
                    "params": {
                        "url": "http://fusio_host/cgi-bin/fusio.dll/"
                    },
                    "sequence": 0
                }
            ]
        }
        raw = self.post('/coverages', json.dumps(coverage))
        return self.assert_sucessful_create(raw)

    @mock.patch('tartare.processes.fusio.Fusio.wait_for_action_terminated')
    @mock.patch('tartare.processes.fusio.Fusio.call')
    # Given I create a contributor with a data source
    # And   I create a coverage containing this contributor and a preprocess FusioDataUpdate
    # And   I do a contributor export on this contributor (and then a coverage export)
    # When  I do a contributor export on this contributor (and then a coverage export)
    # Then  I can see that Fusio has been called 1 time(s) in total
    # => because one time for the first coverage export (normal) and second export does not need any data update
    def test_data_update_called_for_each_data_source(self, fusio_call, wait_for_action_terminated,
                                                           init_http_download_server):
        filename = 'gtfs-{number}.zip'
        url = self.format_url(ip=init_http_download_server.ip_addr,
                              filename=filename.format(number=1),
                              path='gtfs/historisation')
        self.__init_contributor("id_test", [self.__create_data_source("my_gtfs", url)])
        self.__init_coverage("jdr", ["id_test"], ["my_gtfs"])

        content = self.get_fusio_response_from_action_id(42)
        fusio_call.return_value = get_response(200, content)

        self.full_export('id_test', 'jdr', '2017-08-10')
        self.full_export('id_test', 'jdr', '2017-08-10')

        assert fusio_call.call_count == 2

    # Given I create a contributor with a data source with service_id null
    # And   I create a coverage containing this contributor and a preprocess FusioDataUpdate
    # When  I do a contributor export on this contributor (and then a coverage export)
    # Then  FusioDataUpdate should fail because service_id is null
    def test_data_update_fail_if_data_source_has_service_id_null(self, init_http_download_server):
        filename = 'gtfs-{number}.zip'
        url = self.format_url(ip=init_http_download_server.ip_addr,
                              filename=filename.format(number=1),
                              path='gtfs/historisation')
        self.__init_contributor("id_test", [self.__create_data_source("my_gtfs", url, service_id=None)])
        self.__init_coverage("jdr", ["id_test"], ["my_gtfs"])

        response = self.full_export('id_test', 'jdr', '2017-08-10')
        self.assert_sucessful_call(response, 201)

        job_details = self.get_job_details(self.json_to_dict(response)['job']['id'])

        assert job_details['state'] == 'failed'
        assert job_details[
                   'error_message'] == 'service_id of data source id_test of contributor my_gtfs should not be null'

    @mock.patch('tartare.processes.fusio.Fusio.wait_for_action_terminated')
    @mock.patch('tartare.processes.fusio.Fusio.call')
    # Given I create a contributor with 2 data sources
    # And   I create a coverage containing this contributor and a preprocess FusioDataUpdate
    # When  I do a contributor export on this contributor (and then a coverage export)
    # Then  I can see that Fusio has been called twice
    # And   Each data source service id is used
    def test_data_update_one_contributor_with_two_data_sources(self, fusio_call, wait_for_action_terminated,
                                                               init_http_download_server):
        filename = 'gtfs-{number}.zip'
        url = self.format_url(ip=init_http_download_server.ip_addr,
                              filename=filename.format(number=1),
                              path='gtfs/historisation')
        self.__init_contributor("id_test", [
            self.__create_data_source("my_gtfs_1", url, service_id='Google-1'),
            self.__create_data_source("my_gtfs_2", url, service_id='Google-2', name="my_gtfs_2"),
        ])
        self.__init_coverage("jdr", ["id_test"], ["my_gtfs_1", "my_gtfs_2"])

        content = self.get_fusio_response_from_action_id(42)

        fusio_call.return_value = get_response(200, content)
        self.full_export('id_test', 'jdr', '2017-08-10')

        assert fusio_call.call_count == 2
        assert fusio_call.call_args_list[0][1]['data']['serviceid'] == 'Google-1'
        assert fusio_call.call_args_list[1][1]['data']['serviceid'] == 'Google-2'

    @mock.patch('tartare.processes.fusio.Fusio.wait_for_action_terminated')
    @mock.patch('tartare.processes.fusio.Fusio.call')
    @pytest.mark.parametrize("data_format,file_name,begin_date,end_date", [
        (DATA_FORMAT_TITAN, 'titan.zip', '02/01/2018', '18/06/2018'),
        (DATA_FORMAT_OBITI, 'obiti.zip', '28/08/2017', '27/08/2018'),
        (DATA_FORMAT_NEPTUNE, 'neptune.zip', '21/12/2017', '27/02/2018'),
    ])
    def test_data_update_other_data_formats(self, fusio_call, wait_for_action_terminated, init_http_download_server,
                                            data_format, file_name, begin_date, end_date):
        sid = 'my_sid'
        url = self.format_url(ip=init_http_download_server.ip_addr,
                              filename=file_name,
                              path='validity_period/other_data_formats')
        self.init_contributor('cid', 'dsid', url, data_format=data_format, service_id=sid)
        self.__init_coverage("jdr", ["cid"], ["dsid"])

        content = self.get_fusio_response_from_action_id(42)

        fusio_call.return_value = get_response(200, content)
        self.full_export('cid', 'jdr', '2017-08-10')

        assert fusio_call.call_count == 1
        assert fusio_call.call_args_list[0][1]['data'] == {
            'DateDebut': begin_date,
            'DateFin': end_date,
            'action': 'dataupdate',
            'content-type': 'multipart/form-data',
            'contributorexternalcode': 'cid_prefix',
            'dutype': 'update',
            'isadapted': 0,
            'libelle': 'unlibelle',
            'serviceid': sid
        }

    def test_data_update_past_period(self, init_http_download_server):
        url = self.format_url(ip=init_http_download_server.ip_addr,
                              filename='gtfs_with_feed_info_more_than_one_year.zip')
        self.init_contributor('cid', 'dsid', url, service_id='1')
        self.__init_coverage("jdr", ["cid"], ["dsid"])
        # end date is 31/12/2018
        resp = self.full_export('cid', 'jdr', '2019-03-10')
        job = self.get_job_from_export_response(resp)
        assert job['state'] == 'done'
        assert job['step'] == 'save_coverage_export'
        assert job['error_message'] == ''


class TestFusioImportPreprocess(TartareFixture):
    @mock.patch('tartare.processes.fusio.Fusio.wait_for_action_terminated')
    @mock.patch('tartare.processes.fusio.Fusio.call')
    def test_import_period(self, fusio_call, wait_for_action_terminated, init_http_download_server):
        url = self.format_url(ip=init_http_download_server.ip_addr,
                              filename='gtfs_with_feed_info_more_than_one_year.zip')
        self.init_contributor('cid', 'dsid', url)
        self.init_coverage('jdr', ['cid'], ['dsid'])
        preprocess = {
            "id": "fusio_import",
            "type": "FusioImport",
            "params": {
                "url": "http://fusio_host/cgi-bin/fusio.dll/"
            },
            "sequence": 0
        }
        self.add_preprocess_to_coverage(preprocess, 'jdr')

        content = self.get_fusio_response_from_action_id(42)

        fusio_call.return_value = get_response(200, content)
        self.full_export('cid', 'jdr', '2016-05-10')

        assert fusio_call.call_count == 1
        assert fusio_call.call_args_list[0][1]['data'] == {
            'DateDebut': '03/05/2016',
            'DateFin': '02/05/2017',
            'action': 'regionalimport',
        }


class TestFusioExportPreprocess(TartareFixture):
    @mock.patch('tartare.processes.fusio.Fusio.replace_url_hostname_from_url')
    @mock.patch('tartare.processes.fusio.Fusio.wait_for_action_terminated')
    @mock.patch('requests.post')
    @mock.patch('requests.get')
    def test_fusio_export_avoid_merge_and_use_fusio_export_file(self,
                                                                fusio_get,
                                                                fusio_post,
                                                                wait_for_action_terminated,
                                                                replace_url_hostname_from_url,
                                                                init_http_download_server):
        filename = 'gtfs-1.zip'
        url = self.format_url(ip=init_http_download_server.ip_addr,
                              filename=filename,
                              path='gtfs/historisation')
        self.init_contributor("id_test", "my_gtfs", url)
        fusio_end_point = 'http://fusio_host/cgi-bin/fusio.dll/'
        coverage = {
            "id": "my_cov",
            "name": "my_cov",
            "contributors_ids": ['id_test'],
            "input_data_source_ids": ["my_gtfs"],
            "preprocesses":
                [
                    {
                        "id": "fusio_export",
                        "type": "FusioExport",
                        "params": {
                            "url": fusio_end_point,
                            "export_type": "ntfs",
                        },
                        "sequence": 0
                    }
                ]

        }
        raw = self.post('/coverages', self.dict_to_json(coverage))
        self.assert_sucessful_create(raw)

        post_content = self.get_fusio_response_from_action_id(42)
        fetch_url = self.format_url(ip=init_http_download_server.ip_addr, filename='sample_1.zip')
        get_content = self.get_fusio_export_url_response_from_action_id(42, "http://fusio/ntfs.zip")

        replace_url_hostname_from_url.return_value = fetch_url
        fusio_post.return_value = get_response(200, post_content)
        fusio_get.return_value = get_response(200, get_content)
        expected_data = {
            'action': 'Export',
            'ExportType': 32,
            'Source': 4
        }

        resp = self.full_export('id_test', 'my_cov', '2017-08-10')

        fusio_post.assert_called_with(fusio_end_point + 'api', data=expected_data, files=None)
        fusio_get.assert_called_with(fusio_end_point + 'info', data=None, files=None)

        job = self.get_job_from_export_response(resp)
        assert job['state'] == 'done', print(job)
        assert job['step'] == 'save_coverage_export', print(job)
        assert job['error_message'] == '', print(job)

        fixtures_file = _get_file_fixture_full_path('gtfs/{}'.format('sample_1.zip'))

        raw = self.get('coverages/{coverage_id}/exports'.format(coverage_id=coverage['id']))
        self.assert_sucessful_call(raw)
        exports = self.json_to_dict(raw).get('exports')
        assert len(exports) == 1

        resp = self.get('/files/{gridfs_id}/download'.
                        format(coverage_id=coverage['id'], export_id=exports[0]['id'],
                               gridfs_id=exports[0]['gridfs_id']), follow_redirects=True)
        self.assert_sucessful_call(raw)
        assert_text_files_equals(resp.data, fixtures_file)

    @mock.patch('tartare.processes.fusio.Fusio.replace_url_hostname_from_url')
    @mock.patch('tartare.processes.fusio.Fusio.wait_for_action_terminated')
    @mock.patch('requests.post')
    @mock.patch('requests.get')
    def test_fusio_export_to_data_source(self,
                                         fusio_get,
                                         fusio_post,
                                         wait_for_action_terminated,
                                         replace_url_hostname_from_url,
                                         init_http_download_server):
        filename = 'gtfs-1.zip'
        output_fixture = 'sample_1.zip'
        coverage_id = 'my_cov'
        url = self.format_url(ip=init_http_download_server.ip_addr,
                              filename=filename,
                              path='gtfs/historisation')
        self.init_contributor("id_test", "my_gtfs", url)
        fusio_end_point = 'http://fusio_host/cgi-bin/fusio.dll/'
        target_id = "my_export_data_source"
        preprocess = {
            "id": "fusio_export",
            "type": "FusioExport",
            "params": {
                "url": fusio_end_point,
                "target_data_source_id": target_id,
                "export_type": "ntfs"
            },
            "sequence": 0
        }

        self.init_coverage(coverage_id, ['id_test'], ["my_gtfs"], [preprocess])

        post_content = self.get_fusio_response_from_action_id(42)
        fetch_url = self.format_url(ip=init_http_download_server.ip_addr, filename=output_fixture)
        get_content = self.get_fusio_export_url_response_from_action_id(42, "http://fusio/ntfs.zip")

        replace_url_hostname_from_url.return_value = fetch_url
        fusio_post.return_value = get_response(200, post_content)
        fusio_get.return_value = get_response(200, get_content)

        self.full_export('id_test', 'my_cov', '2017-08-10')

        fixtures_file = _get_file_fixture_full_path('gtfs/{}'.format(output_fixture))
        coverage = self.json_to_dict(self.get('/coverages/{}'.format(coverage_id)))['coverages'][0]
        assert 'data_sources' in coverage
        assert len(coverage['data_sources']) == 1
        assert coverage['data_sources'][0]['id'] == target_id
        assert 'data_sets' in coverage['data_sources'][0]
        assert len(coverage['data_sources'][0]['data_sets']) == 1
        gridfs_id = coverage['data_sources'][0]['data_sets'][0]['gridfs_id']
        resp = self.get('/files/{gridfs_id}/download'.format(gridfs_id=gridfs_id), follow_redirects=True)
        assert_text_files_equals(resp.data, fixtures_file)

    @pytest.mark.parametrize("export_type,expected_message", [
        (None,
         'export_type mandatory in preprocess fusio_export parameters (possible values: ntfs,gtfs,google_transit)'),
        ('obiti',
         'export_type obiti is not handled by preprocess FusioExport, possible values: ntfs,gtfs,google_transit)')
    ])
    def test_fusio_export_missing_export_type(self, init_http_download_server, export_type, expected_message):
        url = self.format_url(ip=init_http_download_server.ip_addr,
                              filename='gtfs-1.zip',
                              path='gtfs/historisation')

        self.init_contributor("id_test", "my_gtfs", url)
        preprocess = {
            "id": "fusio_export",
            "type": "FusioExport",
            "params": {
                "url": 'http://whatever.com',
                "target_data_source_id": "whatever_id"
            },
            "sequence": 0
        }
        if export_type:
            preprocess['params']['export_type'] = export_type

        self.init_coverage('cov_id', ['id_test'], ["my_gtfs"], [preprocess])
        resp = self.coverage_export('cov_id')
        job = self.get_job_from_export_response(resp)
        assert job['step'] == 'preprocess'
        assert job['state'] == 'failed'
        assert job['error_message'] == expected_message


class TestFusioExportContributorPreprocess(TartareFixture):
    @mock.patch('tartare.processes.fusio.Fusio.replace_url_hostname_from_url')
    @mock.patch('tartare.processes.fusio.Fusio.wait_for_action_terminated')
    @mock.patch('requests.post')
    @mock.patch('tartare.processes.fusio.Fusio.get_export_url')
    def test_fusio_export_contributor(self,
                                      fusio_get,
                                      fusio_post,
                                      wait_for_action_terminated,
                                      replace_url_hostname_from_url,
                                      init_http_download_server, init_ftp_upload_server):
        ftp_username = init_ftp_upload_server.user
        ftp_password = init_ftp_upload_server.password
        filename = 'gtfs-1.zip'
        url = self.format_url(ip=init_http_download_server.ip_addr,
                              filename=filename,
                              path='gtfs/historisation')
        self.init_contributor("id_test", "my_gtfs", url)
        fusio_end_point = 'http://fusio_host/cgi-bin/fusio.dll/'
        trigram = 'LOL'
        expected_file_name = 'my_formatted_gtfs.zip'

        directory = 'my_dir'
        session = ftplib.FTP(init_ftp_upload_server.ip_addr, ftp_username, ftp_password)
        # Create a directory in the ftp
        session.mkd(directory)

        publication_platform = {
            "protocol": "ftp",
            "url": "ftp://" + init_ftp_upload_server.ip_addr,
            "options": {
                "authent": {
                    "username": ftp_username,
                    "password": ftp_password
                },
                "directory": directory
            }
        }
        coverage = {
            "id": "my_cov",
            "name": "my_cov",
            "contributors_ids": ['id_test'],
            "input_data_source_ids": ['my_gtfs'],
            "preprocesses":
                [
                    {
                        "id": "fusio_export_contributor",
                        "type": "FusioExportContributor",
                        "params": {
                            "expected_file_name": expected_file_name,
                            "url": fusio_end_point,
                            'trigram': trigram,
                            'publication_platform': publication_platform,
                        },
                        "sequence": 0
                    }
                ]

        }
        raw = self.post('/coverages', self.dict_to_json(coverage))
        self.assert_sucessful_create(raw)

        post_content = self.get_fusio_response_from_action_id(42)

        replace_url_hostname_from_url.return_value = url
        fusio_post.return_value = get_response(200, post_content)
        expected_data = {
            'action': 'Export',
            'ExportType': 36,
            'Source': 4,
            'ContributorList': 'LOL',
            'Libelle': 'Export auto Tartare LOL',
            'isadapted': 0
        }

        resp = self.full_export('id_test', 'my_cov', '2017-08-10')

        fusio_post.assert_called_with(fusio_end_point + 'api', data=expected_data, files=None)

        job = self.get_job_from_export_response(resp)
        assert job['state'] == 'done', print(job)
        assert job['step'] == 'save_coverage_export', print(job)
        assert job['error_message'] == '', print(job)

        # check if the file was successfully uploaded
        directory_content = session.nlst(directory)
        assert len(directory_content) == 1
        assert expected_file_name in directory_content
        session.delete('{directory}/{filename}'.format(directory=directory, filename=expected_file_name))
        session.rmd(directory)


class TestFusioSendPtExternalSettingsPreprocess(TartareFixture):
    @mock.patch('tartare.processes.fusio.Fusio.wait_for_action_terminated')
    @mock.patch('tartare.processes.fusio.Fusio.call')
    def test_fusio_send_pt_external_settings(self, fusio_call, wait_for_action_terminated, init_http_download_server):
        url = self.format_url(ip=init_http_download_server.ip_addr,
                              filename='fr-idf-custo-post-fusio-sample.zip',
                              path='prepare_external_settings')
        contributor_id = 'cid'
        self.init_contributor('cid', 'gtfs_id', url, data_prefix='OIF')
        external_settings_ds_id = "my_external_settings_data_source_id"

        self.add_preprocess_to_contributor({
            "data_source_ids": [
                "gtfs_id"
            ],
            "id": "compute_ext_settings",
            "type": "ComputeExternalSettings",
            "sequence": 0,
            "params": {
                "target_data_source_id": external_settings_ds_id,
                "export_type": DATA_FORMAT_PT_EXTERNAL_SETTINGS,
                "links": [
                    {
                        "contributor_id": contributor_id,
                        "data_source_id": "my-data-source-of-perimeter-json-id"
                    },
                    {
                        "contributor_id": contributor_id,
                        "data_source_id": "my-data-source-of-lines-json-id"
                    }
                ],
            }
        }, contributor_id)

        self.add_data_source_to_contributor(
            contributor_id, 'my-data-source-of-perimeter-json-id', self.format_url(
                init_http_download_server.ip_addr, 'tr_perimeter_id.json', 'prepare_external_settings'),
            DATA_FORMAT_TR_PERIMETER
        )
        self.add_data_source_to_contributor(
            contributor_id, 'my-data-source-of-lines-json-id', self.format_url(
                init_http_download_server.ip_addr, 'lines_referential_id.json', 'prepare_external_settings'),
            DATA_FORMAT_LINES_REFERENTIAL
        )

        coverage_id = 'covid'
        coverage = self.init_coverage(coverage_id, [contributor_id], ["gtfs_id"])
        coverage['preprocesses'].append({
            "id": "send_ext_settings",
            "params": {
                "url": "http://fusio.whatever.com",
                "input_data_source_ids": [external_settings_ds_id]
            },
            "type": "FusioSendPtExternalSettings",
            "sequence": 0
        })
        raw = self.put('/coverages/covid', params=self.dict_to_json(coverage))
        self.assert_sucessful_call(raw)

        content = self.get_fusio_response_from_action_id(42)
        fusio_call.return_value = get_response(200, content)

        self.full_export(contributor_id, coverage_id)

        assert fusio_call.call_count == 1
        assert fusio_call.call_args_list[0][1]['data'] == {'action': 'externalstgupdate'}
        assert 'filename' in fusio_call.call_args_list[0][1]['files']
        fusio_settings_zip_file = fusio_call.call_args_list[0][1]['files']['filename']
        with ZipFile(fusio_settings_zip_file, 'r') as fusio_settings_zip_file:
            with tempfile.TemporaryDirectory() as tmp_dir_name:
                assert_zip_contains_only_files_with_extensions(fusio_settings_zip_file, ['txt'])
                fusio_settings_zip_file.extractall(tmp_dir_name)
                assert_text_files_equals(os.path.join(tmp_dir_name, 'fusio_object_codes.txt'),
                                         _get_file_fixture_full_path(
                                        'prepare_external_settings/expected_fusio_object_codes.txt'))
                assert_text_files_equals(os.path.join(tmp_dir_name, 'fusio_object_properties.txt'),
                                         _get_file_fixture_full_path(
                                        'prepare_external_settings/expected_fusio_object_properties.txt'))
