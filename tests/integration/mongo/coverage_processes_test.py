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
from freezegun import freeze_time

from tartare import app
from tartare.core.constants import DATA_FORMAT_OBITI, DATA_FORMAT_TITAN, DATA_FORMAT_NEPTUNE, \
    DATA_FORMAT_TR_PERIMETER, DATA_FORMAT_LINES_REFERENTIAL, DATA_FORMAT_GTFS, \
    DATA_FORMAT_NTFS, ACTION_TYPE_COVERAGE_EXPORT
from tartare.core.gridfs_handler import GridFsHandler
from tests.integration.test_mechanism import TartareFixture
from tests.utils import get_response, assert_text_files_equals, _get_file_fixture_full_path, \
    assert_zip_contains_only_files_with_extensions


class TestFusioDataUpdateProcess(TartareFixture):
    data_update_process = {
        "id": "fusio_dataupdate",
        "type": "FusioDataUpdate",
        "params": {
            "url": "http://fusio_host/cgi-bin/fusio.dll/"
        },
        "sequence": 0
    }

    def __create_data_source(self, data_source_id, url, service_id='Google-1', name=None):
        if not name:
            name = data_source_id

        return {
            "id": data_source_id,
            "name": name,
            "service_id": service_id,
            "input": {
                "type": "auto",
                "url": url,
                "frequency": {
                    "type": "daily",
                    "hour_of_day": 20
                }
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

    def __init_coverage(self, coverage_id, input_data_source_ids):
        coverage = {
            "id": coverage_id,
            "name": "name of the coverage jdr",
            "input_data_source_ids": input_data_source_ids,
            "processes": [
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
    # And   I create a coverage containing this contributor and a process FusioDataUpdate
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
        self.init_contributor('id_test', 'my_gtfs', url, export_id='export_id', service_id='Google-1')
        self.init_coverage('jdr', ['export_id'], processes=[self.data_update_process])

        content = self.get_fusio_response_from_action_id(42)
        fusio_call.return_value = get_response(200, content)

        self.full_export('id_test', 'jdr', '2017-08-10')
        self.full_export('id_test', 'jdr', '2017-08-10')

        assert fusio_call.call_count == 2

    # Given I create a contributor with a data source with service_id null
    # And   I create a coverage containing this contributor and a process FusioDataUpdate
    # When  I do a contributor export on this contributor (and then a coverage export)
    # Then  FusioDataUpdate should fail because service_id is null
    def test_data_update_fail_if_data_source_has_service_id_null(self, init_http_download_server):
        filename = 'gtfs-{number}.zip'
        url = self.format_url(ip=init_http_download_server.ip_addr,
                              filename=filename.format(number=1),
                              path='gtfs/historisation')
        self.init_contributor('id_test', 'my_gtfs', url, export_id='export_id')
        self.init_coverage('jdr', ['export_id'], processes=[self.data_update_process])

        response = self.full_export('id_test', 'jdr', '2017-08-10')
        self.assert_sucessful_call(response, 201)

        job_details = self.get_job_details(self.json_to_dict(response)['job']['id'])

        assert job_details['state'] == 'failed'
        assert job_details[
                   'error_message'] == 'service_id of data source export_id of contributor id_test should not be null'

    @mock.patch('tartare.processes.fusio.Fusio.wait_for_action_terminated')
    @mock.patch('tartare.processes.fusio.Fusio.call')
    # Given I create a contributor with 2 data sources
    # And   I create a coverage containing this contributor and a process FusioDataUpdate
    # When  I do a contributor export on this contributor (and then a coverage export)
    # Then  I can see that Fusio has been called twice
    # And   Each data source service id is used
    def test_data_update_one_contributor_with_two_data_sources(self, fusio_call, wait_for_action_terminated,
                                                               init_http_download_server):
        filename = 'gtfs-{number}.zip'
        url = self.format_url(ip=init_http_download_server.ip_addr,
                              filename=filename.format(number=1),
                              path='gtfs/historisation')
        self.init_contributor('id_test', 'my_gtfs', url, export_id='export_id_1', service_id='Google-1')
        self.add_data_source_to_contributor('id_test', 'my_gtfs_2', url, export_id='export_id_2', service_id='Google-2')
        self.init_coverage('jdr', ['export_id_1', 'export_id_2'], processes=[self.data_update_process])

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
        self.init_coverage("jdr", ["dsid"], processes=[self.data_update_process])

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
        self.init_coverage("jdr", ["dsid"])
        # end date is 31/12/2018
        resp = self.full_export('cid', 'jdr', '2019-03-10')
        job = self.get_job_from_export_response(resp)
        assert job['state'] == 'done'
        assert job['step'] == 'save_coverage_export'
        assert job['error_message'] == ''


class TestFusioImportProcess(TartareFixture):
    @mock.patch('tartare.processes.fusio.Fusio.wait_for_action_terminated')
    @mock.patch('tartare.processes.fusio.Fusio.call')
    def test_import_period(self, fusio_call, wait_for_action_terminated, init_http_download_server):
        url = self.format_url(ip=init_http_download_server.ip_addr,
                              filename='gtfs_with_feed_info_more_than_one_year.zip')
        self.init_contributor('cid', 'dsid', url)
        self.init_coverage('jdr', ['dsid'])
        process = {
            "id": "fusio_import",
            "type": "FusioImport",
            "params": {
                "url": "http://fusio_host/cgi-bin/fusio.dll/"
            },
            "sequence": 0
        }
        self.add_process_to_coverage(process, 'jdr')

        content = self.get_fusio_response_from_action_id(42)

        fusio_call.return_value = get_response(200, content)
        self.full_export('cid', 'jdr', '2016-05-10')

        assert fusio_call.call_count == 1
        assert fusio_call.call_args_list[0][1]['data'] == {
            'DateDebut': '03/05/2016',
            'DateFin': '02/05/2017',
            'action': 'regionalimport',
        }

    @mock.patch('tartare.processes.fusio.Fusio.wait_for_action_terminated')
    @mock.patch('tartare.processes.fusio.Fusio.call')
    def test_import_invalid_dates(self, fusio_call, wait_for_action_terminated, init_http_download_server):
        url = self.format_url(ip=init_http_download_server.ip_addr,
                              filename='gtfs_with_feed_info_more_than_one_year.zip')
        self.init_contributor('cid', 'dsid', url)
        self.init_coverage('jdr', ['dsid'])
        process = {
            "id": "fusio_import",
            "type": "FusioImport",
            "params": {
                "url": "http://fusio_host/cgi-bin/fusio.dll/"
            },
            "sequence": 0
        }
        self.add_process_to_coverage(process, 'jdr')

        content = self.get_fusio_response_from_action_id(42)

        fusio_call.return_value = get_response(200, content)
        resp = self.full_export('cid', 'jdr', '2019-05-10')
        job = self.get_job_from_export_response(resp)
        assert job['state'] == 'failed'
        assert job['step'] == 'process'
        assert job['action_type'] == ACTION_TYPE_COVERAGE_EXPORT
        assert job[
                   'error_message'] == 'bounds date for fusio import incorrect: calculating validity period union on past periods (end_date: 31/12/2018 < now: 10/05/2019)'


class TestFusioExportProcess(TartareFixture):
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
            "input_data_source_ids": ["my_gtfs"],
            "processes":
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
        process = {
            "id": "fusio_export",
            "type": "FusioExport",
            "params": {
                "url": fusio_end_point,
                "target_data_source_id": target_id,
                "export_type": "ntfs"
            },
            "sequence": 0
        }

        self.init_coverage(coverage_id, ["my_gtfs"], [process])

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
         'export_type mandatory in process fusio_export parameters (possible values: ntfs,gtfs,google_transit)'),
        ('obiti',
         'export_type obiti is not handled by process FusioExport, possible values: ntfs,gtfs,google_transit)')
    ])
    def test_fusio_export_missing_export_type(self, init_http_download_server, export_type, expected_message):
        url = self.format_url(ip=init_http_download_server.ip_addr,
                              filename='gtfs-1.zip',
                              path='gtfs/historisation')

        self.init_contributor("id_test", "my_gtfs", url)
        process = {
            "id": "fusio_export",
            "type": "FusioExport",
            "params": {
                "url": 'http://whatever.com',
                "target_data_source_id": "whatever_id"
            },
            "sequence": 0
        }
        if export_type:
            process['params']['export_type'] = export_type

        self.init_coverage('cov_id', ["my_gtfs"], [process])
        resp = self.coverage_export('cov_id')
        job = self.get_job_from_export_response(resp)
        assert job['step'] == 'process'
        assert job['state'] == 'failed'
        assert job['error_message'] == expected_message


class TestFusioExportContributorProcess(TartareFixture):
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
            "input_data_source_ids": ['my_gtfs'],
            "processes":
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


class TestFusioPreProdProcess(TartareFixture):
    @mock.patch('tartare.processes.fusio.Fusio.wait_for_action_terminated')
    @mock.patch('tartare.processes.fusio.Fusio.call')
    def test_fusio_preprod(self, fusio_call, wait_for_action_terminated, init_http_download_server):
        url = self.format_url(init_http_download_server.ip_addr, 'some_archive.zip')
        self.init_contributor('cid', 'gtfs_id', url)
        self.init_coverage('covid', ['gtfs_id'], [
            {
                "type": "FusioPreProd",
                "params": {
                    "url": "http://fusio_host/cgi-bin/fusio.dll/"
                },
                "sequence": 0
            }
        ])
        content = self.get_fusio_response_from_action_id(42)
        fusio_call.return_value = get_response(200, content)
        resp = self.full_export('cid', 'covid')
        assert fusio_call.call_count == 1
        assert fusio_call.call_args_list[0][1]['data'] == {'action': 'settopreproduction'}
        job = self.get_job_from_export_response(resp)
        assert job['state'] == 'done'
        assert job['step'] == 'save_coverage_export'
        assert job['action_type'] == ACTION_TYPE_COVERAGE_EXPORT


class TestFusioSendPtExternalSettingsProcess(TartareFixture):
    @mock.patch('tartare.processes.fusio.Fusio.wait_for_action_terminated')
    @mock.patch('tartare.processes.fusio.Fusio.call')
    def test_fusio_send_pt_external_settings(self, fusio_call, wait_for_action_terminated, init_http_download_server):
        url = self.format_url(ip=init_http_download_server.ip_addr,
                              filename='fr-idf-custo-post-fusio-sample.zip',
                              path='prepare_external_settings')
        contributor_id = 'cid'
        self.init_contributor('cid', 'gtfs_id', url, data_prefix='OIF')
        external_settings_ds_id = "my_external_settings_data_source_id"

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

        self.add_process_to_contributor({
            "input_data_source_ids": [
                "gtfs_id"
            ],
            "id": "compute_ext_settings",
            "type": "ComputeExternalSettings",
            "sequence": 0,
            "target_data_source_id": external_settings_ds_id,
            'configuration_data_sources': [
                {'name': 'perimeter', 'ids': ['my-data-source-of-perimeter-json-id']},
                {'name': 'lines_referential', 'ids': ['my-data-source-of-lines-json-id']},
            ]
        }, contributor_id)

        coverage_id = 'covid'
        coverage = self.init_coverage(coverage_id, ["gtfs_id"])
        coverage['processes'].append({
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


class TestComputeODSProcess(TartareFixture):
    @freeze_time("2018-05-14")
    def test_process_compute_ods(self, init_http_download_server):
        cov_id = 'my-coverage-id'
        self.init_contributor('cid',
                              'ds_gtfs',
                              self.format_url(init_http_download_server.ip_addr, 'some_archive.zip'),
                              data_format=DATA_FORMAT_GTFS)
        self.add_data_source_to_contributor('cid', 'ds_ntfs',
                                            self.format_url(init_http_download_server.ip_addr, 'ntfs.zip', ''),
                                            DATA_FORMAT_NTFS)

        process = {
            'id': 'compute-ods',
            'type': 'ComputeODS',
            'input_data_source_ids': ['ds_gtfs', 'ds_ntfs'],
            "target_data_source_id": "target_id",
            'sequence': 0
        }
        self.init_coverage(cov_id,
                           input_data_source_ids=['ds_gtfs', 'ds_ntfs'],
                           processes=[process],
                           license={
                               "name": 'my license',
                               "url": 'http://license.org/mycompany'
                           })

        self.full_export('cid', cov_id)

        def test_ods_file_exist(_extract_path):
            with app.app_context():
                expected_filename = '{coverage_id}.zip'.format(coverage_id=cov_id)
                target_grid_fs_id = self.get_gridfs_id_from_data_source_of_coverage(cov_id, "target_id")
                ods_zip_file = GridFsHandler().get_file_from_gridfs(target_grid_fs_id)
                assert ods_zip_file.filename == expected_filename

            return ods_zip_file

        self.assert_ods_metadata(cov_id, test_ods_file_exist)
