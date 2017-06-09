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

from flask_restful import abort, request
import flask_restful
from pymongo.errors import PyMongoError
from tartare.core import models
from tartare.interfaces import schema
from marshmallow import ValidationError
from tartare.exceptions import InvalidArguments, DuplicateEntry, InternalServerError, ObjectNotFound
from tartare.decorators import json_data_validate


class DataSource(flask_restful.Resource):
    @json_data_validate()
    def post(self, contributor_id):
        data_source_schema = schema.DataSourceSchema(strict=True)
        try:
            d = request.json
            data_source = data_source_schema.load(d).data
        except ValidationError as err:
            raise InvalidArguments(err.messages)

        try:
            data_source.save(contributor_id)
            return {'data_sources': schema.DataSourceSchema(many=True).dump([data_source]).data}, 201
        except PyMongoError:
            raise InternalServerError('Impossible to add data source.')
        except ValueError as e:
            raise DuplicateEntry(str(e))


    def get(self, contributor_id, data_source_id=None):
        try:
            ds = models.DataSource.get(contributor_id, data_source_id)
            if ds is None:
                raise ObjectNotFound("Data source '{}' not found.".format(data_source_id))
        except ValueError as e:
            raise InvalidArguments(str(e))

        return {'data_sources': schema.DataSourceSchema(many=True).dump(ds).data}, 200


    def delete(self, contributor_id, data_source_id=None):
        try:
            nb_deleted = models.DataSource.delete(contributor_id, data_source_id)
            if nb_deleted == 0:
                raise ObjectNotFound("Data source '{}' not found.".format(contributor_id))
        except ValueError as e:
            raise InvalidArguments(str(e))

        return {'data_sources': []}, 204

    @json_data_validate()
    def patch(self, contributor_id, data_source_id=None):
        ds = models.DataSource.get(contributor_id, data_source_id)
        if len(ds) != 1:
            abort(404)

        schema_data_source = schema.DataSourceSchema(partial=True)
        errors = schema_data_source.validate(request.json, partial=True)
        if errors:
            raise ObjectNotFound("Data source '{}' not found.".format(contributor_id))

        if 'id' in request.json and ds[0].id != request.json['id']:
            raise InvalidArguments('The modification of the id is not possible')

        try:
            data_sources = models.DataSource.update(contributor_id, data_source_id, request.json)
        except ValueError as e:
            raise InvalidArguments(str(e))
        except PyMongoError as e:
            raise InternalServerError('impossible to update contributor with dataset {}'.format(request.json))

        return {'data_sources': schema.DataSourceSchema(many=True).dump(data_sources).data}, 200
