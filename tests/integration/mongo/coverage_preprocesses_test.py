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

import mock

from tests.integration.test_mechanism import TartareFixture
from tests.utils import get_response, assert_files_equals, _get_file_fixture_full_path


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
        self.assert_sucessful_call(raw, 201)

    def __init_coverage(self, coverage_id, contributor_ids):
        coverage = {
            "id": coverage_id,
            "name": "name of the coverage jdr",
            "contributors": contributor_ids,
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
        self.assert_sucessful_call(raw, 201)

    @mock.patch('tartare.processes.fusio.Fusio.wait_for_action_terminated')
    @mock.patch('tartare.processes.fusio.Fusio.call')
    # Given I create a contributor with a data source
    # And   I create a coverage containing this contributor and a preprocess FusioDataUpdate
    # And   I do a contributor export on this contributor (and then a coverage export)
    # When  I update the data source url (or the data set has changed)
    # And   I do a contributor export on this contributor (and then a coverage export)
    # Then  I can see that Fusio has been called 2 time(s) in total
    # => because one time for the first coverage export (normal) and one other because the data set has changed
    def test_data_update_called_if_data_source_updated(self, fusio_call, wait_for_action_terminated,
                                                       init_http_download_server):
        filename = 'gtfs-{number}.zip'

        url = self.format_url(ip=init_http_download_server.ip_addr,
                              filename=filename.format(number=1),
                              path='gtfs/historisation')

        self.__init_contributor("id_test", [self.__create_data_source("my_gtfs",  url)])
        self.__init_coverage("jdr", ["id_test"])

        content = self.get_fusio_response_from_action_id(42)
        fusio_call.return_value = get_response(200, content)

        self.full_export('id_test', 'jdr', '2017-08-10')

        url = self.format_url(ip=init_http_download_server.ip_addr,
                              filename=filename.format(number=2),
                              path='gtfs/historisation')

        raw = self.patch('/contributors/id_test/data_sources/my_gtfs',
                         json.dumps({"input": {"url": url}}))
        self.assert_sucessful_call(raw)

        self.full_export('id_test', 'jdr', '2017-08-10')

        assert fusio_call.call_count == 2

    @mock.patch('tartare.processes.fusio.Fusio.wait_for_action_terminated')
    @mock.patch('tartare.processes.fusio.Fusio.call')
    # Given I create a contributor with a data source
    # And   I create a coverage containing this contributor and a preprocess FusioDataUpdate
    # And   I do a contributor export on this contributor (and then a coverage export)
    # When  I do a contributor export on this contributor (and then a coverage export)
    # Then  I can see that Fusio has been called 1 time(s) in total
    # => because one time for the first coverage export (normal) and second export does not need any data update
    def test_data_update_called_if_data_source_not_updated(self, fusio_call, wait_for_action_terminated,
                                                           init_http_download_server):
        filename = 'gtfs-{number}.zip'
        url = self.format_url(ip=init_http_download_server.ip_addr,
                              filename=filename.format(number=1),
                              path='gtfs/historisation')
        self.__init_contributor("id_test", [self.__create_data_source("my_gtfs",  url)])
        self.__init_coverage("jdr", ["id_test"])

        content = self.get_fusio_response_from_action_id(42)
        fusio_call.return_value = get_response(200, content)

        self.full_export('id_test', 'jdr', '2017-08-10')
        self.full_export('id_test', 'jdr', '2017-08-10')

        assert fusio_call.call_count == 1

    @mock.patch('tartare.processes.fusio.Fusio.wait_for_action_terminated')
    @mock.patch('tartare.processes.fusio.Fusio.call')
    # Given I create a contributor with a data source
    # And   I create a coverage containing this contributor and a preprocess FusioDataUpdate
    # And   I do a contributor export on this contributor (and then a coverage export)
    # And   I delete the data source of the contributor
    # And   I add the deleted data source with a new id
    # When  I do a contributor export on this contributor (and then a coverage export)
    # Then  I can see that Fusio has been called 2 time(s) in total
    # => because one time for the first coverage export (normal) and one other because we cannot perform comparison
    #    of the data sets (data source id has changed)
    def test_data_update_called_if_data_source_deleted_and_recreated_with_new_id(self, fusio_call,
                                                                                 wait_for_action_terminated,
                                                                                 init_http_download_server):
        filename = 'gtfs-1.zip'
        url = self.format_url(ip=init_http_download_server.ip_addr,
                              filename=filename,
                              path='gtfs/historisation')
        self.__init_contributor("id_test", [self.__create_data_source("my_gtfs",  url)])
        self.__init_coverage("jdr", ["id_test"])

        content = self.get_fusio_response_from_action_id(42)
        fusio_call.return_value = get_response(200, content)

        self.full_export('id_test', 'jdr', '2017-08-10')
        raw = self.delete('/contributors/id_test/data_sources/my_gtfs')
        self.assert_sucessful_call(raw, 204)
        new_data_source = {
            "id": 'other_gtfs',
            "name": "other_gtfs",
            "service_id": "Google-2",
            "input": {
                "type": "url",
                "url": url
            }
        }
        raw = self.post('/contributors/id_test/data_sources', json.dumps(new_data_source))
        self.assert_sucessful_call(raw, 201)

        self.full_export('id_test', 'jdr', '2017-08-10')

        assert fusio_call.call_count == 2

    @mock.patch('tartare.processes.fusio.Fusio.wait_for_action_terminated')
    @mock.patch('tartare.processes.fusio.Fusio.call')
    # Given I create a contributor with a data source
    # And   I create a coverage containing this contributor and a preprocess FusioDataUpdate
    # And   I do a contributor export on this contributor (and then a coverage export)
    # And   I add an other data source to the contributor
    # When  I do a contributor export on this contributor (and then a coverage export)
    # Then  I can see that Fusio has been called 2 time(s) in total
    # => because one time for the first coverage export (normal) and one other because the new data source needs one
    #    data update and the first one's data set has not changed
    def test_data_update_called_if_data_source_added_to_contributor(self, fusio_call, wait_for_action_terminated,
                                                                    init_http_download_server):
        filename = 'gtfs-1.zip'
        url = self.format_url(ip=init_http_download_server.ip_addr,
                              filename=filename,
                              path='gtfs/historisation')
        self.__init_contributor("id_test", [self.__create_data_source("my_gtfs",  url)])
        self.__init_coverage("jdr", ["id_test"])

        content = self.get_fusio_response_from_action_id(42)
        fusio_call.return_value = get_response(200, content)

        self.full_export('id_test', 'jdr', '2017-08-10')
        new_data_source = {
            "id": 'other_gtfs',
            "name": "other_gtfs",
            "service_id": "Google-2",
            "input": {
                "type": "url",
                "url": url
            }
        }
        raw = self.post('/contributors/id_test/data_sources', json.dumps(new_data_source))
        self.assert_sucessful_call(raw, 201)

        self.full_export('id_test', 'jdr', '2017-08-10')

        assert fusio_call.call_count == 2

    @mock.patch('tartare.processes.fusio.Fusio.wait_for_action_terminated')
    @mock.patch('tartare.processes.fusio.Fusio.call')
    # Given I create a contributor with a data source
    # And   I create a coverage containing this contributor and a preprocess FusioDataUpdate
    # And   I do a contributor export on this contributor (and then a coverage export)
    # And   I create an other contributor with a data source
    # And   I add this other contributor to the coverage
    # When  I do a contributor export on this other contributor (and then a coverage export)
    # Then  I can see that Fusio has been called 2 time(s) in total
    # => because one time for the first coverage export (normal) and one other because the new contributor needs one
    #    data update and the first one's data set has not changed
    def test_data_update_called_if_contributor_added(self, fusio_call, wait_for_action_terminated,
                                                     init_http_download_server):
        filename = 'gtfs-1.zip'
        url = self.format_url(ip=init_http_download_server.ip_addr,
                              filename=filename,
                              path='gtfs/historisation')
        self.__init_contributor("id_test", [self.__create_data_source("my_gtfs",  url)])
        self.__init_coverage("jdr", ["id_test"])

        content = self.get_fusio_response_from_action_id(42)
        fusio_call.return_value = get_response(200, content)

        self.full_export('id_test', 'jdr', '2017-08-10')

        self.__init_contributor("id_test_2", [self.__create_data_source("my_gtfs_2",  url)], 'BBB')
        raw = self.post('/coverages/jdr/contributors', json.dumps({'id': 'id_test_2'}))
        self.assert_sucessful_call(raw, 201)

        self.full_export('id_test_2', 'jdr', '2017-08-10')

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
        self.__init_contributor("id_test", [self.__create_data_source("my_gtfs",  url, service_id=None)])
        self.__init_coverage("jdr", ["id_test"])

        response = self.full_export('id_test', 'jdr', '2017-08-10')
        self.assert_sucessful_call(response, 201)

        job_details = self.get_job_details(self.json_to_dict(response)['job']['id'])

        assert job_details['state'] == 'failed'
        assert job_details['error_message'] == 'service_id of data source id_test of contributor my_gtfs should not be null'

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
        self.__init_coverage("jdr", ["id_test"])

        content = self.get_fusio_response_from_action_id(42)

        fusio_call.return_value = get_response(200, content)
        self.full_export('id_test', 'jdr', '2017-08-10')

        assert fusio_call.call_count == 2
        assert fusio_call.call_args_list[0][1]['data']['serviceexternalcode'] == 'Google-1'
        assert fusio_call.call_args_list[1][1]['data']['serviceexternalcode'] == 'Google-2'


class TestFusioExportPreprocess(TartareFixture):
    @mock.patch('tartare.processes.fusio.Fusio.wait_for_action_terminated')
    @mock.patch('requests.post')
    @mock.patch('requests.get')
    def test_fusio_export_avoid_merge_and_use_fusio_export_file(self, fusio_get, fusio_post, wait_for_action_terminated, init_http_download_server):
        filename = 'gtfs-1.zip'
        url = self.format_url(ip=init_http_download_server.ip_addr,
                              filename=filename,
                              path='gtfs/historisation')
        self.init_contributor("id_test", "my_gtfs", url)
        fusio_end_point = 'http://fusio_host/cgi-bin/fusio.dll/'
        coverage = {
            "id": "my_cov",
            "name": "my_cov",
            "contributors": ['id_test'],
            "preprocesses":
            [
                {
                    "id": "fusio_export",
                    "type": "FusioExport",
                    "params": {
                        "url": fusio_end_point
                    },
                    "sequence": 0
                }
            ]

        }
        raw = self.post('/coverages', self.dict_to_json(coverage))
        self.assert_sucessful_call(raw, 201)

        post_content = """<?xml version="1.0" encoding="ISO-8859-1"?>
                        <serverfusio>
                            <ActionId>42</ActionId>
                        </serverfusio>"""
        fetch_url = self.format_url(ip=init_http_download_server.ip_addr, filename='sample_1.zip')
        get_content = """<?xml version="1.0" encoding="ISO-8859-1"?>
        <Info>
            <ActionList ActionCount="1" TerminatedCount="1" WaitingCount="0" AbortedCount="0" WorkingCount="0"
                        ThreadSuspended="True">
                <Action ActionType="Export" ActionCaption="export" ActionDesc="" Contributor="" ContributorId="-1"
                        ActionId="42" LastError="">
                    <ActionProgression Status="Terminated"
                                       Description="{url}"
                                       StepCount="10" CurrentStep="10"/>
                </Action>
            </ActionList>
        </Info>""".format(url=fetch_url)

        fusio_post.return_value = get_response(200, post_content)
        fusio_get.return_value = get_response(200, get_content)
        expected_data = {
            'action': 'Export',
            'ExportType': 32,
            'Source': 4}

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

        resp = self.get('/coverages/{coverage_id}/exports/{export_id}/files/{gridfs_id}'.
                        format(coverage_id=coverage['id'], export_id=exports[0]['id'],
                               gridfs_id=exports[0]['gridfs_id']), follow_redirects=True)
        self.assert_sucessful_call(raw)
        assert_files_equals(resp.data, fixtures_file)
