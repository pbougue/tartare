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

from tests.integration.test_mechanism import TartareFixture


class TestCoverageStatus(TartareFixture):
    def __run_automatic_update(self):
        raw = self.post('/actions/automatic_update?current_date=2015-08-10')
        self.assert_sucessful_call(raw, 204)

        raw = self.get('/coverages')
        self.assert_sucessful_call(raw, 200)
        return self.json_to_dict(raw)['coverages']

    def __run_coverage_export(self, coverage_id):
        raw = self.post('/coverages/' + coverage_id + '/actions/export?current_date=2015-08-10')
        self.assert_sucessful_create(raw)

        raw = self.get('/coverages')
        self.assert_sucessful_call(raw, 200)
        return self.json_to_dict(raw)['coverages']

    def __create_contributor(self, ip, id="auto_update_contrib", file='some_archive.zip'):
        contributor = {
            "id": id,
            "name": id,
            "data_prefix": id + "_prefix",
            "data_sources": [
                {
                    "id": "ds_" + id,
                    "name": "ds_" + id,
                    "input": {
                        "type": "url",
                        "url": self.format_url(ip, file)
                    }
                }
            ]
        }
        raw = self.post('/contributors', json.dumps(contributor))
        self.assert_sucessful_create(raw)

    def __create_coverage(self, contributors_ids=[], input_data_source_ids=[], coverage_id='auto_update_coverage', publication_platform=None):
        coverage = {
            'id': coverage_id,
            'name': coverage_id,
            'contributors_ids': contributors_ids,
            'input_data_source_ids': input_data_source_ids,
        }
        if contributors_ids:
            coverage['contributors_ids'] = contributors_ids

        if publication_platform:
            coverage["environments"] = {
                "production": {
                    "name": "production",
                    "sequence": 0,
                    "publication_platforms": [
                        publication_platform
                    ]
                }
            }

        raw = self.post('coverages', json.dumps(coverage))
        self.assert_sucessful_create(raw)

    def test_status_after_success_coverage_export_without_contributor(self):
        coverage_id = 'cov_id'
        self.__create_coverage(coverage_id=coverage_id)
        coverages = self.__run_coverage_export(coverage_id)

        assert len(coverages) == 1
        assert 'last_active_job' in coverages[0]
        last_active_job = coverages[0]['last_active_job']
        assert last_active_job['coverage_id'] == coverage_id
        assert last_active_job['contributor_id'] is None
        assert last_active_job['action_type'] == 'coverage_export'
        assert last_active_job['state'] == 'failed', print(last_active_job)
        assert last_active_job['step'] == 'fetching context', print(last_active_job)
        assert last_active_job['error_message'] == \
               'no data sources are attached to coverage {}'.format(
                   coverage_id), print(last_active_job)

    def test_status_after_success_coverage_export_without_contributor_export(self, init_http_download_server):
        self.__create_contributor(init_http_download_server.ip_addr, 'contributor_export')
        self.__create_coverage(['contributor_export'], ['ds_contributor_export'], 'coverage_export')
        coverages = self.__run_coverage_export('coverage_export')

        assert len(coverages) == 1
        assert 'last_active_job' in coverages[0]
        last_active_job = coverages[0]['last_active_job']
        assert last_active_job['coverage_id'] == 'coverage_export'
        assert last_active_job['contributor_id'] is None
        assert last_active_job['action_type'] == 'coverage_export'
        assert last_active_job['state'] == 'failed', print(last_active_job)
        assert last_active_job['step'] == 'merge', print(last_active_job)
        assert last_active_job['error_message'] == 'coverage coverage_export does not contains any Fusio export preprocess and fallback computation cannot find any gtfs data source'

    def test_status_after_success_coverage_export_with_one_contributor(self, init_http_download_server):
        self.__create_contributor(init_http_download_server.ip_addr, 'contributor_export')
        self.__create_coverage(['contributor_export'], ['ds_contributor_export'], 'coverage_export')
        self.contributor_export('contributor_export')
        coverages = self.__run_coverage_export('coverage_export')

        assert len(coverages) == 1
        assert 'last_active_job' in coverages[0]
        last_active_job = coverages[0]['last_active_job']
        assert last_active_job['coverage_id'] == 'coverage_export'
        assert last_active_job['contributor_id'] is None
        assert last_active_job['action_type'] == 'coverage_export'
        assert last_active_job['error_message'] == ''
        assert last_active_job['state'] == 'done'
        assert last_active_job['step'] == 'save_coverage_export'

    def test_status_after_success_automatic_update(self, init_http_download_server):
        self.__create_contributor(init_http_download_server.ip_addr, 'contributor_automatic_update_1')
        self.__create_contributor(init_http_download_server.ip_addr, 'contributor_automatic_update_2')
        self.__create_coverage(['contributor_automatic_update_1', 'contributor_automatic_update_2'],
                               ['ds_contributor_automatic_update_1', 'ds_contributor_automatic_update_2'], 'coverage_export')
        coverages = self.__run_automatic_update()

        assert len(coverages) == 1
        assert 'last_active_job' in coverages[0]
        last_active_job = coverages[0]['last_active_job']
        assert last_active_job['coverage_id'] == 'coverage_export'
        assert last_active_job['contributor_id'] is None
        assert last_active_job['action_type'] == 'automatic_update_coverage_export'
        assert last_active_job['error_message'] == ''
        assert last_active_job['state'] == 'done'
        assert last_active_job['step'] == 'save_coverage_export'

    def test_status_after_failed_automatic_update_with_invalid_contributor(self, init_http_download_server):
        self.__create_contributor(init_http_download_server.ip_addr, 'contributor_automatic_update_1')
        self.__create_contributor(init_http_download_server.ip_addr, 'contributor_automatic_update_2')
        self.__create_contributor(init_http_download_server.ip_addr, 'contributor_automatic_update_3', 'unknown_file')
        self.__create_coverage(['contributor_automatic_update_1',
                                'contributor_automatic_update_2',
                                'contributor_automatic_update_3'],
                               ['ds_contributor_automatic_update_1',
                                'ds_contributor_automatic_update_2',
                                'ds_contributor_automatic_update_3'], 'coverage_export')
        coverages = self.__run_automatic_update()

        assert len(coverages) == 1
        assert 'last_active_job' in coverages[0]
        last_active_job = coverages[0]['last_active_job']
        assert last_active_job['coverage_id'] is None
        assert last_active_job['contributor_id'] == 'contributor_automatic_update_3'
        assert last_active_job['action_type'] == 'automatic_update_contributor_export'
        assert last_active_job['error_message'] != ''
        assert last_active_job['state'] == 'failed'
        assert last_active_job['step'] == 'fetching data'

    def test_status_after_failed_automatic_update_on_publication(self, init_http_download_server, init_ftp_upload_server):
        self.__create_contributor(init_http_download_server.ip_addr, 'contributor_automatic_update')
        publication_platform = {
            "sequence": 0,
            "type": "ods",
            "protocol": "ftp",
            "url": init_ftp_upload_server.ip_addr,
            "options": {
                "authent": {
                    "username": "bad_username",
                    "password": "bad_password"
                }
            }
        }
        self.__create_coverage(['contributor_automatic_update'], ['ds_contributor_automatic_update'], 'coverage_export', publication_platform)
        coverages = self.__run_automatic_update()

        assert len(coverages) == 1
        assert 'last_active_job' in coverages[0]
        last_active_job = coverages[0]['last_active_job']
        assert last_active_job['coverage_id'] == 'coverage_export'
        assert last_active_job['contributor_id'] is None
        assert last_active_job['action_type'] == 'automatic_update_coverage_export'
        assert last_active_job['error_message'] != ''
        assert last_active_job['state'] == 'failed'
        assert last_active_job['step'].startswith('publish_data production ods on ')

    def test_status_successive_automatic_update(self, init_http_download_server):
        # Automatic update that fails in a contributor export
        self.__create_contributor(init_http_download_server.ip_addr, 'contributor_automatic_update_1')
        self.__create_contributor(init_http_download_server.ip_addr, 'contributor_automatic_update_2', 'unknown_file')
        self.__create_contributor(init_http_download_server.ip_addr, 'contributor_automatic_update_3')
        self.__create_coverage(['contributor_automatic_update_2',
                                'contributor_automatic_update_2',
                                'contributor_automatic_update_3'],
                               ['ds_contributor_automatic_update_2',
                                'ds_contributor_automatic_update_2',
                                'ds_contributor_automatic_update_3'], 'coverage_export')
        coverages = self.__run_automatic_update()

        assert len(coverages) == 1
        assert 'last_active_job' in coverages[0]
        last_active_job = coverages[0]['last_active_job']
        assert last_active_job['coverage_id'] is None
        assert last_active_job['contributor_id'] == 'contributor_automatic_update_2'
        assert last_active_job['action_type'] == 'automatic_update_contributor_export'
        assert last_active_job['error_message'] != ''
        assert last_active_job['state'] == 'failed'
        assert last_active_job['step'] == 'fetching data'

        # Let's make the automatic update a success
        data_source = {
            "input": {
                "type": "url",
                "url": self.format_url(init_http_download_server.ip_addr, 'gtfs_valid.zip')
            }
        }
        self.patch('/contributors/contributor_automatic_update_2/data_sources/ds_contributor_automatic_update_2', json.dumps(data_source))
        coverages = self.__run_automatic_update()
        assert len(coverages) == 1
        assert 'last_active_job' in coverages[0]
        last_active_job = coverages[0]['last_active_job']
        assert last_active_job['coverage_id'] == 'coverage_export'
        assert last_active_job['contributor_id'] is None
        assert last_active_job['action_type'] == 'automatic_update_coverage_export'
        assert last_active_job['error_message'] == ''
        assert last_active_job['state'] == 'done'
        assert last_active_job['step'] == 'save_coverage_export'

        # We make the automatic update failing in the contributor export again
        data_source = {
            "input": {
                "type": "url",
                "url": self.format_url(init_http_download_server.ip_addr, 'invalid_url')
            }
        }
        self.patch('/contributors/contributor_automatic_update_2/data_sources/ds_contributor_automatic_update_2',
                   json.dumps(data_source))
        coverages = self.__run_automatic_update()
        assert len(coverages) == 1
        assert 'last_active_job' in coverages[0]
        last_active_job = coverages[0]['last_active_job']
        assert last_active_job['coverage_id'] is None
        assert last_active_job['contributor_id'] == 'contributor_automatic_update_2'
        assert last_active_job['action_type'] == 'automatic_update_contributor_export'
        assert last_active_job['error_message'] != ''
        assert last_active_job['state'] == 'failed'
        assert last_active_job['step'] == 'fetching data'
