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
import datetime
import os
import tempfile

import pytest
from freezegun import freeze_time

from tartare import app
from tartare.core.constants import INPUT_TYPE_MANUAL
from tartare.core.gridfs_handler import GridFsHandler
from tartare.core.models import DataSource
from tartare.helper import datetime_from_string
from tests.integration.test_mechanism import TartareFixture
from tests.utils import _get_file_fixture_full_path, assert_text_files_equals

fixtures_path = _get_file_fixture_full_path('gtfs/some_archive.zip')


class TestDataSourceFetchAction(TartareFixture):
    def test_fetch_with_unknown_contributor(self):
        raw = self.post('/contributors/unknown/data_sources/unknown/actions/fetch')
        assert raw.status_code == 404
        r = self.json_to_dict(raw)
        assert r["error"] == "contributor 'unknown' not found"

    def test_fetch_with_unknown_data_source(self, contributor):
        raw = self.post('/contributors/id_test/data_sources/unknown/actions/fetch')
        assert raw.status_code == 404
        r = self.json_to_dict(raw)
        assert r["error"] == "data source unknown not found for contributor id_test"

    def test_fetch_ok(self, init_http_download_server, contributor):
        ip = init_http_download_server.ip_addr
        url = self.format_url(ip, 'sample_1.zip')
        contributor['data_sources'].append({
            "name": "bobette",
            "data_format": "gtfs",
            "input": {
                "type": "auto",
                "url": url,
                "frequency": {
                    "type": "daily",
                    "hour_of_day": 20
                }
            }
        })
        raw = self.put('/contributors/id_test', params=self.dict_to_json(contributor))

        json_response = self.json_to_dict(raw)
        data_source_id = json_response['contributors'][0]['data_sources'][0]['id']

        raw = self.post('/contributors/{}/data_sources/{}/actions/fetch'.format(contributor['id'], data_source_id))

        self.assert_sucessful_call(raw, 204)

        data_source = \
            self.json_to_dict(self.get('contributors/{}/data_sources/{}'.format(contributor['id'], data_source_id)))[
                'data_sources'][0]
        data_set = data_source['data_sets'][0]
        # Test that source file and saved file are the same
        with app.app_context():
            gridout = GridFsHandler().get_file_from_gridfs(data_set['gridfs_id'])
            expected_path = _get_file_fixture_full_path('gtfs/sample_1.zip')

            with tempfile.TemporaryDirectory() as path:
                gridout_path = os.path.join(path, gridout.filename)
                with open(gridout_path, 'wb+') as f:
                    f.write(gridout.read())
                    assert_text_files_equals(gridout_path, expected_path)
            jobs = self.get_all_jobs()
            assert len(jobs) == 0

    def test_fetch_invalid_type(self, init_http_download_server, contributor):
        ip = init_http_download_server.ip_addr
        url = "http://{ip}/{filename}".format(ip=ip, filename='unknown.zip')
        contributor['data_sources'].append({
            "name": "bobette",
            "data_format": "gtfs",
            "input": {"type": "manual", "url": url}
        })
        raw = self.put('/contributors/id_test', params=self.dict_to_json(contributor))

        json_response = self.json_to_dict(raw)
        data_source_id = json_response['contributors'][0]['data_sources'][0]['id']

        response = self.post('/contributors/{}/data_sources/{}/actions/fetch'.format(contributor['id'], data_source_id))
        json_response = self.json_to_dict(response)

        assert response.status_code == 400, print(self.json_to_dict(response))
        assert json_response['error'] == 'data source type should be auto and should have an url'

    def test_fetch_invalid_url(self, init_http_download_server, contributor):
        url = self.format_url(init_http_download_server.ip_addr, 'unknown.zip', path='')
        contributor['data_sources'].append({
            "name": "bobette",
            "data_format": "gtfs",
            "input": {
                "type": "auto",
                "url": url,
                "frequency": {
                    "type": "daily",
                    "hour_of_day": 20
                }
            }
        })
        raw = self.put('/contributors/id_test', params=self.dict_to_json(contributor))

        json_response = self.json_to_dict(raw)
        data_source_id = json_response['contributors'][0]['data_sources'][0]['id']

        response = self.post('/contributors/{}/data_sources/{}/actions/fetch'.format(contributor['id'], data_source_id))
        json_response = self.json_to_dict(response)

        assert response.status_code == 500, print(self.json_to_dict(response))
        assert json_response['error'].startswith('fetching {} failed:'.format(url))
        jobs = self.get_all_jobs()
        assert len(jobs) == 0

    def test_fetch_authent_in_http_url_ok(self, init_http_download_authent_server):
        props = init_http_download_authent_server.properties
        url = "http://{user}:{password}@{ip}/{alias}gtfs/{filename}".format(
            user=props['USERNAME'],
            password=props['PASSWORD'],
            alias=props['ROOT'],
            ip=init_http_download_authent_server.ip_addr,
            filename='some_archive.zip'
        )
        self.init_contributor('cid', 'dsid', url)
        self.fetch_data_source('cid', 'dsid')
        data_source = self.get_contributor('cid')['data_sources'][0]
        assert len(data_source['data_sets']) == 1

    def test_fetch_authent_in_options_ok(self, init_http_download_authent_server):
        props = init_http_download_authent_server.properties
        url = "http://{ip}/{alias}gtfs/{filename}".format(
            alias=props['ROOT'],
            ip=init_http_download_authent_server.ip_addr,
            filename='some_archive.zip'
        )
        self.init_contributor('cid', 'dsid', url, options={
            'authent': {'username': props['USERNAME'], 'password': props['PASSWORD']}
        })
        self.fetch_data_source('cid', 'dsid')
        data_source = self.get_contributor('cid')['data_sources'][0]
        assert len(data_source['data_sets']) == 1

    def test_fetch_ftp_authent_in_options_ok(self, init_ftp_download_server_authent):
        url = self.format_url(init_ftp_download_server_authent.ip_addr, 'some_archive.zip', method='ftp')
        self.init_contributor('cid', 'dsid', url, options={
            'authent': {'username': init_ftp_download_server_authent.user,
                        'password': init_ftp_download_server_authent.password}
        })
        self.fetch_data_source('cid', 'dsid')
        data_source = self.get_contributor('cid')['data_sources'][0]
        assert len(data_source['data_sets']) == 1

    def test_fetch_ftp_authent_in_options_unauthorized(self, init_ftp_download_server_authent):
        url = self.format_url(init_ftp_download_server_authent.ip_addr, 'some_archive.zip', method='ftp')
        self.init_contributor('cid', 'dsid', url, options={
            'authent': {'username': 'wrong_user',
                        'password': 'wrong_password'}
        })
        raw = self.fetch_data_source('cid', 'dsid', check_success=False)
        details = self.assert_failed_call(raw, 500)
        assert details == {
            'error': 'fetching {} failed: error during download of file: 530 Login authentication failed'.format(url),
            'message': 'Internal Server Error'}

    def test_fetch_ftp_authent_in_options_not_found(self, init_ftp_download_server_authent):
        url = self.format_url(init_ftp_download_server_authent.ip_addr, 'some_archive_unknown.zip', method='ftp')
        self.init_contributor('cid', 'dsid', url, options={
            'authent': {'username': init_ftp_download_server_authent.user,
                        'password': init_ftp_download_server_authent.password}
        })
        raw = self.fetch_data_source('cid', 'dsid', check_success=False)
        details = self.assert_failed_call(raw, 500)
        assert details == {
            'error': "fetching {} failed: error during download of file: 550 Can't open /gtfs/some_archive_unknown.zip: No such file or directory".format(
                url),
            'message': 'Internal Server Error'}

    def test_fetch_authent_in_http_url_unauthorized(self, init_http_download_authent_server):
        props = init_http_download_authent_server.properties
        contrib_cpt = 0
        for user, password in [('unknown', props['PASSWORD']), (props['USERNAME'], 'wrong_one'),
                               ('unknown', 'wrong_one')]:
            url = "http://{user}:{password}@{ip}/{alias}gtfss/{filename}".format(
                user=user,
                password=password,
                alias=props['ROOT'],
                ip=init_http_download_authent_server.ip_addr,
                filename='some_archive.zip'
            )
            cid = 'cid_{}'.format(contrib_cpt)
            dsid = 'dsid_{}'.format(contrib_cpt)
            self.init_contributor('cid_{}'.format(contrib_cpt), 'dsid_{}'.format(contrib_cpt), url)
            contrib_cpt += 1
            raw = self.fetch_data_source(cid, dsid, check_success=False)
            response_body = self.assert_failed_call(raw, 500)
            assert response_body == {
                'error': 'fetching {} failed: error during download of file: HTTP Error 401: Unauthorized'.format(url),
                'message': 'Internal Server Error'
            }

    def test_fetch_authent_in_http_url_not_found(self, init_http_download_authent_server):
        props = init_http_download_authent_server.properties
        url = "http://{user}:{password}@{ip}/{alias}gtfs/unknown.zip".format(
            user=props['USERNAME'],
            password=props['PASSWORD'],
            alias=props['ROOT'],
            ip=init_http_download_authent_server.ip_addr
        )
        cid = 'cid'
        dsid = 'dsid'
        self.init_contributor('{}'.format(cid), '{}'.format(dsid), url)
        raw = self.fetch_data_source(cid, dsid, check_success=False)
        response_body = self.assert_failed_call(raw, 500)
        assert response_body == {
            'error': 'fetching {} failed: error during download of file: HTTP Error 404: Not Found'.format(url),
            'message': 'Internal Server Error'
        }


class TestDataSourceShouldFetch(TartareFixture):
    start_time = datetime_from_string('1986-01-15 10:00:00 UTC')

    def __fetch(self, ):
        self.fetch_data_source('cid', 'dsid')

    def __init_data_source(self, ip, type='auto', frequency=None):
        contributor = self.init_contributor('cid', 'dsid', self.format_url(ip, 'some_archive.zip'))
        contributor['data_sources'][0]['input']['type'] = type
        if frequency:
            contributor['data_sources'][0]['input']['frequency'] = frequency
        self.put('/contributors/cid', self.dict_to_json(contributor))

    def __assert_should_fetch(self, should_fetch):
        with app.app_context():
            data_source = DataSource.get_one(data_source_id='dsid')
            assert data_source.should_fetch() == should_fetch

    def test_manual_should_not_fetch(self, init_http_download_server):
        self.__init_data_source(init_http_download_server.ip_addr, type=INPUT_TYPE_MANUAL)
        self.__assert_should_fetch(False)

    def test_computed_should_not_fetch(self, init_http_download_server):
        self.init_contributor('cid', 'input_dsid',
                              self.format_url(init_http_download_server.ip_addr, 'some_archive.zip'),
                              export_id='dsid')
        self.__assert_should_fetch(False)

    def test_never_fetch_should_fetch(self, init_http_download_server):
        self.__init_data_source(init_http_download_server.ip_addr, frequency={
            'type': 'continuously',
            'minutes': 5
        })
        self.__assert_should_fetch(True)

    @pytest.mark.parametrize("minutes", [
        1, 3, 27, 123
    ])
    def test_continuous_fetch(self, init_http_download_server, minutes):
        self.__init_data_source(init_http_download_server.ip_addr, frequency={
            'type': 'continuously',
            'minutes': minutes
        })
        with freeze_time(self.start_time) as frozen_datetime:
            # never fetched, we should fetch
            self.__assert_should_fetch(True)
            self.__fetch()
            # after fetch no need to fetch
            self.__assert_should_fetch(False)
            # less than n minutes
            frozen_datetime.tick(delta=datetime.timedelta(seconds=10))
            self.__assert_should_fetch(False)
            frozen_datetime.tick(delta=datetime.timedelta(minutes=minutes - 1))
            # almost n minutes
            self.__assert_should_fetch(False)
            frozen_datetime.tick(delta=datetime.timedelta(minutes=2))
            # n +1 minutes
            self.__assert_should_fetch(True)
            # should fetch until fetch is done
            self.__assert_should_fetch(True)
            self.__fetch()
            self.__assert_should_fetch(False)
            # n minutes since last fetch
            frozen_datetime.tick(delta=datetime.timedelta(minutes=minutes))
            self.__assert_should_fetch(True)
            self.__fetch()
            self.__assert_should_fetch(False)
            # we skip schedule, it's been 2xn minutes
            frozen_datetime.tick(delta=datetime.timedelta(minutes=2 * minutes))
            self.__assert_should_fetch(True)
            self.__fetch()
            self.__assert_should_fetch(False)
            # less than a minute
            frozen_datetime.tick(delta=datetime.timedelta(seconds=30))
            self.__assert_should_fetch(False)

    def test_daily_fetch(self, init_http_download_server):
        self.__init_data_source(init_http_download_server.ip_addr, frequency={
            'type': 'daily',
            'hour_of_day': 13
        })
        with freeze_time(self.start_time) as frozen_datetime:
            # never fetched, we wait till it's time
            self.__assert_should_fetch(False)
            # wait hour_of_day
            frozen_datetime.move_to(datetime_from_string('1986-01-15 12:59:00 UTC'))
            self.__assert_should_fetch(False)
            frozen_datetime.move_to(datetime_from_string('1986-01-15 13:00:00 UTC'))
            self.__assert_should_fetch(True)
            # if no fetch, still should fetch
            self.__assert_should_fetch(True)
            self.__fetch()
            # after fetch should not fetch
            self.__assert_should_fetch(False)
            frozen_datetime.move_to(datetime_from_string('1986-01-15 13:15:00 UTC'))
            self.__assert_should_fetch(False)
            frozen_datetime.move_to(datetime_from_string('1986-01-16 11:15:00 UTC'))
            self.__assert_should_fetch(False)
            # manual fetch
            self.__fetch()
            self.__assert_should_fetch(False)
            frozen_datetime.move_to(datetime_from_string('1986-01-16 12:55:00 UTC'))
            self.__assert_should_fetch(False)
            # less than one day since manual fetch but it's time
            frozen_datetime.move_to(datetime_from_string('1986-01-16 13:55:00 UTC'))
            self.__assert_should_fetch(True)
            # time passed (some crash), we wait until it's been one day
            frozen_datetime.move_to(datetime_from_string('1986-01-16 17:55:00 UTC'))
            self.__assert_should_fetch(False)
            # more than one day since manual fetch
            frozen_datetime.move_to(datetime_from_string('1986-01-17 12:05:00 UTC'))
            self.__assert_should_fetch(True)
            self.__fetch()
            self.__assert_should_fetch(False)

    def test_weekly_fetch(self, init_http_download_server):
        self.__init_data_source(init_http_download_server.ip_addr, frequency={
            'type': 'weekly',
            'day_of_week': 2,  # tuesday
            'hour_of_day': 10
        })
        # start time is wednesday
        with freeze_time(self.start_time) as frozen_datetime:
            # never fetched, we wait till it's time
            self.__assert_should_fetch(False)
            # wait day_of_week
            frozen_datetime.move_to(datetime_from_string('1986-01-18 11:59:00 UTC'))
            self.__assert_should_fetch(False)
            frozen_datetime.move_to(datetime_from_string('1986-01-20 16:00:00 UTC'))
            self.__assert_should_fetch(False)
            frozen_datetime.move_to(datetime_from_string('1986-01-21 09:35:00 UTC'))
            self.__assert_should_fetch(False)
            frozen_datetime.move_to(datetime_from_string('1986-01-21 10:00:00 UTC'))
            self.__assert_should_fetch(True)
            # if no fetch, still should fetch
            self.__assert_should_fetch(True)
            self.__fetch()
            # after fetch should not fetch
            self.__assert_should_fetch(False)
            frozen_datetime.move_to(datetime_from_string('1986-01-21 13:15:00 UTC'))
            self.__assert_should_fetch(False)
            frozen_datetime.move_to(datetime_from_string('1986-01-24 11:15:00 UTC'))
            self.__assert_should_fetch(False)
            # manual fetch
            self.__fetch()
            self.__assert_should_fetch(False)
            frozen_datetime.move_to(datetime_from_string('1986-01-27 12:55:00 UTC'))
            self.__assert_should_fetch(False)
            # less than one week since manual fetch but it's time
            frozen_datetime.move_to(datetime_from_string('1986-01-28 10:55:00 UTC'))
            self.__assert_should_fetch(True)
            # time passed (some crash), we wait until it's been one day
            frozen_datetime.move_to(datetime_from_string('1986-01-28 17:55:00 UTC'))
            self.__assert_should_fetch(False)
            # more than one week since manual fetch
            frozen_datetime.move_to(datetime_from_string('1986-01-31 12:05:00 UTC'))
            self.__assert_should_fetch(True)
            self.__fetch()
            self.__assert_should_fetch(False)

    def test_monthly_fetch(self, init_http_download_server):
        self.__init_data_source(init_http_download_server.ip_addr, frequency={
            'type': 'monthly',
            'day_of_month': 12,  # tuesday
            'hour_of_day': 16
        })
        # start time is wednesday
        with freeze_time(self.start_time) as frozen_datetime:
            # never fetched, we wait till it's time
            self.__assert_should_fetch(False)
            # wait day_of_month
            frozen_datetime.move_to(datetime_from_string('1986-01-18 11:59:00 UTC'))
            self.__assert_should_fetch(False)
            frozen_datetime.move_to(datetime_from_string('1986-01-30 16:00:00 UTC'))
            self.__assert_should_fetch(False)
            frozen_datetime.move_to(datetime_from_string('1986-02-12 15:35:00 UTC'))
            self.__assert_should_fetch(False)
            frozen_datetime.move_to(datetime_from_string('1986-02-12 16:00:00 UTC'))
            self.__assert_should_fetch(True)
            # if no fetch, still should fetch
            self.__assert_should_fetch(True)
            self.__fetch()
            # after fetch should not fetch
            self.__assert_should_fetch(False)
            frozen_datetime.move_to(datetime_from_string('1986-02-20 13:15:00 UTC'))
            self.__assert_should_fetch(False)
            frozen_datetime.move_to(datetime_from_string('1986-02-28 11:15:00 UTC'))
            self.__assert_should_fetch(False)
            # manual fetch
            self.__fetch()
            self.__assert_should_fetch(False)
            frozen_datetime.move_to(datetime_from_string('1986-03-11 12:55:00 UTC'))
            self.__assert_should_fetch(False)
            # less than one month since manual fetch but it's time
            frozen_datetime.move_to(datetime_from_string('1986-03-12 16:55:00 UTC'))
            self.__assert_should_fetch(True)
            # time passed (some crash), we wait until it's been one month
            frozen_datetime.move_to(datetime_from_string('1986-03-12 17:55:00 UTC'))
            self.__assert_should_fetch(False)
            # more than one month since manual fetch
            frozen_datetime.move_to(datetime_from_string('1986-04-01 12:05:00 UTC'))
            self.__assert_should_fetch(True)
            self.__fetch()
            self.__assert_should_fetch(False)
