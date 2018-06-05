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
import logging
from typing import Optional

import flask_restful
from flask import Response
from flask import request
from marshmallow import ValidationError
from pymongo.errors import PyMongoError, DuplicateKeyError

from tartare.core import models
from tartare.decorators import JsonDataValidate, RemoveLastActiveJob, \
    ValidateInputDataSourceIds
from tartare.helper import setdefault_ids
from tartare.http_exceptions import InvalidArguments, DuplicateEntry, InternalServerError, ObjectNotFound
from tartare.interfaces import schema
from tartare.processes.processes import PreProcessManager


class Coverage(flask_restful.Resource):
    @classmethod
    def __pre_save_coverage(self, post_data: dict) -> models.Coverage:
        coverage_schema = schema.CoverageSchema(strict=True)
        preprocesses = post_data.get('preprocesses', [])
        PreProcessManager.check_preprocesses_for_instance(preprocesses, 'coverage')
        setdefault_ids(preprocesses)
        try:
            coverage = coverage_schema.load(post_data).data
            coverage.add_computed_data_sources()
            return coverage
        except ValidationError as err:
            raise InvalidArguments(err.messages)

    @JsonDataValidate()
    @ValidateInputDataSourceIds()
    def post(self) -> Response:
        coverage = self.__pre_save_coverage(request.json)
        try:
            coverage.save()
        except DuplicateKeyError:
            raise DuplicateEntry("coverage {} already exists".format(request.json['id']))
        except PyMongoError:
            raise InternalServerError('impossible to add coverage')

        response, status = self.get(coverage.id)
        return response, 201

    def get(self, coverage_id: Optional[str]=None) -> Response:
        if coverage_id:
            c = models.Coverage.get(coverage_id)
            if c is None:
                raise ObjectNotFound("coverage '{}' not found".format(coverage_id))

            result = schema.CoverageSchema().dump(c)
            return {'coverages': [result.data]}, 200

        coverages = models.Coverage.all()

        return {'coverages': schema.CoverageSchema(many=True).dump(coverages).data}, 200

    def delete(self, coverage_id: str) -> Response:
        c = models.Coverage.delete(coverage_id)
        if c == 0:
            raise ObjectNotFound("coverage '{}' not found".format(coverage_id))
        return "", 204

    @JsonDataValidate()
    @ValidateInputDataSourceIds()
    @RemoveLastActiveJob()
    def put(self, coverage_id: str) -> Response:
        post_data = request.json
        if 'id' in post_data and coverage_id != post_data['id']:
            raise InvalidArguments('the modification of the id is not possible')
        post_data['id'] = coverage_id
        new_coverage = self.__pre_save_coverage(request.json)
        try:
            existing_coverage = models.Coverage.get(coverage_id)
            existing_coverage.update_with_object(new_coverage)
        except DuplicateKeyError:
            raise DuplicateEntry("coverage {} already exists".format(request.json['id']))
        except PyMongoError:
            raise InternalServerError('impossible to add coverage')
        return self.get(coverage_id)
