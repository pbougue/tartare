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

from tartare.core import calendar_handler


def test_merge_calendar_join_with_line_code():
    calendar_lines = [
        {
            'grid_calendar_id': 1,
            'network_id': 'network:A',
            'line_code': 1,
        },
        {
            'grid_calendar_id': 2,
            'network_id': 'network:A',
            'line_code': 2,
        }
    ]

    lines = [
        {
            'line_id': 'l1',
            'network_id': 'network:A',
            'line_code': 1,
        },
        {
            'line_id': 'l2',
            'network_id': 'network:A',
            'line_code': 2,
        },
        {
            'line_id': 'l3',
            'network_id': 'network:B',
            'line_code': 3,
        }
    ]

    grid_rel_calendar_line = calendar_handler._join_calendar_lines(calendar_lines, lines)

    assert grid_rel_calendar_line == [
        {
            'grid_calendar_id': 1,
            'line_id': 'l1',
        },
        {
            'grid_calendar_id': 2,
            'line_id': 'l2',
        }
    ]


def test_merge_calendar_take_all_lines_if_no_line_code():
    calendar_lines = [
        {
            'grid_calendar_id': 1,
            'network_id': 'network:A',
            'line_code': 1,
        },
        {
            'grid_calendar_id': 2,
            'network_id': 'network:A',
            'line_code': '',
        }
    ]

    lines = [
        {
            'line_id': 'l1',
            'network_id': 'network:A',
            'line_code': 1,
        },
        {
            'line_id': 'l2',
            'network_id': 'network:A',
            'line_code': 2,
        },
        {
            'line_id': 'l3',
            'network_id': 'network:A',
            'line_code': 3,
        },
        {
            'line_id': 'l4',
            'network_id': 'network:B',
            'line_code': 4,
        }
    ]

    grid_rel_calendar_line = calendar_handler._join_calendar_lines(calendar_lines, lines)

    assert grid_rel_calendar_line == [
        {
            'grid_calendar_id': 1,
            'line_id': 'l1',
        },
        {
            'grid_calendar_id': 2,
            'line_id': 'l1',
        },
        {
            'grid_calendar_id': 2,
            'line_id': 'l2',
        },
        {
            'grid_calendar_id': 2,
            'line_id': 'l3',
        }
    ]
