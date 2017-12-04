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
from flask import Response
from tartare.core import models
from tartare.core.constants import INPUT_TYPE_URL
from tartare.core.contributor_export_functions import fetch_and_save_dataset
from tartare.exceptions import FetcherException
from tartare.http_exceptions import InvalidArguments, InternalServerError, ObjectNotFound


class DataSourceFetch(flask_restful.Resource):
    def post(self, contributor_id: str, data_source_id: str) -> Response:
        try:
            data_source = models.DataSource.get_one(contributor_id=contributor_id, data_source_id=data_source_id)
        except ValueError as e:
            raise ObjectNotFound(str(e))

        if not data_source.is_type(INPUT_TYPE_URL) or not data_source.input.url:
            raise InvalidArguments('data source type should be {}'.format(INPUT_TYPE_URL))

        try:
            fetch_and_save_dataset(contributor_id, data_source)
        except FetcherException as e:
            raise InternalServerError('fetching {} failed: {}'.format(data_source.input.url, str(e)))

        return '', 204
