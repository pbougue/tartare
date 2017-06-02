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
import celery
from collections.abc import Mapping
import requests
from gridfs.grid_file import GridOut
import tartare.processes
import logging
from tartare.exceptions import InvalidArguments


#monkey patching of gridfs file for exposing the size in a "standard" way
def grid_out_len(self):
    return self.length
GridOut.__len__ = grid_out_len


def upload_file(url, filename, file):
    return requests.post(url, files={'file': file}, timeout=120)
    #TODO: fix interaction between toolbets and gridfs file
    #form = encoder.MultipartEncoder({
    #    'file': (filename, file, 'application/octet-stream')
    #})
    #headers =  {'Content-Type': form.content_type}
    #return requests.post(url, headers=headers, data=form, timeout=10)


def configure_logger(app_config):
    """
    initialize logging
    """
    if 'LOGGER' in app_config:
        logging.config.dictConfig(app_config['LOGGER'])
    else:  # Default is std out
        logging.basicConfig(level='INFO')


def make_celery(app):
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


def _make_doted_key(*args):
    return '.'.join([e for e in args if e])


def to_doted_notation(data, prefix=None):
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


def validate_preprocesses_or_raise(preprocesses):
    for p in preprocesses:
        p_type = p.get('type')
        kls = getattr(tartare.processes, p_type, None)
        if kls is None:
            msg = 'Invalid process type {}'.format(p_type)
            logging.getLogger(__name__).error(msg)
            raise InvalidArguments(msg)
