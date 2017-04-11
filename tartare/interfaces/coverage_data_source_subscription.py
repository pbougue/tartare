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

from flask_restful import request
import flask_restful
from pymongo.errors import PyMongoError
from tartare.core import models
import logging
from tartare.interfaces import schema


class CoverageDataSourceSubscription(flask_restful.Resource):
    def post(self, coverage_id):
        coverage = models.Coverage.get(coverage_id)
        if coverage is None:
            return {'message': 'bad coverage {}'.format(coverage_id)}, 400

        if 'id' not in request.json:
            return {'error': 'Missing data_source_id attribute in request body.'}, 400

        data_source_id = request.json['id']

        try:
            data_sources = models.DataSource.get(data_source_id=data_source_id)
        except ValueError:
            return {'error': 'unknown data_source_id {}.'.format(data_source_id, coverage_id)}, 400

        if coverage.has_data_source(data_sources[0]):
            return {'error': 'data_source_id {} already exists in coverage {}.'.format(data_source_id, coverage_id)}, 400

        coverage.add_data_source(data_sources[0])

        try:
            coverage = models.Coverage.update(coverage_id, {"data_sources": coverage.data_sources})
        except (PyMongoError, ValueError) as e:
            logging.getLogger(__name__).exception(
                'impossible to update coverage {} with data_source {}'.format(coverage_id, data_source_id)
            )
            return {'error': str(e)}, 400

        return {'coverages': schema.CoverageSchema().dump([coverage], many=True).data}, 200
