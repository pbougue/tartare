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
from tartare.exceptions import InvalidArguments, InternalServerError, ObjectNotFound
from tartare.helper import validate_preprocesses_or_raise


class PreProcess(flask_restful.Resource):
    def post(self, contributor_id):
        preprocess_schema = schema.PreProcessSchema(strict=True)
        try:
            d = request.json
            validate_preprocesses_or_raise([d])
            preprocess = preprocess_schema.load(d).data
        except ValidationError as err:
            raise InvalidArguments(err.messages)

        try:
            preprocess.save(contributor_id)
        except (PyMongoError, ValueError) as e:
            raise InternalServerError('Impossible to add data source.')

        return {'preprocesses': schema.PreProcessSchema(many=True).dump([preprocess]).data}, 201

    def get(self, contributor_id, preprocess_id=None):
        try:
            ps = models.PreProcess.get(contributor_id, preprocess_id)
            if not ps and preprocess_id:
                raise ObjectNotFound("Preprocess '{}' not found.".format(preprocess_id))
        except ValueError as e:
            raise InvalidArguments(str(e))

        return {'preprocesses': schema.PreProcessSchema(many=True).dump(ps).data}, 200

    def patch(self, contributor_id, preprocess_id):
        ds = models.PreProcess.get(contributor_id, preprocess_id)
        if len(ds) != 1:
            abort(404)

        schema_preprocess = schema.PreProcessSchema(partial=True)
        errors = schema_preprocess.validate(request.json, partial=True)
        if errors:
            raise ObjectNotFound("Preprocess '{}' not found.".format(contributor_id))

        try:
            p = request.json
            validate_preprocesses_or_raise([p])
            preprocesses = models.PreProcess.update(contributor_id, preprocess_id, p)
        except ValueError as e:
            raise InvalidArguments(str(e))
        except PyMongoError as e:
            raise InternalServerError('impossible to update contributor with preprocess {}'.format(p))

        return {'preprocesses': schema.PreProcessSchema(many=True).dump(preprocesses).data}, 200

    def delete(self, contributor_id, preprocess_id):
        try:
            nb_deleted = models.PreProcess.delete(contributor_id, preprocess_id)
            if nb_deleted == 0:
                raise ObjectNotFound("Preprocess '{}' not found.".format(contributor_id))
        except ValueError as e:
            raise InvalidArguments(str(e))

        return {'preprocesses': []}, 204
