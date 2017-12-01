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
from tartare.interfaces.files import File
from tartare.interfaces.preprocesses import PreProcesses

api = Api(app)

api.app.url_map.strict_slashes = False

coverage = '/coverages'
coverage_and_id = coverage + '/<string:coverage_id>'

contributor = '/contributors'
contributor_and_id = contributor + '/<string:contributor_id>'
environment = "/environments"
environment_and_id = environment + "/<string:environment_id>"
environment_and_type = environment + "/<string:environment_type>"

export = '/exports'
export_and_id = export + '/<string:export_id>'


file_and_id = '/files/<string:file_id>'


api.add_resource(Index,
                 '/',
                 endpoint='index')

api.add_resource(Status,
                 '/status',
                 endpoint='status')

api.add_resource(File,
                 coverage_and_id + environment_and_id + file_and_id,
                 coverage_and_id + export_and_id + file_and_id,
                 contributor_and_id + export_and_id + file_and_id,
                 endpoint='files')

api.add_resource(Coverage,
                 coverage,
                 coverage_and_id,
                 endpoint='coverages')

api.add_resource(GridCalendar,
                 coverage_and_id + '/grid_calendar',
                 endpoint='grid_calendar')

api.add_resource(Contributor,
                 contributor,
                 contributor_and_id,
                 endpoint='contributors')

api.add_resource(DataSource,
                 contributor_and_id + '/data_sources',
                 contributor_and_id + '/data_sources/<string:data_source_id>')

api.add_resource(DataSourceFetch,
                 contributor_and_id + '/data_sources/<string:data_source_id>/actions/fetch')

api.add_resource(DataSet,
                 contributor_and_id + '/data_sources/<string:data_source_id>/data_sets')

api.add_resource(PreProcess,
                 contributor_and_id + '/preprocesses',
                 contributor_and_id + '/preprocesses/<string:preprocess_id>',
                 coverage_and_id + '/preprocesses',
                 coverage_and_id + '/preprocesses/<string:preprocess_id>')

api.add_resource(CoverageContributorSubscription,
                 coverage_and_id + contributor,
                 coverage_and_id + contributor_and_id)

api.add_resource(ContributorExportResource,
                 contributor_and_id + export,
                 contributor_and_id + export_and_id,
                 contributor_and_id + '/actions/export')

api.add_resource(AutomaticUpdateResource,
                 '/actions/automatic_update')

api.add_resource(Job,
                 '/jobs',
                 contributor_and_id + '/jobs',
                 contributor_and_id + '/jobs/<string:job_id>',
                 coverage_and_id + '/jobs',
                 coverage_and_id + '/jobs/<string:job_id>',
                 '/jobs/<string:job_id>',
                 endpoint='jobs')

api.add_resource(CoverageExportResource,
                 coverage_and_id + '/exports',
                 coverage_and_id + '/actions/export')

api.add_resource(PreProcesses, '/preprocesses')
