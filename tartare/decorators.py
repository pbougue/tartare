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
import re
from functools import wraps
from typing import Any, Callable, List

from flask import request

from tartare.core import models
from tartare.core.constants import DATA_TYPE_PUBLIC_TRANSPORT, DATA_FORMAT_BY_DATA_TYPE, DATA_FORMAT_DEFAULT, \
    DATA_FORMAT_VALUES, DATA_FORMAT_OSM_FILE, DATA_FORMAT_POLY_FILE, INPUT_TYPE_COMPUTED
from tartare.core.models import DataSource
from tartare.http_exceptions import ObjectNotFound, UnsupportedMediaType, InvalidArguments, InternalServerError
from tartare.processes.processes import PreProcessManager

id_format_text = '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
id_format = re.compile(id_format_text)

id_gridfs_text = '^[0-9a-f]{24}$'
id_gridfs = re.compile(id_gridfs_text)


def check_excepted_data_format(data_format: str, data_type: str) -> None:
    if data_format not in DATA_FORMAT_VALUES:
        msg = 'choice "{}" not in possible values {}'.format(data_format, DATA_FORMAT_VALUES)
        logging.getLogger(__name__).error(msg)
        raise InvalidArguments(msg)

    if data_format not in DATA_FORMAT_BY_DATA_TYPE[data_type]:
        msg = "data source format {} is incompatible with contributor data_type {}, possibles values are: '{}'".format(
            data_format, data_type, ','.join(DATA_FORMAT_BY_DATA_TYPE[data_type]))
        logging.getLogger(__name__).error(msg)
        raise InvalidArguments(msg)


def check_contributor_data_source_osm_and_poly_constraint(existing_data_sources: List[DataSource],
                                                          new_data_sources: List[dict]) -> None:
    for data_format in [DATA_FORMAT_OSM_FILE, DATA_FORMAT_POLY_FILE]:
        existing_ds_ids = [ds_model.id for ds_model in existing_data_sources if
                           ds_model.data_format == data_format]
        if len(existing_ds_ids) > 1:
            raise InternalServerError('found contributor with more than one {} data source'.format(data_format))
        new_ds = [ds_dict for ds_dict in new_data_sources if
                  ds_dict.get('data_format', DATA_FORMAT_DEFAULT) == data_format and
                  ds_dict.get('id') not in existing_ds_ids]
        if len(new_ds) + len(existing_ds_ids) > 1:
            msg = "contributor contains more than one {} data source".format(data_format)
            logging.getLogger(__name__).error(msg)
            raise InvalidArguments(msg)


class JsonDataValidate(object):
    def __call__(self, func: Callable) -> Any:
        @wraps(func)
        def wrapper(*args: list, **kwargs: str) -> Any:
            post_data = request.json
            if post_data is None:
                msg = 'request without data'
                logging.getLogger(__name__).error(msg)
                raise UnsupportedMediaType(msg)
            return func(*args, **kwargs)

        return wrapper


class ValidateContributors(object):
    def __call__(self, func: Callable) -> Any:
        @wraps(func)
        def wrapper(*args: list, **kwargs: str) -> Any:
            post_data = request.json
            if "contributors" in post_data:
                for contributor_id in post_data.get("contributors"):
                    contributor_model = models.Contributor.get(contributor_id)
                    if not contributor_model:
                        msg = "contributor {} not found".format(contributor_id)
                        logging.getLogger(__name__).error(msg)
                        raise InvalidArguments(msg)
            return func(*args, **kwargs)

        return wrapper


class ValidateContributorPrepocessesDataSourceIds(object):
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


class RemoveComputedDataSources(object):
    def __call__(self, func: Callable) -> Any:
        @wraps(func)
        def wrapper(*args: list, **kwargs: str) -> Any:
            post_data = request.json
            non_computed_data_sources = [ds for ds in post_data.get('data_sources', [])
                                         if 'input' not in ds or ds.get('input').get('type') != INPUT_TYPE_COMPUTED]
            post_data['data_sources'] = non_computed_data_sources

            return func(*args, **kwargs)

        return wrapper


class CheckContributorIntegrity(object):
    def __init__(self, method: str) -> None:
        self.method = method

    def __call__(self, func: Callable) -> Any:
        @wraps(func)
        def wrapper(*args: list, **kwargs: str) -> Any:
            post_data = request.json
            contributor_id = kwargs.get('contributor_id', None)

            if not self.method == 'POST' and not contributor_id:
                msg = "contributor_id not present in request"
                logging.getLogger(__name__).error(msg)
                raise ObjectNotFound(msg)

            if contributor_id:
                contributor = models.Contributor.get(contributor_id)
                if not contributor:
                    msg = "contributor '{}' not found".format(contributor_id)
                    logging.getLogger(__name__).error(msg)
                    raise ObjectNotFound(msg)
                data_type = post_data.get('data_type', contributor.data_type)
                existing_data_sources = contributor.data_sources
            else:
                data_type = post_data.get('data_type', DATA_TYPE_PUBLIC_TRANSPORT)
                existing_data_sources = []
            data_sources = post_data.get('data_sources', [])
            if self.method == 'PATCH':
                for existing_data_source in existing_data_sources:
                    check_excepted_data_format(existing_data_source.data_format, data_type)
            if data_sources:
                for data_source in post_data.get('data_sources', []):
                    check_excepted_data_format(data_source.get('data_format', DATA_FORMAT_DEFAULT), data_type)
                check_contributor_data_source_osm_and_poly_constraint(existing_data_sources, data_sources)
            return func(*args, **kwargs)

        return wrapper


class CheckDataSourceIntegrity(object):
    def __init__(self, data_source_id_required: bool = False) -> None:
        self.data_source_id_required = data_source_id_required

    def __call__(self, func: Callable) -> Any:
        @wraps(func)
        def wrapper(*args: list, **kwargs: str) -> Any:
            post_data = request.json
            contributor_id = kwargs.get('contributor_id', None)
            data_source_id = kwargs.get('data_source_id', None)
            if self.data_source_id_required and not data_source_id:
                msg = "data_source_id not present in request"
                logging.getLogger(__name__).error(msg)
                raise ObjectNotFound(msg)
            contributor = models.Contributor.get(contributor_id)
            if not contributor:
                msg = "contributor '{}' not found".format(contributor_id)
                logging.getLogger(__name__).error(msg)
                raise ObjectNotFound(msg)
            data_type = contributor.data_type
            new_data_source = post_data.copy()
            if self.data_source_id_required:
                try:
                    models.DataSource.get_one(contributor_id, data_source_id)
                except ValueError as e:
                    raise ObjectNotFound(str(e))
                new_data_source['id'] = data_source_id
                if post_data.get('data_format'):
                    check_excepted_data_format(post_data.get('data_format'), data_type)
            else:
                check_excepted_data_format(post_data.get('data_format', DATA_FORMAT_DEFAULT), data_type)
            check_contributor_data_source_osm_and_poly_constraint(contributor.data_sources, [new_data_source])

            return func(*args, **kwargs)

        return wrapper


class ValidatePatchCoverages(object):
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
            data_source = models.DataSource.get_one(contributor_id=contributor_id, data_source_id=data_source_id)
        except ValueError as e:
            raise ObjectNotFound(str(e))

        if data_source is None:
            raise ObjectNotFound("data source {} not found for contributor {}".format(data_source_id, contributor_id))

        if not request.files:
            raise InvalidArguments('no file provided')

        if 'file' not in request.files:
            raise InvalidArguments('file provided with bad param ("file" param expected)')

        return func(*args, **kwargs)

    return wrapper


def validate_get_data_sets(func: Callable) -> Any:
    @wraps(func)
    def wrapper(*args: list, **kwargs: str) -> Any:
        contributor_id = kwargs['contributor_id']
        data_source_id = kwargs['data_source_id']

        try:
            data_source = models.DataSource.get_one(contributor_id=contributor_id, data_source_id=data_source_id)
        except ValueError as e:
            raise ObjectNotFound(str(e))

        if data_source is None:
            raise ObjectNotFound("data source {} not found for contributor {}".format(data_source_id, contributor_id))

        return func(*args, **kwargs)

    return wrapper


class validate_file_params(object):
    def __call__(self, func: Callable) -> Any:
        @wraps(func)
        def wrapper(*args: list, **kwargs: str) -> Any:
            file_id = kwargs.get("file_id")

            if not id_gridfs.match(file_id):
                msg = "invalid file id, you give {}".format(file_id)
                logging.getLogger(__name__).error(msg)
                raise InvalidArguments(msg)

            return func(*args, **kwargs)

        return wrapper
