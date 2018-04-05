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

from tartare.core.constants import DATA_FORMAT_GTFS
from tartare.core.context import Context
from tartare.core.fetcher import HttpFetcher
from tartare.core.gridfs_handler import GridFsHandler
from tartare.exceptions import FusioException
from tartare.processes.abstract_preprocess import AbstractFusioProcess
from tartare.processes.utils import preprocess_registry
from tartare.processes.fusio import Fusio


@preprocess_registry('coverage')
class FusioExport(AbstractFusioProcess):
    def get_export_type(self) -> int:
        export_type = self.params.get('export_type', "ntfs")
        map_export_type = {
            "ntfs": 32,
            "gtfsv2": 36,
            "googletransit": 37
        }
        lower_export_type = export_type.lower()
        if lower_export_type not in map_export_type:
            msg = 'export_type {} not found'.format(lower_export_type)
            logging.getLogger(__name__).exception(msg)
            raise FusioException(msg)
        return map_export_type.get(lower_export_type)

    def save_export(self, url: str) -> Context:
        with tempfile.TemporaryDirectory() as tmp_dir_name:
            dest_full_file_name, expected_file_name = HttpFetcher().fetch(url, tmp_dir_name)
            with open(dest_full_file_name, 'rb') as file:
                self.context.global_gridfs_id = GridFsHandler().save_file_in_gridfs(file, filename=expected_file_name)
        return self.context

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

        # fusio hostname is replaced by the one configured in the preprocess
        # avoid to access to a private ip from outside
        new_export_url = Fusio.replace_url_hostname_from_url(export_url, self.fusio.url)

        return self.save_export(new_export_url)
