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

from flask import Response
from flask_restful import Resource, reqparse
from tartare.processes.utils import PREPROCESSES_POSSIBLE
from tartare.http_exceptions import InvalidArguments


class PreProcesses(Resource):

    def __init__(self) -> None:
        self.parsers = reqparse.RequestParser()
        self.parsers.add_argument('owner', type=str, default='', location='args')

    def get(self) -> Response:
        args = self.parsers.parse_args()
        owner = args.get('owner')

        if not owner:
            return {'preprocesses': PREPROCESSES_POSSIBLE}, 200
        if owner not in PREPROCESSES_POSSIBLE:
            raise InvalidArguments("The owner argument must be in list {}, you gave {}".format(
                list(PREPROCESSES_POSSIBLE.keys()), owner))
        return {'preprocesses': {owner: PREPROCESSES_POSSIBLE[owner]}}, 200
