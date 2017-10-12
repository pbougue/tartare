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

import requests

from tartare.core.constants import DATA_FORMAT_GTFS
from tartare.core.context import Context, DataSourceContext
from tartare.core.gridfs_handler import GridFsHandler
from tartare.core.models import Contributor, DataSource, CoverageExport
from tartare.processes.abstract_preprocess import AbstractFusioProcess
from tartare.processes.fusio import Fusio
from tartare.processes.utils import preprocess_registry


@preprocess_registry('coverage')
class FusioDataUpdate(AbstractFusioProcess):
    def __get_data(self, contributor: Contributor, data_source_context: DataSourceContext) -> dict:
        validity_period = data_source_context.validity_period
        return {
            'action': 'dataupdate',
            'contributorexternalcode': contributor.data_prefix,
            'isadapted': 0,
            'dutype': 'update',
            'serviceexternalcode': data_source_context.data_source_id,
            'libelle': 'unlibelle',
            'DateDebut': Fusio.format_date(validity_period.start_date),
            'DateFin': Fusio.format_date(validity_period.end_date),
            'content-type': 'multipart/form-data',
        }

    def __is_update_needed(self, contributor_id: str, data_source_context: DataSourceContext) -> bool:
        coverage_export = CoverageExport.get_last(self.context.coverage.id)
        if not coverage_export:
            return True
        previous_coverage_contributor = next(
            (coverage_export_contributor for coverage_export_contributor in coverage_export.contributors if
             coverage_export_contributor.contributor_id == contributor_id), None)
        previous_contributor_data_source_grid_fs_id = next(
            (data_source.gridfs_id for data_source in previous_coverage_contributor.data_sources if
             data_source.data_source_id == data_source_context.data_source_id), None)
        previous_gtfs = GridFsHandler().get_file_from_gridfs(previous_contributor_data_source_grid_fs_id)
        current_gtfs = GridFsHandler().get_file_from_gridfs(data_source_context.gridfs_id)
        return previous_gtfs.md5 != current_gtfs.md5

    def do(self) -> Context:
        for contributor_context in self.context.contributor_contexts:
            for data_source_context in contributor_context.data_source_contexts:
                if not data_source_context.gridfs_id:
                    continue
                if not DataSource.is_type_data_format(data_source_context.data_source_id, DATA_FORMAT_GTFS):
                    continue
                if self.__is_update_needed(contributor_context.contributor.id, data_source_context):
                    resp = self.fusio.call(requests.post, api='api',
                                           data=self.__get_data(contributor_context.contributor, data_source_context),
                                           files=self.get_files_from_gridfs(data_source_context.gridfs_id))
                    self.fusio.wait_for_action_terminated(self.fusio.get_action_id(resp.content))
        return self.context
