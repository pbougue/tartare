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
import csv
import os
import tempfile
from functools import partial

from tartare.core.context import Context
from tartare.core.gridfs_handler import GridFsHandler
from tartare.core.zip import edit_file_in_zip_file_and_pack
from tartare.exceptions import RuntimeException
from tartare.helper import get_content_file_from_grid_out_file
from tartare.processes.abstract_process import AbstractContributorProcess
from tartare.processes.utils import process_registry


@process_registry()
class GtfsAgencyFile(AbstractContributorProcess):
    def _get_agency_data(self, file_data: dict) -> dict:
        # for more informations, see : https://developers.google.com/transit/gtfs/reference/agency-file
        default_data = {
            "agency_id": '42',
            "agency_name": "",
            "agency_url": "https://www.navitia.io/",
            "agency_timezone": "Europe/Paris",
        }
        optional_columns = ['agency_lang', 'agency_phone', 'agency_fare_url', 'agency_email']
        params = self.params.get("data", {})

        columns = [*default_data] + optional_columns
        data = {**default_data, **file_data}
        data = {**data, **params}
        data = {k: data.get(k) for k in data if k in columns}

        return data

    def manage_agency_file(self, filename: str, file_data: dict) -> None:
        new_data = self._get_agency_data(file_data)
        with open(filename, 'w') as agency:
            writer = csv.DictWriter(agency, fieldnames=list(new_data.keys()))
            writer.writeheader()
            writer.writerow(new_data)

    def do(self) -> Context:
        data_source_id = self.data_source_ids[0]
        data_source_export = self.context.get_data_source_export_from_data_source(data_source_id)
        grid_out = GridFsHandler().get_file_from_gridfs(data_source_export.gridfs_id)

        data = get_content_file_from_grid_out_file(grid_out, 'agency.txt')

        if len(data) > 1:
            raise RuntimeException(self.format_error_message('agency.txt should not have more than 1 agency'))
        # there is no agency_id in the parameters nor in agency.txt
        if not self.params.get('data', {}).get('agency_id') and \
                (len(data) == 0 or len(data) == 1 and not data[0].get('agency_id')):
            raise RuntimeException(self.format_error_message('agency_id should be provided'))

        file_data = data[0] if data else {}

        with tempfile.TemporaryDirectory() as extract_zip_path, tempfile.TemporaryDirectory() as new_zip_path:
            gtfs_computed_path = edit_file_in_zip_file_and_pack(grid_out, 'agency.txt', extract_zip_path,
                                                                new_zip_path,
                                                                callback=partial(
                                                                    self.manage_agency_file,
                                                                    file_data=file_data)
                                                                )
            data_source_export.update_data_set_state(self.create_archive_and_add_in_grid_fs(
                gtfs_computed_path, computed_file_name=os.path.splitext(grid_out.filename)[0]))
        return self.context
