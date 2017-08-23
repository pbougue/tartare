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

from tartare.core import models
from tartare.core.models import Coverage, CoverageExport
from tartare.http_exceptions import ObjectNotFound, UnsupportedMediaType, InvalidArguments
from tartare.processes.processes import PreProcessManager


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
            PreProcessManager.check_preprocess_data_source_integrity(post_data.get('preprocesses', []),
                                                                     post_data.get('data_sources', []), 'contributor')
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
