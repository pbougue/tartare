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
from flask import request
from marshmallow import ValidationError
from pymongo.errors import PyMongoError, DuplicateKeyError

from tartare.core import models
from tartare.decorators import JsonDataValidate, ValidateContributorPrepocessesDataSourceIds, \
    CheckContributorIntegrity, RemoveComputedDataSources, ValidateUniqueDataSourcesInContributor
from tartare.exceptions import EntityNotFound, IntegrityException
from tartare.helper import setdefault_ids
from tartare.http_exceptions import InvalidArguments, DuplicateEntry, InternalServerError, ObjectNotFound
from tartare.interfaces import schema
from tartare.processes.processes import ProcessManager


class Contributor(flask_restful.Resource):
    @classmethod
    def __pre_save_contributor(cls, post_data: dict) -> models.Contributor:
        if 'data_prefix' not in post_data:
            raise InvalidArguments('contributor data_prefix must be specified')
        # first a check on the contributor id and providing a uuid if not provided
        setdefault_ids([post_data])
        # then a check on the data_sources id and providing a uuid if not provided
        setdefault_ids(post_data.get('data_sources', []))
        processes = post_data.get('processes', [])
        ProcessManager.check_processes_for_instance(processes, 'contributor')
        setdefault_ids(processes)
        try:
            contributor = schema.ContributorSchema(strict=True).load(post_data).data
            contributor.add_computed_data_sources()
            return contributor
        except ValidationError as err:
            raise InvalidArguments(err.messages)

    @JsonDataValidate()
    @ValidateUniqueDataSourcesInContributor()
    @ValidateContributorPrepocessesDataSourceIds()
    @CheckContributorIntegrity()
    @RemoveComputedDataSources()
    def post(self) -> Response:
        post_data = request.json
        contributor = self.__pre_save_contributor(post_data)

        try:
            contributor.save()
        except DuplicateKeyError as e:
            raise DuplicateEntry('duplicate entry: {}'.format(str(e)))
        except PyMongoError:
            raise InternalServerError('impossible to add contributor {}'.format(contributor))

        return {'contributors': [
            schema.ContributorSchema(strict=True).dump(models.Contributor.get(post_data['id'])).data
        ]}, 201

    def get(self, contributor_id: Optional[str] = None) -> Response:
        try:
            if contributor_id:
                result = schema.ContributorSchema().dump(models.Contributor.get(contributor_id))
                return {'contributors': [result.data]}, 200
            contributors = models.Contributor.all()
            return {'contributors': schema.ContributorSchema(many=True).dump(contributors).data}, 200
        except EntityNotFound as e:
            raise ObjectNotFound(str(e))

    def delete(self, contributor_id: str) -> Response:
        try:
            c = models.Contributor.delete(contributor_id)
            if c == 0:
                raise ObjectNotFound("contributor '{}' not found".format(contributor_id))
            return "", 204
        except IntegrityException as e:
            raise InvalidArguments(str(e))


    @JsonDataValidate()
    @ValidateUniqueDataSourcesInContributor()
    @ValidateContributorPrepocessesDataSourceIds()
    @CheckContributorIntegrity(True)
    @RemoveComputedDataSources()
    def put(self, contributor_id: str) -> Response:
        post_data = request.json
        if 'id' in post_data and contributor_id != post_data['id']:
            raise InvalidArguments('the modification of the id is not possible')
        post_data['id'] = contributor_id
        new_contributor = self.__pre_save_contributor(post_data)
        try:
            existing_contributor = models.Contributor.get(contributor_id)
            existing_contributor.update_with_object(new_contributor)
        except EntityNotFound as e:
            raise ObjectNotFound(str(e))
        except DuplicateKeyError as e:
            raise DuplicateEntry('duplicate entry: {}'.format(str(e)))
        except PyMongoError:
            raise InternalServerError('impossible to add contributor {}'.format(new_contributor))

        return {'contributors': [
            schema.ContributorSchema(strict=True).dump(models.Contributor.get(contributor_id)).data
        ]}, 200
