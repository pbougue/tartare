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
import flask
from flask.globals import request
from flask_restful import Resource
from tartare.core import models, data_handler
import tempfile
import shutil
from tartare import tasks


class DataUpdate(Resource):
    def post(self, coverage_id, environment_type):
        coverage = models.Coverage.get(coverage_id)
        if coverage is None:
            return {'message': 'bad coverage {}'.format(coverage_id)}, 404

        if environment_type not in coverage.environments:
            return {'message': 'bad environment {}'.format(environment_type)}, 404

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

            #TODO: improve this function so we don't have to write the file localy first
            file_type, file_name = data_handler.type_of_data(tmp_file)
            if file_type in [None, "tmp"] :
                logger.warning('invalid file provided: %s', content.filename)
                return {'message': 'invalid file provided: {}'.format(content.filename)}, 400
            with open(tmp_file, 'rb') as file:
                if file_type == 'fusio': #ntfs is called fusio in type_of_data
                    coverage.save_ntfs(environment_type, file)
                    tasks.send_ntfs_to_tyr.delay(coverage_id, environment_type)
                else:
                    #we need to temporary save the file before sending it
                    file_id = models.save_file_in_gridfs(file, filename=content.filename)
                    tasks.send_file_to_tyr_and_discard.delay(coverage_id, environment_type, file_id)

        return {'message': 'Valid {} file provided : {}'.format(file_type, file_name)}, 200

    def get(self, coverage_id, environment_type):
        coverage = models.Coverage.get(coverage_id)
        if coverage is None:
            return {'message': 'bad coverage {}'.format(coverage_id)}, 404
        if environment_type not in coverage.environments:
            return {'message': 'bad environment {}'.format(environment_type)}, 404
        ntfs_file_id = coverage.environments[environment_type].current_ntfs_id
        ntfs_file = models.get_file_from_gridfs(ntfs_file_id)
        return flask.send_file(ntfs_file, mimetype='application/zip')
