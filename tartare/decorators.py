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
from functools import wraps
from typing import Any, Callable

from flask import request
import re

from tartare.core import models
from tartare.core.models import Coverage, CoverageExport
from tartare.http_exceptions import ObjectNotFound, UnsupportedMediaType, InvalidArguments
from tartare.processes.processes import PreProcessManager


id_format_text = '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
id_format = re.compile(id_format_text)

id_gridfs_text = '^[0-9a-f]{24}$'
id_gridfs = re.compile(id_gridfs_text)


class publish_params_validate(object):
    def __call__(self, func: Callable) -> Any:
        @wraps(func)
        def wrapper(*args: list, **kwargs: str) -> Any:
            # Test coverage
            coverage = Coverage.get(kwargs.get("coverage_id"))
            if not coverage:
                msg = 'Coverage not found: {}'.format(kwargs.get("coverage_id"))
                logging.getLogger(__name__).error(msg)
                raise ObjectNotFound(msg)
            # Test environment
            environment = coverage.get_environment(kwargs.get("environment_id"))
            if not environment:
                msg = 'Environment not found: {}'.format(kwargs.get("environment_id"))
                logging.getLogger(__name__).error(msg)
                raise ObjectNotFound(msg)
            # Test export
            last_export = CoverageExport.get_last(coverage.id)
            if not last_export:
                msg = 'Coverage {} without export.'.format(coverage.id)
                logging.getLogger(__name__).error(msg)
                raise ObjectNotFound(msg)
            return func(*args, **kwargs)

        return wrapper


class json_data_validate(object):
    def __call__(self, func: Callable) -> Any:
        @wraps(func)
        def wrapper(*args: list, **kwargs: str) -> Any:
            post_data = request.json
            if post_data is None:
                msg = 'request without data.'
                logging.getLogger(__name__).error(msg)
                raise UnsupportedMediaType(msg)
            return func(*args, **kwargs)

        return wrapper


class validate_contributors(object):
    def __call__(self, func: Callable) -> Any:
        @wraps(func)
        def wrapper(*args: list, **kwargs: str) -> Any:
            post_data = request.json
            if "contributors" in post_data:
                for contributor_id in post_data.get("contributors"):
                    contributor_model = models.Contributor.get(contributor_id)
                    if not contributor_model:
                        msg = "Contributor {} not found.".format(contributor_id)
                        logging.getLogger(__name__).error(msg)
                        raise InvalidArguments(msg)
            return func(*args, **kwargs)

        return wrapper


class validate_contributor_prepocesses_data_source_ids(object):
    def __call__(self, func: Callable) -> Any:
        @wraps(func)
        def wrapper(*args: list, **kwargs: str) -> Any:
            post_data = request.json
            existing_data_source_ids = [data_source['id'] for data_source in post_data.get('data_sources', []) if
                                        'id' in data_source]
            PreProcessManager.check_preprocess_data_source_integrity(post_data.get('preprocesses', []),
                                                                     existing_data_source_ids, 'contributor')
            return func(*args, **kwargs)

        return wrapper


class validate_patch_coverages(object):
    def __call__(self, func: Callable) -> Any:
        @wraps(func)
        def wrapper(*args: list, **kwargs: str) -> Any:
            post_data = request.json
            if "environments" in post_data:
                for environment_name in post_data.get("environments"):
                    environment = post_data.get("environments").get(environment_name)
                    if environment is not None and "publication_platforms" in environment:
                        msg = "'publication_platforms' field can't be updated"
                        logging.getLogger(__name__).error(msg)
                        raise InvalidArguments(msg)
            return func(*args, **kwargs)

        return wrapper


def validate_post_data_set(func: Callable) -> Any:
    @wraps(func)
    def wrapper(*args: list, **kwargs: str) -> Any:
        contributor_id = kwargs['contributor_id']
        data_source_id = kwargs['data_source_id']

        try:
            data_source = models.DataSource.get(contributor_id=contributor_id, data_source_id=data_source_id)
        except ValueError as e:
            raise ObjectNotFound(str(e))

        if data_source is None:
            raise ObjectNotFound("Data source {} not found for contributor {}.".format(data_source_id, contributor_id))

        if not request.files:
            raise InvalidArguments('No file provided.')

        if 'file' not in request.files:
            raise InvalidArguments('File provided with bad param ("file" param expected).')

        return func(*args, **kwargs)

    return wrapper


class validate_file_params(object):
    def __call__(self, func: Callable) -> Any:
        @wraps(func)
        def wrapper(*args: list, **kwargs: str) -> Any:
            contributor_id = kwargs.get("contributor_id")
            coverage_id = kwargs.get("coverage_id")
            export_id = kwargs.get("export_id")
            file_id = kwargs.get("file_id")
            environment_id = kwargs.get("environment_id")

            if not id_gridfs.match(file_id):
                msg = "Invalid file id, you give {}".format(file_id)
                logging.getLogger(__name__).error(msg)
                raise InvalidArguments(msg)

            if export_id and not id_format.match(export_id):
                msg = "Invalid export id, you give {}".format(export_id)
                logging.getLogger(__name__).error(msg)
                raise InvalidArguments(msg)

            if not coverage_id and not contributor_id:
                msg = "Invalid argument, required argument contributor_id or coverage_id"
                logging.getLogger(__name__).error(msg)
                raise InvalidArguments(msg)

            if coverage_id:
                coverage = models.Coverage.get(coverage_id)
                if not coverage:
                    msg = "Coverage not found."
                    logging.getLogger(__name__).error(msg)
                    raise ObjectNotFound(msg)
                if environment_id:
                    environment = coverage.get_environment(environment_id)
                    if not environment:
                        msg = "Environment not found."
                        logging.getLogger(__name__).error(msg)
                        raise ObjectNotFound(msg)
                    if environment.current_ntfs_id != file_id:
                        msg = "Environment file not found."
                        logging.getLogger(__name__).error(msg)
                        raise ObjectNotFound(msg)
                else:
                    coverage_export = models.CoverageExport.get(coverage_id)
                    if not coverage_export or not next((ce for ce in coverage_export if ce.gridfs_id == file_id), None):
                        msg = "Coverage export not found."
                        logging.getLogger(__name__).error(msg)
                        raise ObjectNotFound(msg)

            if contributor_id:
                contributor_export = models.ContributorExport.get(contributor_id)
                if not contributor_export or not next((ce for ce in contributor_export if ce.gridfs_id == file_id), None):
                    msg = "Contributor export not found."
                    logging.getLogger(__name__).error(msg)
                    raise ObjectNotFound(msg)

            return func(*args, **kwargs)

        return wrapper
