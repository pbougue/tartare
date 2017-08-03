#!/usr/bin/env python
# coding: utf-8

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
from flask import Response
from flask.globals import request
from flask_restful import Resource
from tartare.core import models
from tartare.http_exceptions import InvalidArguments, ObjectNotFound


class DataSet(Resource):
    def post(self, contributor_id: str, data_source_id: str) -> Response:
        try:
            data_source = models.DataSource.get(contributor_id=contributor_id, data_source_id=data_source_id)
        except ValueError as e:
            raise ObjectNotFound(str(e))

        if data_source is None:
            raise ObjectNotFound("Data source {} not found.".format(data_source_id))

        if not request.files:
            raise InvalidArguments('No file provided.')

        if 'file' not in request.files:
            raise InvalidArguments('File provided with bad param ("file" param expected).')

        file = request.files['file']
        data_source_fetched = models.DataSourceFetched(contributor_id=contributor_id,
                                                       data_source_id=data_source_id)
        data_source_fetched.save_dataset(file.filename, os.path.basename(file.filename))
        data_source_fetched.save()

        return {'data_sets': [models.MongoDataSourceFetchedSchema().dump(data_source_fetched).data]}, 201
