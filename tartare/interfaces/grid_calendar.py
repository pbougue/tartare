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
import shutil
from flask.globals import request
from flask_restful import Resource
from flask import jsonify
from tartare import app

GRID_CALENDARS = "grid_calendars.txt"
GRID_CALENDARS_HEADER = {'grid_calendar_id', 'name', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday',
                         'sunday'}
GRID_PERIODS = "grid_periods.txt"
GRID_PERIODS_HEADER = {'grid_calendar_id', 'start_date', 'end_date'}
GRID_CALENDAR_NETWORK_LINE = "grid_rel_calendar_to_network_and_line.txt"
GRID_CALENDAR_NETWORK_LINE_HEADER = {'grid_calendar_id', 'network_id', 'line_code'}
CALENDAR_REQUESTED_FILE = {GRID_CALENDARS, GRID_PERIODS, GRID_CALENDAR_NETWORK_LINE}


def is_valid_file(zip_file):
    files = zipfile.ZipFile(zip_file, 'r').namelist()
    valid_file = True
    for request_file in CALENDAR_REQUESTED_FILE:
        valid_file = valid_file and request_file in files
        if not valid_file:
            logging.getLogger(__name__).critical('file {} is missing'.format(request_file))
    return valid_file


def get_header(file):
    if file == GRID_CALENDARS:
        return GRID_CALENDARS_HEADER
    if file == GRID_PERIODS:
        return GRID_PERIODS_HEADER
    if file == GRID_CALENDAR_NETWORK_LINE:
        return GRID_CALENDAR_NETWORK_LINE_HEADER


def check_files_header(work_dir):
    valid_header = True
    for request_file in CALENDAR_REQUESTED_FILE:
        header = get_header(request_file)
        columns = open(os.path.join(work_dir, request_file), 'r').readline().split(',')
        valid_header = valid_header and (column in header for column in columns)
        if not valid_header:
            logging.getLogger(__name__).critical('invalid header for {}'.format(request_file))
    return valid_header


def make_response(status_code, message):
    response = jsonify({
        'status': status_code,
        'message': message
    })
    print(response)
    response.status_code = status_code
    return response


class GridCalendar(Resource):
    def post(self):
        if request.files:
            content = request.files['file']
            logger = logging.getLogger(__name__)
            logger.info('content received: {}'.format(content))
            if zipfile.is_zipfile(content) and is_valid_file(content):
                work_dir = app.config.get("GRID_CALENDAR_DIR")
                zipfile.ZipFile(content, 'r').extractall(work_dir)
                # check files header
                if check_files_header(work_dir):
                    # backup content
                    bck_dir = os.path.join(work_dir, 'backup')
                    if not os.path.exists(bck_dir):
                        os.makedirs(bck_dir)
                    file_list = [f for f in os.listdir(work_dir) if os.path.isfile(os.path.join(work_dir, f))]
                    for filename in file_list:
                        input_file = os.path.join(work_dir, filename)
                        output_file = os.path.join(bck_dir, filename)
                        shutil.move(input_file, output_file)
                    return make_response(200, 'OK')
                else:
                    return make_response(400, 'non-compliant file')
            else:
                return make_response(400, 'file(s) missing')
        else:
            return make_response(400, 'the archive is missing')

