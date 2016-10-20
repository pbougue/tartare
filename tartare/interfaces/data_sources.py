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
        contributor = models.Contributor.get(contributor_id)
        if contributor is None:
            return {'message': 'bad contributor {}'.format(contributor_id)}, 400

        data_source_schema = schema.DataSourceSchema(strict=True)
        try:
            d = request.json
            d['contributor_id'] = contributor_id
            data_source = data_source_schema.load(d).data
        except ValidationError as err:
            return {'error': err.messages}, 400

        try:
            data_source.save()
        except PyMongoError as e:
            logging.getLogger(__name__).exception('impossible to add data_source {}'.format(data_source))
            return {'error': str(e)}, 400

        return {'data_source': data_source_schema.dump(data_source).data}, 201

    def get(self, contributor_id, data_source_id=None):
        contributor = models.Contributor.get(contributor_id)
        if contributor is None:
            return {'message': 'bad contributor {}'.format(contributor_id)}, 400

        if data_source_id:
            ds = models.DataSoure.get(data_source_id)
            if ds is None:
                abort(404)

            result = schema.DataSoureSchema().dump(ds)
            return {'data_source': result.data}, 200

        data_sources = models.DataSource.all()

        return {'data_sources': schema.DataSourceSchema(many=True).dump(data_sources).data}, 200

    def delete(self, data_source_id):
        ds = models.DataSoure.delete(data_source_id)
        if ds == 0:
            abort(404)
        return {'data_source': None}, 204

    def patch(self, data_source_id):
        data_source = models.DataSource.get(data_source_id)
        if data_source is None:
            abort(404)

        schema_data_source = schema.DataSourceSchema(partial=True)
        errors = schema_data_source.validate(request.json, partial=True)
        if errors:
            return {'error': errors}, 400

        if 'id' in request.json and contributor.id != request.json['id']:
            return {'error': 'The modification of the id is not possible'}, 400

        try:
            data_source = models.DataSource.update(data_source_id, request.json)
        except PyMongoError as e:
            logging.getLogger(__name__).exception('impossible to update data_source with dataset {}'.format(args))
            return {'error': str(e)}, 500

        return {'data_source': schema.DataSourceSchema().dump(data_source).data}, 200
