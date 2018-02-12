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
import json
import logging
import tempfile
from collections import defaultdict
from functools import partial
from typing import Dict, List

from tartare.core import zip
from tartare.core.constants import DATA_FORMAT_DIRECTION_CONFIG
from tartare.core.context import Context
from tartare.core.models import PreProcess
from tartare.core.readers import CsvReader
from tartare.exceptions import IntegrityException
from tartare.processes.abstract_preprocess import AbstractContributorProcess
from tartare.processes.utils import preprocess_registry


@preprocess_registry()
class ComputeDirections(AbstractContributorProcess):
    direction_id_normal = '0'
    direction_id_return = '1'

    def __init__(self, context: Context, preprocess: PreProcess) -> None:
        super().__init__(context, preprocess)

    def __get_config_gridfs_id_from_context(self) -> str:
        links = self.params.get('links')
        data_source_config_context = self.context.get_data_source_context_in_links(links, DATA_FORMAT_DIRECTION_CONFIG)
        return data_source_config_context.gridfs_id

    def do(self) -> Context:
        self.check_expected_files(['stop_times.txt', 'trips.txt'])
        self.check_links([DATA_FORMAT_DIRECTION_CONFIG])
        config_gridfs_id = self.__get_config_gridfs_id_from_context()
        for data_source_id_to_process in self.data_source_ids:
            # following data_source_to_process_context cannot be None because of integrity checks
            # when creating contributor
            data_source_to_process_context = self.context.get_contributor_data_source_context(
                contributor_id=self.contributor_id,
                data_source_id=data_source_id_to_process)
            config = json.load(self.gfs.get_file_from_gridfs(config_gridfs_id))
            data_source_to_process_context.gridfs_id = self.__process_file_from_gridfs_id(
                data_source_to_process_context.gridfs_id, config)
        return self.context

    def __get_rules(self, trip_to_route: Dict[str, str], trip_stop_sequences: Dict[str, List[str]],
                    config: Dict[str, List[str]]) -> Dict[str, str]:
        trips_to_fix = {}
        for a_trip, a_stop_sequence in trip_stop_sequences.items():
            try:
                a_route = trip_to_route[a_trip]
                reference = config[a_route]

                new_reference = [item for item in reference if
                                 item in a_stop_sequence]  # reduce to keep only known stops
                if len(new_reference) < 2:
                    raise IntegrityException(
                        'unable to calculate direction_id for route {route_id}: not enough stops for trip {trip_id}'.
                            format(route_id=a_route, trip_id=a_trip))

                forward_sequence_count = 0
                sequence_count = len(new_reference) - 1
                # on boucle sur les couples d'arrêts consécutifs stop_id_a -> stop_id_b
                # et on vérifie s'ils sont dans le même ordre que dans la séquence de référence.
                for stop_idx in range(sequence_count):
                    stop_id_a = new_reference[stop_idx]
                    stop_id_b = new_reference[stop_idx + 1]
                    if a_stop_sequence.index(stop_id_b) > a_stop_sequence.index(stop_id_a):
                        forward_sequence_count += 1
                # si moins de la moitié des couples d'arrêts ne sont pas dans le bon sens, on passe en sens retour
                if forward_sequence_count < sequence_count / 2:
                    trips_to_fix[a_trip] = self.direction_id_return
                else:
                    trips_to_fix[a_trip] = self.direction_id_normal
            except IntegrityException as e:
                logging.getLogger(__name__).error(str(e))
        return trips_to_fix

    def __apply_rules(self, trips_reader: CsvReader, trips_file_name: str, trips_to_fix: Dict[str, str]) -> None:
        trips_reader.apply(column_name='direction_id', callback=lambda row, trips=trips_to_fix:
                           trips_to_fix[row['trip_id']] if row['trip_id'] in trips else row['direction_id'])
        trips_reader.save_as_csv(trips_file_name)

    def __get_stop_sequence_by_trip(self, trip_to_route: Dict[str, str]) -> Dict[str, List[str]]:
        trip_stop_sequences = defaultdict(list)  # type: Dict[str, List[str]]
        stop_times_reader = CsvReader()
        stop_times_reader.load_csv_data_from_zip_file(self.file_to_process, "stop_times.txt",
                                                      usecols=['trip_id', 'stop_id', 'stop_sequence'])
        # the sort_values fixes legacy assumption: "it assumes that stop_times comes in order"
        # https://github.com/CanalTP/navitiaio-updater/blob/master/scripts/fr-idf_OIF_fix_direction_id_tn.py#L13
        # it sorts stop_ids by stop_sequence for each trip
        trip_stop_sequences_with_weight = stop_times_reader.data[stop_times_reader.data['trip_id'] \
            .isin(trip_to_route)] \
            .sort_values(['trip_id', 'stop_sequence']) \
            .to_dict('records')
        for trip in trip_stop_sequences_with_weight:
            trip_stop_sequences[trip['trip_id']].append(trip['stop_id'])
        return trip_stop_sequences

    def do_compute_directions(self, trips_file_name: str, config: tuple) -> None:
        trips_reader = CsvReader()
        trips_reader.load_csv_data(trips_file_name, dtype={'direction_id': str}, keep_default_na=False, sep=',')

        trips_dict = trips_reader.data[trips_reader.data['route_id'].isin(config[1].keys())].to_dict('records')
        trip_to_route = {trip['trip_id']: trip['route_id'] for trip in trips_dict}
        trip_stop_sequences = self.__get_stop_sequence_by_trip(trip_to_route)
        rules = self.__get_rules(trip_to_route, trip_stop_sequences, config[1])
        self.__apply_rules(trips_reader, trips_file_name, rules)

    def __process_file_from_gridfs_id(self, gridfs_id_to_process: str, config: Dict[str, List[str]]) -> str:
        self.file_to_process = self.gfs.get_file_from_gridfs(gridfs_id_to_process)
        with tempfile.TemporaryDirectory() as tmp_dir_name, tempfile.TemporaryDirectory() as new_tmp_dir_name:
            gtfs_computed_path = zip.edit_file_in_zip_file(self.file_to_process, 'trips.txt', tmp_dir_name,
                                                           new_tmp_dir_name,
                                                           callback=partial(self.do_compute_directions,
                                                                            config=("compute-direction", config))
                                                           )

            return self.create_archive_and_replace_in_grid_fs(gridfs_id_to_process, gtfs_computed_path)
