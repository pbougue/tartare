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
import shutil
import tempfile
from zipfile import ZipFile

from tartare.core.context import Context, DataSourceExport
from tartare.core.gridfs_handler import GridFsHandler
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
        opcional_colums = ['agency_lang', 'agency_phone', 'agency_fare_url', 'agency_email']
        params = self.params.get("data", {})

        columns = [*default_data] + opcional_colums
        data = {**default_data, **file_data}
        data = {**data, **params}
        data = {k: data.get(k) for k in data if k in columns}

        return data

    def create_new_zip(self, file_data: dict, files_zip: ZipFile, tmp_dir_name: str, filename: str, zip_destination: str) -> str:
        new_data = self._get_agency_data(file_data)
        files_zip.extractall(tmp_dir_name)
        with open('{}/{}'.format(tmp_dir_name, 'agency.txt'), 'w') as agency:
            writer = csv.DictWriter(agency, fieldnames=list(new_data.keys()))
            writer.writeheader()
            writer.writerow(new_data)
        new_zip = '{}/{}'.format(zip_destination, filename.split(".")[0])
        return shutil.make_archive(new_zip, 'zip', tmp_dir_name)

    def manage_agency_file(self, data_source_export: DataSourceExport) -> None:
        grid_out = GridFsHandler().get_file_from_gridfs(data_source_export.gridfs_id)
        filename = grid_out.filename
        data = get_content_file_from_grid_out_file(grid_out, 'agency.txt')

        if len(data) > 1:
            raise RuntimeException(self.format_error_message('agency.txt should not have more than 1 agency'))
        # there is no agency_id in the parameters nor in agency.txt
        if not self.params.get('data', {}).get('agency_id') and \
                (len(data) == 0 or len(data) == 1 and not data[0].get('agency_id')):
            raise RuntimeException(self.format_error_message('agency_id should be provided'))

        file_data = data[0] if data else {}

        with ZipFile(grid_out, 'r') as files_zip:
            with tempfile.TemporaryDirectory() as tmp_dir_name:
                with tempfile.TemporaryDirectory() as zip_destination:
                    new_zip = self.create_new_zip(file_data, files_zip, tmp_dir_name, grid_out.filename, zip_destination)
                    data_source_export.update_data_set_state(self.add_in_grid_fs(new_zip, filename))

    def do(self) -> Context:
        for data_source_id in self.data_source_ids:
            data_source_export = self.context.get_data_source_export_from_data_source(data_source_id)
            self.manage_agency_file(data_source_export)
        return self.context
