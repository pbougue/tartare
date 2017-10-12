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

from tests.integration.test_mechanism import TartareFixture
from tartare.processes.utils import  PREPROCESSES_POSSIBLE


class TestPreProcesses(TartareFixture):
    def assert_preprocesses_by_owner(self, preprocesses, owner):
        assert owner in preprocesses
        assert len(preprocesses[owner]) == len(PREPROCESSES_POSSIBLE[owner])
        assert (set(preprocesses[owner]) - set(PREPROCESSES_POSSIBLE[owner])) == set()

    def test_preprocesses_owner_contributor(self):
        owner = 'contributor'
        raw = self.get('/preprocesses?owner={}'.format(owner))
        assert raw.status_code == 200
        r = self.to_json(raw)
        assert 'preprocesses' in r
        preprocesses = r['preprocesses']
        assert 'coverage' not in preprocesses
        self.assert_preprocesses_by_owner(preprocesses, owner)

    def test_preprocesses_owner_coverage(self):
        owner = 'coverage'
        raw = self.get('/preprocesses?owner={}'.format(owner))
        assert raw.status_code == 200
        r = self.to_json(raw)
        assert 'preprocesses' in r
        preprocesses = r['preprocesses']
        assert 'contributor' not in preprocesses
        self.assert_preprocesses_by_owner(preprocesses, owner)

    def test_preprocesses_without_owner(self):
        raw = self.get('/preprocesses')
        assert raw.status_code == 200
        r = self.to_json(raw)
        assert 'preprocesses' in r
        preprocesses = r['preprocesses']
        for owner in PREPROCESSES_POSSIBLE.keys():
                    self.assert_preprocesses_by_owner(preprocesses, owner)

    def test_preprocesses_owner_invalid(self):
        raw = self.get('/preprocesses?owner=abcd')
        assert raw.status_code == 400
        r = self.to_json(raw)
        assert 'message' in r
        assert r['error'] == "The owner argument must be in list ['contributor', 'coverage'], you gave abcd"
