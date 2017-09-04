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

from tartare import app
import json


class TartareFixture(object):
    tester = app.test_client()

    def post(self, url, params=None, headers={'Content-Type': 'application/json'}):
        data = params if params else {}
        return self.tester.post(url,
                                headers=headers,
                                data=data)

    def get(self, url):
        return self.tester.get(url)

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

    def assert_sucessful_call(self, raw, status_code_expected=200):
        assert raw.status_code == status_code_expected, print(self.to_json(raw))
