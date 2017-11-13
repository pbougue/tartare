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

from typing import Optional
import flask_restful
from flask import Response
from pymongo.errors import PyMongoError, DuplicateKeyError
from tartare.core import models
from flask import request
from tartare.interfaces import schema
from marshmallow import ValidationError
from tartare.http_exceptions import InvalidArguments, DuplicateEntry, InternalServerError, ObjectNotFound
from tartare.helper import setdefault_ids
from tartare.core.mongodb_helper import upgrade_dict
from tartare.decorators import json_data_validate, validate_contributor_prepocesses_data_source_ids, \
    check_contributor_integrity
from tartare.processes.processes import PreProcessManager


class Contributor(flask_restful.Resource):
    @json_data_validate()
    @validate_contributor_prepocesses_data_source_ids()
    @check_contributor_integrity()
    def post(self) -> Response:
        post_data = request.json
        if 'data_prefix' not in post_data:
            raise InvalidArguments('contributor data_prefix must be specified')
        # first a check on the contributor id and providing a uuid if not provided
        setdefault_ids([post_data])

        # then a check on the data_sources id and providing a uuid if not provided
        setdefault_ids(post_data.get('data_sources', []))

        preprocesses = post_data.get('preprocesses', [])

        PreProcessManager.check_preprocesses_for_instance(preprocesses, 'contributor')

        setdefault_ids(preprocesses)

        contributor_schema = schema.ContributorSchema(strict=True)

        try:
            contributor = contributor_schema.load(post_data).data
        except ValidationError as err:
            raise InvalidArguments(err.messages)

        try:
            contributor.save()
        except DuplicateKeyError as e:
            raise DuplicateEntry('duplicate entry: {}'.format(str(e)))
        except PyMongoError:
            raise InternalServerError('Impossible to add contributor {}'.format(contributor))

        return {'contributors': [contributor_schema.dump(models.Contributor.get(post_data['id'])).data]}, 201

    def get(self, contributor_id: Optional[str]=None) -> Response:
        if contributor_id:
            c = models.Contributor.get(contributor_id)
            if c is None:
                raise ObjectNotFound("Contributor '{}' not found.".format(contributor_id))
            result = schema.ContributorSchema().dump(c)
            return {'contributors': [result.data]}, 200
        contributors = models.Contributor.all()
        return {'contributors': schema.ContributorSchema(many=True).dump(contributors).data}, 200

    def delete(self, contributor_id: str) -> Response:
        c = models.Contributor.delete(contributor_id)
        if c == 0:
            raise ObjectNotFound("Contributor '{}' not found.".format(contributor_id))
        return "", 204

    @json_data_validate()
    @check_contributor_integrity(True)
    def patch(self, contributor_id: str) -> Response:
        # "data_prefix" field is not modifiable, impacts of the modification
        # need to be checked. The previous value needs to be checked for an error
        contributor = models.Contributor.get(contributor_id)
        request_data = request.json
        preprocess_dict_list = request_data.get('preprocesses', [])
        data_sources_dict_list = request_data.get('data_sources', [])

        # checking errors before updating PATCH data
        setdefault_ids(data_sources_dict_list)
        setdefault_ids(preprocess_dict_list)

        PreProcessManager.check_preprocesses_for_instance(preprocess_dict_list, 'contributor')
        existing_data_source_ids = [data_source.id for data_source in contributor.data_sources]
        PreProcessManager.check_preprocess_data_source_integrity(preprocess_dict_list, existing_data_source_ids, 'contributor')

        schema_contributor = schema.ContributorSchema(partial=True)
        errors = schema_contributor.validate(request_data, partial=True)
        if errors:
            raise InvalidArguments(errors)

        if 'data_prefix' in request_data and contributor.data_prefix != request_data['data_prefix']:
            raise InvalidArguments('The modification of the data_prefix is not possible ({} => {})'.format(
                contributor.data_prefix, request_data['data_prefix']))
        if 'id' in request_data and contributor.id != request_data['id']:
            raise InvalidArguments('The modification of the id is not possible')

        upgrade_dict(contributor.data_sources, request_data, "data_sources")
        upgrade_dict(contributor.preprocesses, request_data, "preprocesses")

        try:
            contributor = models.Contributor.update(contributor_id, request_data)
        except PyMongoError:
            raise InternalServerError('impossible to update contributor with payload {}'.format(request_data))

        return {'contributors': [schema.ContributorSchema().dump(contributor).data]}, 200
