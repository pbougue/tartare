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
from tests.utils import to_json, post


def test_get_coverage_export(app, coverage_export_obj):
    post(app, '/coverages', '{"id": "coverage1", "name":"name_test"}')
    post(app, '/coverages', '{"id": "coverage2", "name":"name_test"}')

    # Exports for coverage1, one export
    exports = app.get('/coverages/coverage1/exports')
    assert exports.status_code == 200
    r = to_json(exports)
    assert len(r["exports"]) == 1
    assert r["exports"][0]["gridfs_id"] == "1234"
    assert r["exports"][0]["coverage_id"] == "coverage1"
    assert r["exports"][0]["contributors"] == ["contributor1", "contributor2"]

    # Exports for coverage2, 0 export
    exports = app.get('/coverages/coverage2/exports')
    assert exports.status_code == 200
    r = to_json(exports)
    assert len(r["exports"]) == 0

    # Exports for unknown coverage, 0 export
    exports = app.get('/coverages/bob/exports')
    assert exports.status_code == 404
    r = to_json(exports)
    assert r['message'] == 'Object Not Found'
    assert r['error'] == 'Coverage not found: bob'
