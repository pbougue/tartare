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
import zipfile
import os
from flask.globals import request
from flask_restful import Resource
from tartare import app
from tartare.core import models
import shutil

GRID_CALENDARS = "grid_calendars.txt"
GRID_CALENDARS_HEADER = {'id', 'name', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday',
                         'sunday'}
GRID_PERIODS = "grid_periods.txt"
GRID_PERIODS_HEADER = {'calendar_id', 'begin_date', 'end_date'}
GRID_CALENDAR_NETWORK_LINE = "grid_rel_calendar_to_network_and_line.txt"
GRID_CALENDAR_NETWORK_LINE_HEADER = {'grid_calendar_id', 'network_id'}
CALENDAR_REQUESTED_FILE = {GRID_CALENDARS: GRID_CALENDARS_HEADER,
                           GRID_PERIODS: GRID_PERIODS_HEADER,
                           GRID_CALENDAR_NETWORK_LINE: GRID_CALENDAR_NETWORK_LINE_HEADER}


def is_valid_file(zip_file):
    valid_file = True
    missing_files = []
    for request_file, header in CALENDAR_REQUESTED_FILE.items():
        file_exist = request_file in zip_file.namelist()
        if not file_exist:
            missing_files.append(request_file)
            logging.getLogger(__name__).warning('file {} is missing'.format(request_file))
        valid_file = valid_file and file_exist
    return valid_file, missing_files


def check_files_header(zip_file):
    valid_header = True
    invalid_files = []
    for request_file, header in CALENDAR_REQUESTED_FILE.items():
        valid_file_header = True
        with zip_file.open(request_file) as f:
            line = next(line for line in f).decode("utf-8")
            file_columns = line.rstrip().split(',')
        for column in header:
            valid_file_header = valid_file_header and (column in file_columns)
        if not valid_file_header:
            invalid_files.append(request_file)
            logging.getLogger(__name__).warning('invalid header for {}'.format(request_file))
        valid_header = valid_header and valid_file_header
    return valid_header, invalid_files


class GridCalendar(Resource):
    def post(self, coverage_id):
        coverage = models.Coverage.get(coverage_id)
        if coverage is None:
            return {'message': 'bad coverage {}'.format(coverage_id)}, 400

        if not request.files:
            return {'message': 'the archive is missing'}, 400
        content = request.files['file']
        logger = logging.getLogger(__name__)
        logger.info('content received: {}'.format(content))
        if not zipfile.is_zipfile(content):
            return {'message': ' invalid ZIP'}, 400
        zip_file = zipfile.ZipFile(content)
        valid_file, missing_files = is_valid_file(zip_file)
        if not valid_file:
            return {'message': 'file(s) missing : {}'.format(''.join(missing_files))}, 400
        # check files header
        valid_header, invalid_files = check_files_header(zip_file)
        if not valid_header:
            return {'message': 'non-compliant file(s) : {}'.format(''.join(invalid_files))}, 400

        # backup content
        input_dir = coverage.technical_conf.input_dir
        if not os.path.exists(input_dir):
            os.makedirs(input_dir)
        content.stream.seek(0)
        content.save(os.path.join(input_dir, content.filename + ".tmp"))
        zip_file.close()
        full_file_name = os.path.join(os.path.realpath(input_dir), content.filename)

        shutil.move(full_file_name + ".tmp", full_file_name)

        return {'message': 'OK'}, 200
