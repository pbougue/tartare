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
import logging

from tartare.core.models import Coverage, CoverageExport
from tartare.tasks import publish_data_on_platform
from tartare.decorators import publish_params_validate


class DataPublisher(flask_restful.Resource):
    @publish_params_validate()
    def post(self, coverage_id, environment_id):
        logging.getLogger(__name__).debug('trying to publish data: coverage {}, environment {}'.format(coverage_id,
                                                                                                       environment_id))
        coverage = Coverage.get(coverage_id)
        environment = coverage.get_environment(environment_id)
        gridfs_id = CoverageExport.get_last(coverage.id)[0].get('gridfs_id')
        for platform in environment.publication_platforms:
            publish_data_on_platform.delay(platform, gridfs_id, coverage, environment_id)
        return {'message': 'OK'}, 200