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
import datetime
import json
from typing import Any

from celery import Task, Celery
from celery.signals import setup_logging
from flask import Flask, jsonify, Response, request
from flask_pymongo import PyMongo
from flask_script import Manager
from werkzeug.exceptions import NotFound

from tartare.helper import configure_logger

app = Flask(__name__)  # type: Flask
app.config.from_object('tartare.default_settings')
app.config.from_envvar('TARTARE_CONFIG_FILE', silent=True)
manager = Manager(app)

configure_logger(app.config)

mongo = PyMongo(app)


@app.after_request
def after(response: Response) -> Response:
    if request.endpoint != 'requestlogs':
        req_data = {
            'url': request.url,
            'method': request.method,
            'headers': dict(request.headers),
        }
        if request.data:
            req_data['body'] = json.loads(request.data)

        resp_data = {
            'status_code': response.status_code,
            'headers': dict(response.headers),
        }

        if response.mimetype == 'application/json':
            resp_data['body'] = json.loads(response.get_data())

        log_data = {
            'date': datetime.datetime.utcnow(),
            'request': req_data,
            'response': resp_data,
        }

        mongo.db.logs.insert_one(log_data)

    return response


@app.errorhandler(404)
def page_not_found(e: NotFound) -> Response:
    return jsonify(code=e.code, message=e.description), e.code


@setup_logging.connect
def celery_setup_logging(*args: Any, **kwargs: Any) -> Any:
    # we don't want celery to mess with our logging configuration
    pass


class ContextTask(Task):
    abstract = True

    def __init__(self) -> None:
        pass

    def __call__(self, *args: list, **kwargs: dict) -> Any:
        with app.app_context():
            return Task.__call__(self, *args, **kwargs)


celery = Celery(app.import_name)
celery.conf.update(app.config)
celery.Task = ContextTask

from tartare import api

from tartare.core.mailer import Mailer

mailer = Mailer(app.config.get('MAILER'), app.config.get('PLATFORM'))
