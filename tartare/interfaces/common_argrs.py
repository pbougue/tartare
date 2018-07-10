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

from datetime import date

from flask_restful import reqparse

from tartare.helper import date_from_string
from tartare.http_exceptions import InvalidArguments


class CommonArgs(object):
    def __init__(self) -> None:
        self.parsers = reqparse.RequestParser()
        self.parsers.add_argument('current_date', type=date_from_string, default=date.today(), location='args')

    def get_current_date(self) -> date:
        args = self.parsers.parse_args()
        return args.get('current_date')


class Pagination(object):
    def __init__(self) -> None:
        parsers = reqparse.RequestParser()
        parsers.add_argument('page', type=int, default=1, location='args')
        parsers.add_argument('per_page', type=int, default=20, location='args')
        args = parsers.parse_args()
        self.page = args.get('page')
        if self.page <= 0:
            raise InvalidArguments('page should be 1 or more')
        self.per_page = args.get('per_page')
        if self.per_page <= 0:
            raise InvalidArguments('per_page should be 1 or more')
