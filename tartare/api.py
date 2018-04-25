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

from tartare.interfaces.automatic_update import AutomaticUpdateResource
from tartare.interfaces.data_source_fetch import DataSourceFetch
from tartare.interfaces.status import Status
from tartare.interfaces.index import Index
from tartare.interfaces.coverages import Coverage
from tartare.interfaces.contributors import Contributor
from tartare.interfaces.grid_calendar import GridCalendar
from tartare.interfaces.data_sources import DataSource
from tartare.interfaces.data_set import DataSet
from tartare.interfaces.coverage_contributor_subscription import CoverageContributorSubscription
from tartare.interfaces.contributor_export import ContributorExportResource
from tartare.interfaces.coverage_export import CoverageExportResource
from tartare.interfaces.jobs import Job
from tartare.interfaces.preprocess import PreProcess
from tartare.interfaces.files_download import FileDownload
from tartare.interfaces.preprocesses import PreProcesses

api = Api(app)

api.app.url_map.strict_slashes = False


api.add_resource(Index,
                 '/',
                 endpoint='index')

api.add_resource(Status,
                 '/status',
                 endpoint='status')

api.add_resource(FileDownload, '/files/<string:file_id>/download', endpoint='files')

api.add_resource(Coverage,
                 '/coverages',
                 '/coverages/<string:coverage_id>',
                 endpoint='coverages')

api.add_resource(GridCalendar,
                 '/coverages/<string:coverage_id>/grid_calendar',
                 endpoint='grid_calendar')

api.add_resource(Contributor,
                 '/contributors',
                 '/contributors/<string:contributor_id>',
                 endpoint='contributors')

api.add_resource(DataSource,
                 '/contributors/<string:contributor_id>/data_sources',
                 '/contributors/<string:contributor_id>/data_sources/<string:data_source_id>')

api.add_resource(DataSourceFetch,
                 '/contributors/<string:contributor_id>/data_sources/<string:data_source_id>/actions/fetch')

api.add_resource(DataSet,
                 '/contributors/<string:contributor_id>/data_sources/<string:data_source_id>/data_sets')

api.add_resource(PreProcess,
                 '/contributors/<string:contributor_id>/preprocesses',
                 '/contributors/<string:contributor_id>/preprocesses/<string:preprocess_id>',
                 '/coverages/<string:coverage_id>/preprocesses',
                 '/coverages/<string:coverage_id>/preprocesses/<string:preprocess_id>')

api.add_resource(CoverageContributorSubscription,
                 '/coverages/<string:coverage_id>/contributors',
                 '/coverages/<string:coverage_id>/contributors/<string:contributor_id>')

api.add_resource(ContributorExportResource,
                 '/contributors/<string:contributor_id>/exports',
                 '/contributors/<string:contributor_id>/exports/<string:export_id>',
                 '/contributors/<string:contributor_id>/actions/export')

api.add_resource(AutomaticUpdateResource,
                 '/actions/automatic_update')

api.add_resource(Job,
                 '/jobs',
                 '/contributors/<string:contributor_id>/jobs',
                 '/contributors/<string:contributor_id>/jobs/<string:job_id>',
                 '/coverages/<string:coverage_id>/jobs',
                 '/coverages/<string:coverage_id>/jobs/<string:job_id>',
                 '/jobs/<string:job_id>',
                 endpoint='jobs')

api.add_resource(CoverageExportResource,
                 '/coverages/<string:coverage_id>/exports',
                 '/coverages/<string:coverage_id>/actions/export')

api.add_resource(PreProcesses, '/preprocesses')
