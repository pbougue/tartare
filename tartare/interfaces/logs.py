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
from datetime import datetime, timedelta
import json

from bson import json_util
from flask import Response
from flask_restful import Resource, reqparse
from tartare import mongo


def datetime_type(value: str) -> datetime:
    _datetime = datetime.strptime(value, '%Y-%m-%d')

    return reset_time(_datetime)


def reset_time(_datetime: datetime) -> datetime:
    return _datetime.replace(minute=0, hour=0, second=0, microsecond=0)


class RequestLogs(Resource):
    def __init__(self) -> None:

        self.parsers = reqparse.RequestParser()
        self.parsers.add_argument('start_date', type=datetime_type, default=None, location='args')

        default_date = datetime.utcnow()
        default_date = reset_time(default_date)
        self.parsers.add_argument('end_date', type=datetime_type, default=default_date, location='args')

    def get(self) -> Response:
        args = self.parsers.parse_args()

        start_date = args['start_date']
        end_date = args['end_date']

        if not start_date:
            start_date = end_date

        end_date += timedelta(days=1)

        results = mongo.db['logs'].aggregate([
            {
                "$match": {
                    "date": {
                        "$gte": start_date,
                        "$lt": end_date
                    }
                },
            },
            {
                "$project": {
                    "_id": 0,
                    "date": {
                        "$dateToString": {
                            "format": "%Y-%m-%dT%H:%M:%S.%LZ",
                            "date": "$date",
                        }
                    },
                    "request": 1,
                    "response": 1,
                }
            }
        ])

        return Response(
            json.dumps(list(results), default=json_util.default),
            mimetype='application/json'
        )
