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

import flask_restful
from pymongo.errors import PyMongoError, DuplicateKeyError
from tartare.core import models
from flask import request
from tartare.interfaces import schema
from marshmallow import ValidationError
from tartare.http_exceptions import InvalidArguments, DuplicateEntry, InternalServerError, ObjectNotFound
from tartare.helper import validate_preprocesses_or_raise
import uuid
import logging


class Contributor(flask_restful.Resource):
    @staticmethod
    def upgrade_dict(source, request_data, key):
        map_model = {
            "data_sources": schema.DataSourceSchema,
            "preprocesses": schema.PreProcessSchema
        }
        existing_id = [d.id for d in source]
        logging.getLogger(__name__).debug("PATCH : list of existing {} ids {}".format(key, str(existing_id)))
        # constructing PATCH data
        patched_data = None
        if key in request_data:
            patched_data = map_model.get(key)(many=True).dump(source).data
            for item in request_data[key]:
                if item['id'] in existing_id:
                    item2update = next((p for p in patched_data if p['id'] == item['id']), None)
                    if item2update:
                        item2update.update(item)
                else:
                    patched_data.append(item)
        if patched_data:
            request_data[key] = patched_data

    @staticmethod
    def set_ids(collections):
        for c in collections:
            c.setdefault('id', str(uuid.uuid4()))

    def post(self):
        post_data = request.json
        if 'id' not in post_data:
            raise InvalidArguments('contributor id has to be specified')
        # first a check on the data_sources id and providing a uuid if not provided
        self.set_ids(post_data.get('data_sources', []))

        preprocesses = post_data.get('preprocesses', [])

        validate_preprocesses_or_raise(preprocesses)

        self.set_ids(preprocesses)

        contributor_schema = schema.ContributorSchema(strict=True)

        try:
            contributor = contributor_schema.load(post_data).data
        except ValidationError as err:
            raise InvalidArguments(err.messages)

        try:
            contributor.save()
        except DuplicateKeyError:
            raise DuplicateEntry("Impossible to add contributor, id {} or data_prefix {} already used."
                                 .format(request.json['id'], request.json['data_prefix']))
        except PyMongoError:
            raise InternalServerError('Impossible to add contributor {}'.format(contributor))

        return {'contributors': [contributor_schema.dump(models.Contributor.get(post_data['id'])).data]}, 201

    def get(self, contributor_id=None):
        if contributor_id:
            c = models.Contributor.get(contributor_id)
            if c is None:
                raise ObjectNotFound("Contributor '{}' not found.".format(contributor_id))
            result = schema.ContributorSchema().dump(c)
            return {'contributors': [result.data]}, 200
        contributors = models.Contributor.all()
        return {'contributors': schema.ContributorSchema(many=True).dump(contributors).data}, 200

    def delete(self, contributor_id):
        c = models.Contributor.delete(contributor_id)
        if c == 0:
            raise ObjectNotFound("Contributor '{}' not found.".format(contributor_id))
        return "", 204

    def patch(self, contributor_id):
        # "data_prefix" field is not modifiable, impacts of the modification
        # need to be checked. The previous value needs to be checked for an error
        contributor = models.Contributor.get(contributor_id)
        if contributor is None:
            raise ObjectNotFound("Contributor '{}' not found.".format(contributor_id))

        request_data = request.json
        # checking errors before updating PATCH data
        self.set_ids(request_data.get('data_sources', []))
        self.set_ids(request_data.get('preprocesses', []))
        validate_preprocesses_or_raise(request_data.get('preprocesses', []))

        schema_contributor = schema.ContributorSchema(partial=True)
        errors = schema_contributor.validate(request_data, partial=True)
        if errors:
            raise InvalidArguments(errors)

        if 'data_prefix' in request_data and contributor.data_prefix != request_data['data_prefix']:
            raise InvalidArguments('The modification of the data_prefix is not possible ({} => {})'.format(
                contributor.data_prefix, request_data['data_prefix']))
        if 'id' in request_data and contributor.id != request_data['id']:
            raise InvalidArguments('The modification of the id is not possible')

        self.upgrade_dict(contributor.data_sources, request_data, "data_sources")
        self.upgrade_dict(contributor.preprocesses, request_data, "preprocesses")

        try:
            contributor = models.Contributor.update(contributor_id, request_data)
        except PyMongoError:
            raise InternalServerError('impossible to update contributor with dataset {}'.format(request_data))

        return {'contributors': [schema.ContributorSchema().dump(contributor).data]}, 200
