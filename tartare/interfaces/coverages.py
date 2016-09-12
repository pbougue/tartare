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
import os
from flask_restful import reqparse, abort
import flask_restful
from pymongo.errors import PyMongoError
from tartare import app
from tartare.core import models
import logging
from tartare.interfaces import schema


def _default_dir(var, coverage_id):
    return os.path.join(app.config.get(var), coverage_id)


class Coverage(flask_restful.Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('id', location='json')
        parser.add_argument('name', location='json')
        parser.add_argument('input_dir', location='json')
        parser.add_argument('output_dir', location='json')
        parser.add_argument('current_data_dir', location='json')

        args = parser.parse_args()
        coverageSchema = schema.CoverageSchema(strict=True)

        try:
            coverage = coverageSchema.load(args).data
            coverage.save()
        except ValidationError as err:
            return {'error': err.messages}, 400
        except PyMongoError as e:
            logging.getLogger(__name__).exception('impossible to add coverage {}'.format(coverage))
            return {'error': str(e)}, 400

        return {'coverage': coverageSchema.dump(coverage).data}, 201

    def get(self, coverage_id=None):
        if coverage_id:
            c = models.Coverage.get(coverage_id)
            if c is None:
                abort(404)

            result = schema.CoverageSchema().dump(c)
            return {'coverage': result.data}, 200

        coverages = models.Coverage.all()

        return {'coverages': schema.CoverageSchema(many=True).dump(coverages).data}, 200

    def delete(self, coverage_id):
        c = models.Coverage.delete(coverage_id)
        if c == 0:
            abort(404)
        return {'coverage': None}, 204

    def patch(self, coverage_id):
        parser = reqparse.RequestParser()
        parser.add_argument('name', location='json')

        args = parser.parse_args()

        try:
            coverage = models.Coverage.update(coverage_id, args)
        except PyMongoError as e:
            logging.getLogger(__name__).exception('impossible to update coverage with dataset{}'.format(args))
            return {'error': str(e)}, 400

        if coverage is None:
            abort(404)

        return {'coverage': schema.CoverageSchema().dump(coverage).data}, 200
