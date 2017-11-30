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

import json

from tartare import app
from tartare.core.constants import DATA_FORMAT_DEFAULT, DATA_TYPE_DEFAULT


class TartareFixture(object):
    tester = app.test_client()

    def post(self, url, params=None, headers={'Content-Type': 'application/json'}):
        data = params if params else {}
        return self.tester.post(url,
                                headers=headers,
                                data=data)

    def get(self, url, **kwargs):
        return self.tester.get(url, **kwargs)

    def dict_to_json(self, dict):
        return json.dumps(dict)

    def to_json(self, response):
        return json.loads(response.data.decode('utf-8'))

    def patch(self, url, params=None, headers={'Content-Type': 'application/json'}):
        data = params if params else {}
        return self.tester.patch(url,
                                 headers=headers,
                                 data=data)

    def delete(self, url):
        return self.tester.delete(url)

    def is_json(self, data):
        try:
            self.to_json(data)
        except ValueError as e:
            return False
        return True

    def format_url(self, ip, filename, path='gtfs', method='http'):
        return "{method}://{ip}/{path}/{filename}".format(method=method, ip=ip, filename=filename, path=path)

    def assert_sucessful_call(self, raw, status_code_expected=200):
        debug = self.to_json(raw) if status_code_expected != 204 else 'no body'
        assert raw.status_code == status_code_expected, print(debug)
        return debug

    def assert_failed_call(self, raw, status_code_expected=400):
        assert raw.status_code == status_code_expected, print(self.to_json(raw))
        return self.to_json(raw)

    def get_job_details(self, id):
        raw = self.get('/jobs/{}'.format(id))
        self.assert_sucessful_call(raw, 200)
        return self.to_json(raw)['jobs'][0]

    def contributor_export(self, contributor_id, current_date=None):
        date_option = '?current_date=' + current_date if current_date else ''
        resp = self.post("/contributors/{}/actions/export{}".format(contributor_id, date_option))
        self.assert_sucessful_call(resp, 201)
        resp = self.get("/jobs/{}".format(self.to_json(resp)['job']['id']))
        job = self.to_json(resp)['jobs'][0]
        assert job['state'] == 'done', print(job)
        assert job['step'] == 'save_contributor_export', print(job)
        assert job['error_message'] == '', print(job)
        return resp

    def get_job_from_export_response(self, response):
        self.assert_sucessful_call(response, 201)
        resp = self.get("/jobs/{}".format(self.to_json(response)['job']['id']))
        return self.to_json(resp)['jobs'][0]

    def coverage_export(self, coverage_id):
        resp = self.post("/coverages/{}/actions/export".format(coverage_id))
        self.assert_sucessful_call(resp, 201)
        return resp

    def full_export(self, contributor_id, coverage_id, current_date=None):
        self.contributor_export(contributor_id, current_date)
        return self.coverage_export(coverage_id)

    def init_contributor(self, contributor_id, data_source_id, url, data_prefix='AAA', data_format=DATA_FORMAT_DEFAULT,
                         data_type=DATA_TYPE_DEFAULT):
        data_source = {
            "id": data_source_id,
            "name": data_source_id,
            "data_format": data_format,
            "input": {
                "type": "url",
                "url": url
            }
        }
        contributor = {
            "data_type": data_type,
            "id": contributor_id,
            "name": contributor_id + '_name',
            "data_prefix": data_prefix,
            "data_sources": [data_source]
        }
        raw = self.post('/contributors', self.dict_to_json(contributor))
        self.assert_sucessful_call(raw, 201)

    def add_data_source_to_contributor(self, contrib_id, data_source_id, url, data_format=DATA_FORMAT_DEFAULT):
        data_source = {
            "id": data_source_id,
            "name": data_source_id,
            "data_format": data_format,
            "input": {
                "type": "url",
                "url": url
            }
        }
        raw = self.post('/contributors/{}/data_sources'.format(contrib_id), self.dict_to_json(data_source))
        self.assert_sucessful_call(raw, 201)

    def update_data_source_url(self, contrib_id, ds_id, url):
        raw = self.patch('/contributors/{}/data_sources/{}'.format(contrib_id, ds_id),
                         json.dumps({'input': {
                             'url': url}}))
        return self.assert_sucessful_call(raw, 200)

    def run_automatic_update(self, current_date=None):
        date_option = '?current_date=' + current_date if current_date else ''
        raw = self.post('/actions/automatic_update{}'.format(date_option))
        self.assert_sucessful_call(raw, 204)
        raw = self.get('/jobs')
        self.assert_sucessful_call(raw, 200)
        return self.to_json(raw)['jobs']
