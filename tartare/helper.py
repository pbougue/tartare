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
from typing import Union, Any, Optional, List
import celery
from celery import Celery
from collections.abc import Mapping
import requests
from flask import Flask
from requests import Response
from gridfs.grid_file import GridOut
import logging
from hashlib import md5
import uuid
import urllib.request
from urllib.error import ContentTooShortError, HTTPError, URLError
import zipfile
import csv
from io import TextIOWrapper


# monkey patching of gridfs file for exposing the size in a "standard" way
def grid_out_len(self: GridOut) -> int:
    return self.length
GridOut.__len__ = grid_out_len


def upload_file(url: str, filename: str, file: Union[str, bytes, IOBase, GridOut]) -> Response:
    return requests.post(url, files={'file': file, 'filename': filename}, timeout=120)
    # TODO: fix interaction between toolbets and gridfs file


def configure_logger(app_config: dict) -> None:
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

        def __init__(self) -> None:
            pass

        def __call__(self, *args: list, **kwargs: dict) -> Any:
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery_app.Task = ContextTask
    return celery_app


def _make_doted_key(*args: Optional[str]) -> str:
    return '.'.join([e for e in args if e])


def to_doted_notation(data: Mapping, prefix: Optional[Any] = None) -> Mapping:
    result = {}  # type: dict
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


def get_filename(url: str, data_source_id: str) -> str:
    filename = "gtfs-{data_source_id}.zip".format(data_source_id=data_source_id)
    if not url:
        return filename
    parse_url = url.split('/')
    tmp = parse_url[-1]
    if tmp.endswith(".zip"):
        return tmp
    return filename


def get_md5_content_file(file: Union[str, bytes, int]) -> str:
    hasher = md5()
    with open(file, "rb") as f:
        data = f.read()
        hasher.update(data)
        return hasher.hexdigest()


def setdefault_ids(collections: List[dict]) -> None:
    for c in collections:
        c.setdefault('id', str(uuid.uuid4()))


def download_zip_file(url_file: str, dest: str) -> None:
    logger = logging.getLogger(__name__)
    try:
        urllib.request.urlretrieve(url_file, dest)
    except HTTPError as e:
        logger.error('error during download of file: {}'.format(str(e)))
        raise
    except ContentTooShortError:
        logger.error('downloaded file size was shorter than exepected for url {}'.format(url_file))
        raise
    except URLError as e:
        logger.error('error during download of file: {}'.format(str(e)))
        raise
    if not zipfile.is_zipfile(dest):
        raise Exception('downloaded file from url {} is not a zip file'.format(url_file))


def get_values_by_key(values: Union[List, dict], out: List[str], key: str='gridfs_id') -> None:
    my_list = values.items() if isinstance(values, dict) else enumerate(values)
    for k, v in my_list:
        if isinstance(v, dict) or isinstance(v, list):
            get_values_by_key(v, out, key)
        else:
            if k == key and v not in out:
                out.append(v)


def get_dict_from_zip(zip: zipfile.ZipFile, file_name: str) -> List[dict]:
    with zip.open(file_name) as file:
        return [l for l in csv.DictReader(TextIOWrapper(file, 'utf8'))]


def get_content_file_from_grid_out_file(zip_file: GridOut, filename: str) -> List[dict]:
    with zipfile.ZipFile(zip_file, 'r') as file:
        try:
            return get_dict_from_zip(file, filename)
        except KeyError as e:
            logging.getLogger(__name__).warning('impossible during download of file: {}'.format(str(e)))
            pass
        return []
