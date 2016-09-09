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
from flask_restful import reqparse, abort
import flask_restful
from pymongo.errors import PyMongoError
from tartare import mongo
from tartare.core import models
import logging
from tartare.interfaces import schema


class Coverage(flask_restful.Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('id', required=True, help='id is required', location='json')
        parser.add_argument('name', required=True, help='name is required', location='json')

        args = parser.parse_args()

        coverage = models.Coverage(_id=args['id'], name=args['name'])
        try:
            coverage.save()
        except PyMongoError as e:
            logging.getLogger(__name__).exception('impossible to add coverage {}'.format(coverage))
            return {'error': str(e)}, 400

        return {'coverage': schema.CoverageSchema().dump(coverage)}, 201

    def get(self, coverage_id=None):
        if coverage_id:
            c = models.Coverage.get(coverage_id)
            if c is None:
                abort(404)
            return {'coverage': schema.CoverageSchema().dump(c)}, 200

        return {'coverages': schema.CoverageSchema(many=True).dump(list(models.Coverage.find()))}, 200
