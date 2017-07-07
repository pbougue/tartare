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

import logging.config
from io import IOBase
from typing import Union, Any, Optional
import celery
from celery import Celery
from collections.abc import Mapping
import requests
from flask import Flask
from requests import Response
from gridfs.grid_file import GridOut
from tartare.processes.processes import PreProcess
import logging
from tartare.http_exceptions import InvalidArguments
from hashlib import md5
import uuid


#monkey patching of gridfs file for exposing the size in a "standard" way
def grid_out_len(self: GridOut) -> int:
    return self.length
GridOut.__len__ = grid_out_len


def upload_file(url: str, filename: str, file: Union[str, bytes, IOBase, GridOut]) -> Response:
    return requests.post(url, files={'file': file, 'filename': filename}, timeout=120)
    #TODO: fix interaction between toolbets and gridfs file


def configure_logger(app_config: dict):
    """
    initialize logging
    """
    if 'LOGGER' in app_config:
        logging.config.dictConfig(app_config['LOGGER'])
    else:  # Default is std out
        logging.basicConfig(level='INFO')


def make_celery(app: Flask) -> Celery:
    celery_app = celery.Celery(app.import_name,
                               broker=app.config['CELERY_BROKER_URL'])
    celery_app.conf.update(app.config)
    TaskBase = celery_app.Task

    class ContextTask(TaskBase):
        abstract = True

        def __init__(self):
            pass

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery_app.Task = ContextTask
    return celery_app


def _make_doted_key(*args: Mapping) -> Mapping:
    return '.'.join([e for e in args if e])


def to_doted_notation(data: Mapping, prefix: Optional[Any]=None) -> Mapping:
    result = {}
    for k, v in data.items():
        key = _make_doted_key(prefix, k)
        if isinstance(v, Mapping):
            result.update(to_doted_notation(v, key))
        elif isinstance(v, list):
            # if data is a list of scalars
            if all(isinstance(item, (int, float, str, bool)) for item in v):
                result[key] = v
            else:
                for lk, lv in enumerate(v):
                    list_key = _make_doted_key(key, str(lk))
                    result.update(to_doted_notation(lv, list_key))
        else:
            result[key] = v
    return result


def validate_preprocesses_or_raise(preprocesses: dict, instance: str):
    for p in preprocesses:
        PreProcess.get_preprocess_class(p.get('type'), instance)


def get_filename(url: str, data_source_id: str) -> str:
    filename = "gtfs-{data_source_id}.zip".format(data_source_id=data_source_id)
    if not url:
        return filename
    parse_url = url.split('/')
    tmp = parse_url[-1]
    if tmp.endswith(".zip"):
        return tmp
    return filename


def get_md5_content_file(file: Union[str, bytes, IOBase, GridOut]) -> str:
    hasher = md5()
    with open(file, "rb") as f:
        data = f.read()
        hasher.update(data)
        return hasher.hexdigest()


def setdefault_ids(collections):
    for c in collections:
        c.setdefault('id', str(uuid.uuid4()))
