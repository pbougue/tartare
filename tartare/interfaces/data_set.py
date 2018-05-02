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

from tartare.core.models import Contributor
from tartare.core.models import DataSet as DataSetModel
from tartare.core.validity_period_finder import ValidityPeriodFinder
from tartare.decorators import validate_post_data_set
from tartare.interfaces import schema


class DataSet(Resource):
    @validate_post_data_set
    def post(self, contributor_id: str, data_source_id: str) -> Response:
        file = request.files['file']
        contributor = Contributor.get(contributor_id)
        data_source = contributor.get_data_source(data_source_id)
        validity_period = ValidityPeriodFinder.select_computer_and_find(file.filename, data_source.data_format)
        data_set = DataSetModel(validity_period=validity_period)
        data_set.add_file_from_io(file, os.path.basename(file.filename))
        data_source.add_data_set_and_update_contributor(data_set, contributor)
        return {'data_sets': [schema.DataSetSchema().dump(data_set).data]}, 201
