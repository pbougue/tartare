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
import logging
import tempfile

import requests

from tartare.core.constants import DATA_FORMAT_GTFS, DATA_FORMAT_NTFS, DATA_FORMAT_GOOGLE_TRANSIT
from tartare.core.context import Context, CoverageExportContext
from tartare.core.fetcher import HttpFetcher
from tartare.core.gridfs_handler import GridFsHandler
from tartare.core.models import OldProcess
from tartare.core.validity_period_finder import ValidityPeriodFinder
from tartare.exceptions import FusioException, ParameterException
from tartare.processes.abstract_process import AbstractFusioProcess
from tartare.processes.fusio import Fusio
from tartare.processes.utils import process_registry


@process_registry('coverage')
class FusioExport(AbstractFusioProcess):
    def __init__(self, context: CoverageExportContext, process: OldProcess) -> None:
        super().__init__(context, process)
        self.export_type = self.params.get('export_type')

    def get_export_type(self) -> int:
        map_export_type = {
            DATA_FORMAT_NTFS: 32,
            DATA_FORMAT_GTFS: 36,
            DATA_FORMAT_GOOGLE_TRANSIT: 37
        }
        if not self.params.get('export_type'):
            raise ParameterException(
                'export_type mandatory in process {} parameters (possible values: {})'.format(
                    self.process_id, ','.join(map_export_type.keys())
                ))

        if self.export_type not in map_export_type:
            msg = 'export_type {} is not handled by process FusioExport, possible values: {})'.format(
                self.export_type, ','.join(map_export_type.keys())
            )
            logging.getLogger(__name__).exception(msg)
            raise FusioException(msg)
        return map_export_type.get(self.export_type)

    def save_export(self, url: str) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir_name:
            dest_full_file_name, expected_file_name = HttpFetcher().fetch(url, tmp_dir_name)
            with open(dest_full_file_name, 'rb') as file:
                gridfs_id = GridFsHandler().save_file_in_gridfs(file, filename=expected_file_name)
                if self.params.get('target_data_source_id'):
                    validity_period = ValidityPeriodFinder.select_computer_and_find(dest_full_file_name,
                                                                                    self.export_type)
                    self.save_result_into_target_data_source(self.context.coverage, gridfs_id, validity_period)
            if self.export_type == DATA_FORMAT_NTFS:
                self.context.global_gridfs_id = gridfs_id

    def do(self) -> Context:
        data = {
            'action': 'Export',
            'ExportType': self.get_export_type(),
            'Source': 4
        }
        resp = self.fusio.call(requests.post, api='api', data=data)
        action_id = self.fusio.get_action_id(resp.content)
        self.fusio.wait_for_action_terminated(action_id)

        export_url = self.fusio.get_export_url(action_id)

        # fusio hostname is replaced by the one configured in the process
        # avoid to access to a private ip from outside
        new_export_url = Fusio.replace_url_hostname_from_url(export_url, self.fusio.url)

        self.save_export(new_export_url)
        return self.context
