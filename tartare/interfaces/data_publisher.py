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

import flask_restful
from tartare.core.models import Coverage, CoverageExport
from tartare.exceptions import ObjectNotFound
import logging
from tartare.tasks import publish_data
from functools import wraps


class is_publish(object):
    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
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


class DataPublisher(flask_restful.Resource):
    @is_publish()
    def post(self, coverage_id, environment_id):
        logging.getLogger(__name__).debug('trying to publish data: coverage {}, environment')
        publish_data.delay(coverage_id, environment_id)
        return {'message': 'OK'}, 200
