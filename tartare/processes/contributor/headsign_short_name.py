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
from functools import partial

from tartare.core.context import Context
from tartare.processes.abstract_preprocess import AbstractContributorProcess
import logging
from tartare.exceptions import ParameterException
from tartare.core.gridfs_handler import GridFsHandler
import tempfile
from tartare.core.readers import CsvReader
from tartare.core import zip
from gridfs import GridOut
from pandas.core.series import Series
from tartare.processes.utils import preprocess_registry


@preprocess_registry()
class HeadsignShortName(AbstractContributorProcess):
    # For more informations, see : https://developers.google.com/transit/gtfs/reference/#routestxt => route_type
    METRO = 1
    RAIL = 2
    def get_trip_short_name(self, row: Series, map_route_modes: dict) -> str:

        # Metro
        if map_route_modes.get(row['route_id']) == self.METRO:
            return ''
        # Train Ter
        if map_route_modes.get(row['route_id']) == self.RAIL and row["route_id"].startswith("800:TER"):
            return row['trip_headsign']
        return row['trip_short_name']

    def get_map_route_modes(self, grid_out: GridOut) -> dict:
        reader = CsvReader()
        reader.load_csv_data_from_zip_file(grid_out,
                                           'routes.txt',
                                           usecols=["route_id", "route_type"],
                                           keep_default_na=False, low_memory=False)
        return reader.data.groupby('route_id')['route_type'].apply(lambda x: x.iloc[0]).to_dict()

    def do_manage_headsign_short_name(self, filename: str, map_route_modes: dict) -> None:
        reader = CsvReader()
        reader.load_csv_data(filename, keep_default_na=False, low_memory=False)

        reader.apply(column_name='trip_short_name',
                     callback=lambda row: self.get_trip_short_name(row, map_route_modes))
        # For All modes
        reader.apply(column_name='trip_headsign', callback=lambda _: '')
        reader.save_as_csv(filename)

    def do(self) -> Context:
        contributor = self.context.contributor_contexts[0].contributor
        for data_source_id in self.data_source_ids:
            data_source_context = self.context.get_contributor_data_source_context(contributor_id=contributor.id,
                                                                                   data_source_id=data_source_id)
            if not data_source_context:
                msg = 'impossible to build preprocess HeadsignShortName : ' \
                      'data source {} does not exist for contributor {}'.format(data_source_id, contributor.id)
                logging.getLogger(__name__).error(msg)
                raise ParameterException(msg)

            grid_out = GridFsHandler().get_file_from_gridfs(data_source_context.gridfs_id)
            map_route_modes = self.get_map_route_modes(grid_out)

            with tempfile.TemporaryDirectory() as extract_zip_path, tempfile.TemporaryDirectory() as new_zip_path:
                gtfs_computed_path = zip.edit_file_in_zip_file(grid_out, 'trips.txt', extract_zip_path, new_zip_path,
                                                               callback=partial(self.do_manage_headsign_short_name,
                                                                                map_route_modes=map_route_modes)
                                                               )
                data_source_context.gridfs_id = self.create_archive_and_replace_in_grid_fs(
                    data_source_context.gridfs_id, gtfs_computed_path, computed_file_name=grid_out.filename)
        return self.context
