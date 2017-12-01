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
from typing import Tuple, List
from zipfile import ZipFile, is_zipfile

from flask import Response
from flask.globals import request
from flask_restful import Resource
from tartare import tasks
from tartare.core import models
from tartare.http_exceptions import InvalidArguments, ObjectNotFound

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


def is_valid_file(zip_file: ZipFile) -> Tuple[bool, List[str]]:
    """
        :return: list of missing files among CALENDAR_REQUESTED_FILE
    """
    valid_file = True
    missing_files = []
    for request_file, header in CALENDAR_REQUESTED_FILE.items():
        file_exist = request_file in zip_file.namelist()
        if not file_exist:
            missing_files.append(request_file)
            logging.getLogger(__name__).warning('file {} is missing'.format(request_file))
        valid_file = valid_file and file_exist
    return valid_file, missing_files


def check_files_header(zip_file: ZipFile) -> Tuple[bool, List[str]]:
    """
        :return: list of invalid files among CALENDAR_REQUESTED_FILE
    """
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
    def post(self, coverage_id: str) -> Response:
        coverage = models.Coverage.get(coverage_id)
        if coverage is None:
            raise ObjectNotFound("Coverage {} not found.".format(coverage_id))

        if not request.files:
            raise InvalidArguments('The archive is missing.')
        content = request.files['file']
        logger = logging.getLogger(__name__)
        logger.info('content received: {}'.format(content))
        if not is_zipfile(content):
            raise InvalidArguments('Invalid ZIP.')
        zip_file = ZipFile(content)
        valid_file, missing_files = is_valid_file(zip_file)
        if not valid_file:
            raise InvalidArguments('File(s) missing : {}.'.format(''.join(missing_files)))
        # check files header
        valid_header, invalid_files = check_files_header(zip_file)
        if not valid_header:
            raise InvalidArguments('Non-compliant file(s) : {}.'.format(''.join(invalid_files)))

        content.stream.seek(0)
        coverage.save_grid_calendars(content)
        zip_file.close()

        # run the update of navitia in background
        for k, env in coverage.environments.items():
            if env.current_ntfs_id:
                # @TODO: use a chain later
                tasks.send_ntfs_to_tyr.delay(coverage.id, k)

        return {'message': 'OK'}, 200
