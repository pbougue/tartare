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
from tartare.interfaces import schema
from tartare.exceptions import InvalidArguments, DuplicateEntry, InternalServerError, ResourceNotFound


class CoverageDataSourceSubscription(flask_restful.Resource):
    def post(self, coverage_id):
        coverage = models.Coverage.get(coverage_id)
        if coverage is None:
            raise ResourceNotFound("Coverage {} not found.".format(coverage_id))

        if 'id' not in request.json:
            raise InvalidArguments('Missing data_source_id attribute in request body.')

        data_source_id = request.json['id']

        data_sources = models.DataSource.get(data_source_id=data_source_id)
        if data_sources is None:
            raise ResourceNotFound("Data source {} not found.".format(data_source_id))

        if coverage.has_data_source(data_sources[0]):
            raise DuplicateEntry('Data source id {} already exists in coverage {}.'
                                 .format(data_source_id, coverage_id))

        coverage.add_data_source(data_sources[0])

        try:
            coverage = models.Coverage.update(coverage_id, {"data_sources": coverage.data_sources})
        except (PyMongoError, ValueError) as e:
            raise InternalServerError('Impossible to update coverage {} with data_source {}.'
                                      .format(coverage_id, data_source_id))

        return {'coverages': schema.CoverageSchema().dump([coverage], many=True).data}, 200
