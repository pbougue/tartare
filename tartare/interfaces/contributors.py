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
import logging
from flask import request
from tartare.interfaces import schema
from marshmallow import ValidationError
import uuid
from tartare.exceptions import InvalidArguments, DuplicateEntry, InternalServerError, ResourceNotFound



class Contributor(flask_restful.Resource):
    def post(self):
        post_data = request.json
        #first a check on the data_sources id and providing a uuid if not provided
        for ds in post_data.get('data_sources', []):
            if not ds.get('id', None):
                ds['id'] = str(uuid.uuid4())

        contributor_schema = schema.ContributorSchema(strict=True)
        try:
            contributor = contributor_schema.load(post_data).data
        except ValidationError as err:
            raise InvalidArguments(err.messages)

        contributor_id = post_data["id"]
        try:
            contributor.save()
        except DuplicateKeyError as e:
            raise DuplicateEntry("Impossible to add contributor, id {} or data_prefix {} already used."
                                 .format(request.json['id'], request.json['data_prefix']))
        except PyMongoError:
            raise InternalServerError('Impossible to add contributor {}'.format(contributor))

        return {'contributors': [contributor_schema.dump(models.Contributor.get(contributor_id)).data]}, 201

    def get(self, contributor_id=None):
        if contributor_id:
            c = models.Contributor.get(contributor_id)
            if c is None:
                raise ResourceNotFound("Contributor '{}' not found.".format(contributor_id))
            result = schema.ContributorSchema().dump(c)
            return {'contributors': [result.data]}, 200
        contributors = models.Contributor.all()
        return {'contributors': schema.ContributorSchema(many=True).dump(contributors).data}, 200

    def delete(self, contributor_id):
        c = models.Contributor.delete(contributor_id)
        if c == 0:
            raise ResourceNotFound("Contributor '{}' not found.".format(contributor_id))
        return "", 204

    def patch(self, contributor_id):
        # "data_prefix" field is not modifiable, impacts of the modification
        # need to be checked. The previous value needs to be checked for an error
        contributor = models.Contributor.get(contributor_id)
        if contributor is None:
            raise ResourceNotFound("Contributor '{}' not found.".format(contributor_id))

        request_data = request.json
        #checking errors before updating PATCH data
        for ds in request_data.get('data_sources', []):
            if not ds.get('id', None):
                ds['id'] = str(uuid.uuid4())

        schema_contributor = schema.ContributorSchema(partial=True)
        errors = schema_contributor.validate(request_data, partial=True)
        if errors:
            raise InvalidArguments(errors)

        if 'data_prefix' in request_data and contributor.data_prefix != request_data['data_prefix']:
            raise InvalidArguments('The modification of the data_prefix is not possible ({} => {})'.format(
                contributor.data_prefix, request_data['data_prefix']))
        if 'id' in request_data and contributor.id != request_data['id']:
            raise InvalidArguments('The modification of the id is not possible')

        existing_ds_id = [d.id for d in contributor.data_sources]
        logging.getLogger(__name__).debug("PATCH : list of existing data_sources ids %s", str(existing_ds_id))

        #constructing PATCH data
        patched_data_sources = None
        if "data_sources" in request_data:
            patched_data_sources = schema.DataSourceSchema(many=True).dump(contributor.data_sources).data

            for ds in request_data["data_sources"]:
                if ds['id'] in existing_ds_id:
                    pds = next((p for p in patched_data_sources if p['id'] == ds['id']), None)
                    if pds:
                        pds.update(ds)
                else:
                    #adding a new data_source
                    patched_data_sources.append(ds)
        if patched_data_sources:
            request_data['data_sources'] = patched_data_sources
        try:
            contributor = models.Contributor.update(contributor_id, request_data)
        except PyMongoError:
            raise InternalServerError('impossible to update contributor with dataset {}'.format(request_data))

        return {'contributors': [schema.ContributorSchema().dump(contributor).data]}, 200
