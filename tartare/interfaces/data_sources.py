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
from flask_restful import reqparse, abort, request
import flask_restful
from pymongo.errors import PyMongoError
from tartare import app
from tartare.core import models
import logging
from tartare.interfaces import schema
from marshmallow import ValidationError


class DataSource(flask_restful.Resource):
    def post(self, contributor_id):
        data_source_schema = schema.DataSourceSchema(strict=True)
        try:
            d = request.json
            data_source = data_source_schema.load(d).data
        except ValidationError as err:
            return {'error': err.messages}, 400

        try:
            data_source.save(contributor_id)
        except (PyMongoError, ValueError) as e:
            logging.getLogger(__name__).exception('impossible to add data_source {}'.format(data_source))
            return {'error': str(e)}, 400

        return {'data_sources': data_source_schema.dump(data_source).data}, 201


    def get(self, contributor_id, data_source_id=None):
        try:
            ds = models.DataSource.get(contributor_id, data_source_id)
            if ds is None:
                abort(404)
        except ValueError as e:
            logging.getLogger(__name__).exception('impossible to get data_source {} on contributor {}'
                                                  .format(data_source_id, contributor_id))
            return {'error': str(e)}, 400

        return {'data_sources': schema.DataSourceSchema(many=True).dump(ds).data}, 200


    def delete(self, contributor_id, data_source_id=None):
        try:
            nb_deleted = models.DataSource.delete(contributor_id, data_source_id)
            if nb_deleted == 0:
                abort(404)
        except ValueError as e:
            logging.getLogger(__name__).exception('impossible to delete data_source {} on contributor {}'
                                                  .format(data_source_id, contributor_id))
            return {'error': str(e)}, 400

        return {'data_sources': []}, 204


    def patch(self, contributor_id, data_source_id=None):
        ds = models.DataSource.get(contributor_id, data_source_id)
        if ds is None or len(ds) != 1:
            abort(404)

        schema_data_source = schema.DataSourceSchema(partial=True)
        errors = schema_data_source.validate(request.json, partial=True)
        if errors:
            return {'error': errors}, 400

        if 'id' in request.json and ds[0].id != request.json['id']:
            return {'error': 'The modification of the id is not possible'}, 400

        try:
            data_source = models.DataSource.update(contributor_id, data_source_id, request.json)
        except ValueError as e:
            logging.getLogger(__name__).exception('impossible to update data_source {} on contributor {}'
                                                  .format(data_source_id, contributor_id))
            return {'error': str(e)}, 400
        except PyMongoError as e:
            logging.getLogger(__name__).exception('impossible to update data_source with dataset {}'.format(request.json))
            return {'error': str(e)}, 500

        return {'data_sources': schema.DataSourceSchema(many=True).dump(data_source).data}, 200
