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
from flask import Response
from pymongo.errors import PyMongoError
from tartare.core import models
from tartare.exceptions import IntegrityException, EntityNotFound
from tartare.interfaces import schema
from tartare.http_exceptions import InvalidArguments, DuplicateEntry, InternalServerError, ObjectNotFound
from tartare.decorators import JsonDataValidate


class CoverageContributorSubscription(flask_restful.Resource):
    @JsonDataValidate()
    def post(self, coverage_id: str) -> Response:
        coverage = models.Coverage.get(coverage_id)
        if coverage is None:
            raise ObjectNotFound("coverage {} not found".format(coverage_id))

        if 'id' not in request.json:
            raise InvalidArguments('missing contributor_id attribute in request body')

        contributor_id = request.json['id']
        try:
            contributor = models.Contributor.get(contributor_id=contributor_id)
            if coverage.has_contributor(contributor):
                raise DuplicateEntry('contributor id {} already exists in coverage {}'
                                     .format(contributor_id, coverage_id))
            coverage.add_contributor(contributor)
        except EntityNotFound as e:
            raise ObjectNotFound(str(e))
        except (PyMongoError, ValueError):
            raise InternalServerError('impossible to update coverage {} with contributor {}'
                                      .format(coverage_id, contributor_id))
        except IntegrityException as e:
            raise InvalidArguments(str(e))

        return {'coverages': schema.CoverageSchema().dump([coverage], many=True).data}, 201

    def delete(self, coverage_id: str, contributor_id: str) -> Response:
        coverage = models.Coverage.get(coverage_id)
        if coverage is None:
            raise ObjectNotFound('unknown coverage id "{}"'.format(coverage_id))

        if contributor_id not in coverage.contributors_ids:
            raise ObjectNotFound('unknown contributor id "{}" attribute in uri'.format(contributor_id))

        try:
            coverage.remove_contributor(contributor_id)
        except (PyMongoError, ValueError):
            raise InternalServerError

        return {'contributors': None}, 204
