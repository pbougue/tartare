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

import logging
import os
from flask.globals import request
from flask_restful import Resource
from tartare.core import models, data_handler
import tempfile
import shutil


class DataUpdate(Resource):
    def post(self, coverage_id):
        coverage = models.Coverage.get(coverage_id)
        if coverage is None:
            return {'message': 'bad coverage {}'.format(coverage_id)}, 404

        if not request.files :
            return {'message': 'no file provided'}, 400
        if request.files and 'file' not in request.files:
            return {'message': 'file provided with bad param ("file" param expected)'}, 400
        content = request.files['file']
        logger = logging.getLogger(__name__)
        logger.info('content received: %s', content)
        with tempfile.TemporaryDirectory() as tmpdirname:
            tmp_file = os.path.join(tmpdirname, content.filename)
            content.save(tmp_file)

            file_type, file_name = data_handler.type_of_data(tmp_file)
            if file_type in [None, "tmp"] :
                logger.warning('invalid file provided: %s', content.filename)
                return {'message': 'invalid file provided: {}'.format(content.filename)}, 400

            # backup content
            input_dir = coverage.technical_conf.input_dir
            if not os.path.exists(input_dir):
                os.makedirs(input_dir)
            full_file_name = os.path.join(os.path.realpath(input_dir), content.filename)
            shutil.move(tmp_file, full_file_name + ".tmp")
            shutil.move(full_file_name + ".tmp", full_file_name)

        return {'message': 'Valid {} file provided : {}'.format(file_type, file_name)}, 200
