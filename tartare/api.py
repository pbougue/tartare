# coding=utf-8

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

from tartare import app
from flask_restful import Api
from tartare.interfaces.status import Status
from tartare.interfaces.index import Index
from tartare.interfaces.coverages import Coverage
from tartare.interfaces.contributors import Contributor
from tartare.interfaces.grid_calendar import GridCalendar
from tartare.interfaces.data_update import DataUpdate, CoverageData
from tartare.interfaces.data_sources import DataSource
from tartare.interfaces.coverage_data_source_subscription import CoverageDataSourceSubscription
from tartare.interfaces.coverage_contributor_subscription import CoverageContributorSubscription
from tartare.interfaces.contributor_export import ContributorExport
from tartare.interfaces.jobs import Job
from tartare.interfaces.preprocess import PreProcess


api = Api(app)

api.app.url_map.strict_slashes = False
api.add_resource(Index, '/', endpoint='index')
api.add_resource(Status, '/status', endpoint='status')
api.add_resource(Coverage, '/coverages', '/coverages/', '/coverages/<string:coverage_id>', endpoint='coverages')
api.add_resource(GridCalendar, '/coverages/<string:coverage_id>/grid_calendar', endpoint='grid_calendar')
api.add_resource(DataUpdate, '/coverages/<string:coverage_id>/environments/<string:environment_type>/data_update',
                             endpoint='data_update')
api.add_resource(CoverageData, '/coverages/<string:coverage_id>/environments/<string:environment_type>/data/<string:data_type>',
                             endpoint='data')
api.add_resource(Contributor, '/contributors', '/contributors/', '/contributors/<string:contributor_id>', endpoint='contributors')
api.add_resource(DataSource, '/contributors/<string:contributor_id>/data_sources',
                 '/contributors/<string:contributor_id>/data_sources/<string:data_source_id>')
api.add_resource(PreProcess, '/contributors/<string:contributor_id>/preprocesses',
                 '/contributors/<string:contributor_id>/preprocesses/<string:preprocess_id>')
api.add_resource(CoverageDataSourceSubscription, '/coverages/<string:coverage_id>/data_sources',
                 '/coverages/<string:coverage_id>/data_sources/<string:data_source_id>')
api.add_resource(CoverageContributorSubscription, '/coverages/<string:coverage_id>/contributors',
                 '/coverages/<string:coverage_id>/contributors/<string:contributor_id>')
api.add_resource(ContributorExport, '/contributors/<string:contributor_id>/actions/export')
api.add_resource(Job, '/jobs', '/jobs/<string:job_id>', endpoint='jobs')
