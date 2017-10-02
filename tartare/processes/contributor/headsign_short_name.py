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

from tartare.core.context import Context
from tartare.processes.abstract_preprocess import AbstractContributorProcess
from tartare.core.models import PreProcess
import logging
from tartare.exceptions import ParameterException
from tartare.core.gridfs_handler import GridFsHandler
import tempfile
from tartare.core.readers import CsvReader
from tartare.core import zip


class HeadsignShortName(AbstractContributorProcess):
    def __init__(self, context: Context, preprocess: PreProcess) -> None:
        super().__init__(context, preprocess)

    def manage_headsign_short_name(self, data_source_context):
        grid_out = GridFsHandler().get_file_from_gridfs(data_source_context.gridfs_id)
        reader = CsvReader()
        reader.load_csv_data_from_zip_file(grid_out,
                                           'routes.txt',
                                           usecols=["route_id", "route_type"],
                                           keep_default_na=False)
        map_route_modes = reader.data.groupby('route_id')['route_type'].apply(lambda x: x.iloc[0]).to_dict()

        with tempfile.TemporaryDirectory() as extract_zip_path, tempfile.TemporaryDirectory() as new_zip_path:
            gtfs_computed_path = zip.edit_file_in_zip_file(grid_out, 'trips.txt', extract_zip_path, new_zip_path,
                                                           self.do_manage_headsign_short_name, map_route_modes)
            data_source_context.gridfs_id = self.create_archive_and_replace_in_grid_fs(data_source_context.gridfs_id,
                                                                                       gtfs_computed_path,
                                                                                       computed_file_name=grid_out.filename)

    def get_trip_short_name(self, row, map_route_modes) -> str:
        # Metro
        if map_route_modes.get(row['route_id']) == 1:
            return ''
        # Train Ter
        if map_route_modes.get(row['route_id']) == 2 and row["route_id"].startswith("800:TER"):
            return row['trip_headsign']
        return row['trip_short_name']

    def do_manage_headsign_short_name(self, filename, map_route_modes):
        reader = CsvReader()
        reader.load_csv_data(filename, keep_default_na=False)

        reader.data['trip_short_name'] = reader.data.apply(lambda row: self.get_trip_short_name(row, map_route_modes),
                                                           axis=1)
        # For All modes
        reader.data['trip_headsign'] = ""
        reader.save_as_csv(filename)

    def do(self) -> Context:
        contributor = self.context.contributor_contexts[0].contributor
        for data_source_id in self.data_source_ids:
            data_source_context = self.context.get_contributor_data_source_context(contributor_id=contributor.id,
                                                                                   data_source_id=data_source_id)
            if not data_source_context:
                msg = 'impossible to build preprocess HeadsignShortName : ' \
                      'data source {} not exist for contributor {}'.format(data_source_id, contributor.id)
                logging.getLogger(__name__).warning(msg)
                raise ParameterException(msg)
            self.manage_headsign_short_name(data_source_context)
        return self.context
