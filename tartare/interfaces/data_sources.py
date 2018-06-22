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

from tartare.core import models
from tartare.exceptions import EntityNotFound
from tartare.http_exceptions import ObjectNotFound
from tartare.interfaces import schema


class DataSource(flask_restful.Resource):
    def get(self, contributor_id: str, data_source_id: Optional[str] = None) -> Response:
        try:
            data_sources = models.DataSource.get(contributor_id, data_source_id)
            if not data_sources and data_source_id:
                raise ObjectNotFound(
                    "data source '{}' not found for contributor '{}'".format(data_source_id, contributor_id))
        except EntityNotFound as e:
            raise ObjectNotFound(str(e))

        return {'data_sources': schema.DataSourceSchema(many=True).dump(data_sources).data}, 200
