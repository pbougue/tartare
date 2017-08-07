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
import json
import logging
import os
import shutil
import tempfile
import zipfile
from collections import defaultdict
from typing import List, Dict, TextIO
from tartare.core.context import Context, DataSourceContext
from tartare.core.gridfs_handler import GridFsHandler
from tartare.core.models import PreProcess
from tartare.exceptions import ParameterException, IntegrityException
from tartare.processes.processes import AbstractProcess
import logging
from tartare.core.gridfs_handler import GridFsHandler
from zipfile import ZipFile
import csv
from tartare.helper import get_content_file_from_grid_out_file
import tempfile
import shutil
from typing import List
from tartare.exceptions import ParameterException


class Ruspell(AbstractProcess):
    def do(self) -> Context:
        return self.context


class ComputeDirections(AbstractProcess):

    valid_column_names = ['route_id', 'service_id', 'trip_id', 'trip_headsign', 'direction_id', 'block_id']

    def __init__(self, context: Context, preprocess: PreProcess) -> None:
        super().__init__(context, preprocess)
        self.gfs = GridFsHandler()

    def __get_config_gridfs_id_from_context(self, data_source_contexts: List[DataSourceContext]) -> str:
        if not self.params.get('config') or 'data_source_id' not in self.params.get('config'):
            raise ParameterException('data_source_id missing in preprocess config')

        data_source_id_config = self.params.get('config')['data_source_id']
        data_sources_config_context = [dsc for dsc in data_source_contexts if
                                       dsc.data_source_id == data_source_id_config]
        if not data_sources_config_context:
            raise ParameterException(
                'data_source_id "{data_source_id_config}" in preprocess config does not belong to contributor'.format(
                    data_source_id_config=data_source_id_config))
        data_source_config_context = data_sources_config_context[0]
        return data_source_config_context.gridfs_id

    def do(self) -> Context:
        contributor_context = self.context.contributor_contexts[0]
        data_source_contexts = self.context.get_contributor_data_source_contexts(
            contributor_context.contributor.id)
        config_gridfs_id = self.__get_config_gridfs_id_from_context(data_source_contexts)

        for data_source_id_to_process in self.data_source_ids:
            data_sources_to_process_context = [dsc for dsc in data_source_contexts if
                                               dsc.data_source_id == data_source_id_to_process]
            if not data_sources_to_process_context:
                raise ParameterException(
                    'data_source_id to preprocess "{data_source_id_to_process}" does not belong to contributor'.format(
                        data_source_id_to_process=data_source_id_to_process))
            data_source_to_process_context = data_sources_to_process_context[0]
            self.config = json.load(self.gfs.get_file_from_gridfs(config_gridfs_id))
            data_source_to_process_context.gridfs_id = self.__process_file_from_gridfs_id(
                data_source_to_process_context.gridfs_id)
        return self.context

    def __get_rules(self, trip_to_route: Dict[str, str], trip_stop_sequences: Dict[str, List[str]]) -> List[str]:
        trips_to_invert = []
        for a_trip, a_stop_sequence in trip_stop_sequences.items():
            try:
                a_route = trip_to_route[a_trip]
                reference = self.config[a_route]

                new_reference = [item for item in reference if
                                 item in a_stop_sequence]  # reduce to keep only known stops
                if len(new_reference) < 2:
                    raise IntegrityException(
                        'unable to calculate direction_id for route {route_id}: not enough stops for trip {trip_id}'.format(
                            route_id=a_route, trip_id=a_trip))

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
                    trips_to_invert.append(a_trip)
            except IntegrityException as e:
                logging.getLogger(__name__).error(str(e))
        return trips_to_invert

    def __apply_rules(self, trips_file_name: str, trips_file_read: TextIO, trips_to_invert: List[str]) -> None:
        with open(trips_file_name, 'w') as trips_file_write:
            trips_file_read.seek(0)
            reader = csv.DictReader(trips_file_read)
            writer = csv.DictWriter(trips_file_write, fieldnames=self.valid_column_names, delimiter=',',
                                    quoting=csv.QUOTE_MINIMAL)
            writer.writeheader()
            for row in reader:
                row['direction_id'] = '0' if row['trip_id'] in trips_to_invert else '1'
                writer.writerow(row)

    def __create_archive_and_replace_in_grid_fs(self, old_gridfs_id: str, tmp_dir_name: str,
                                                backup_files: List[str] = []) -> str:
        computed_file_name = 'gtfs-computed-directions'
        for backup_file in backup_files:
            os.remove(backup_file)
        with tempfile.TemporaryDirectory() as tmp_out_dir_name:
            new_archive_file_name = os.path.join(tmp_out_dir_name, 'gtfs-computed-directions')
            new_archive_file_name = shutil.make_archive(new_archive_file_name, 'zip', tmp_dir_name)
            with open(new_archive_file_name, 'rb') as new_archive_file:
                new_gridfs_id = self.gfs.save_file_in_gridfs(new_archive_file, filename=computed_file_name + '.zip')
                self.gfs.delete_file_from_gridfs(old_gridfs_id)
                return new_gridfs_id

    def __process_file_from_gridfs_id(self, gridfs_id_to_process: str) -> str:
        file_to_process = self.gfs.get_file_from_gridfs(gridfs_id_to_process)
        with zipfile.ZipFile(file_to_process, 'r') as files_zip:
            with tempfile.TemporaryDirectory() as tmp_dir_name:
                trips_file_name = os.path.join(tmp_dir_name, 'trips.txt')
                trips_backup_file = trips_file_name + '.bak'
                files_zip.extractall(tmp_dir_name)
                shutil.copyfile(trips_file_name, trips_backup_file)
                with open(trips_backup_file, 'r') as trips_file_read:
                    trip_to_route = {trip['trip_id']: trip['route_id'] for trip in csv.DictReader(trips_file_read) if
                                     trip['route_id'] in self.config.keys()}
                    with open(os.path.join(tmp_dir_name, 'stop_times.txt'), 'r') as stop_times_file:
                        trip_stop_sequences = defaultdict(list)  # type: dict
                        for stop_line in csv.DictReader(stop_times_file):
                            if stop_line['trip_id'] in trip_to_route:
                                trip_stop_sequences[stop_line['trip_id']].append(stop_line['stop_id'])

                        rules = self.__get_rules(trip_to_route, trip_stop_sequences)
                        self.__apply_rules(trips_file_name, trips_file_read, rules)

                return self.__create_archive_and_replace_in_grid_fs(gridfs_id_to_process, tmp_dir_name,
                                                                    [trips_backup_file])


class HeadsignShortName(AbstractProcess):
    def do(self) -> Context:
        return self.context


class GtfsAgencyFile(AbstractProcess):

    def _is_agency_dict_valid(self, data: List[dict]) -> bool:
        if not data:
            return False
        return any([(v in data[0].keys()) for v in ['agency_name', 'agency_url', 'agency_timezone']])

    def _get_agency_data(self) -> dict:
        # for more informations, see : https://developers.google.com/transit/gtfs/reference/agency-file
        agency_data = {
            "agency_id": '42',
            "agency_name": "",
            "agency_url": "",
            "agency_timezone": "",
            "agency_lang": "",
            "agency_phone": "",
            "agency_fare_url": "",
            "agency_email": ""
        }
        agency_data.update(self.params.get("data", {}))
        return agency_data

    def create_new_zip(self, files_zip: ZipFile, tmp_dir_name: str, filename: str) -> str:
        new_data = self._get_agency_data()
        files_zip.extractall(tmp_dir_name)
        with open('{}/{}'.format(tmp_dir_name, 'agency.txt'), 'a') as agency:
            writer = csv.DictWriter(agency, fieldnames=list(new_data.keys()))
            writer.writeheader()
            writer.writerow(new_data)
        new_zip = '{}/{}'.format(tmp_dir_name, filename.split(".")[0])
        shutil.make_archive(new_zip, 'zip', tmp_dir_name)
        return new_zip

    def manage_agency_file(self, data_source_context: DataSourceContext) -> None:
        grid_out = GridFsHandler().get_file_from_gridfs(data_source_context.gridfs_id)
        filename = grid_out.filename
        data = get_content_file_from_grid_out_file(grid_out, 'agency.txt')
        if not self._is_agency_dict_valid(data):
            logging.getLogger(__name__).debug('data source {}  without or empty agency.txt file'.
                                              format(data_source_context.data_source_id))
            with ZipFile(grid_out, 'r') as files_zip:
                with tempfile.TemporaryDirectory() as tmp_dir_name:
                    new_zip = self.create_new_zip(files_zip, tmp_dir_name, grid_out.filename)
                    with open('{}.{}'.format(new_zip, 'zip'), 'rb') as file:
                        old_gridfs_id = data_source_context.gridfs_id
                        data_source_context.gridfs_id = GridFsHandler().save_file_in_gridfs(file=file,
                                                                                            filename=filename)
                        GridFsHandler().delete_file_from_gridfs(old_gridfs_id)

    def do(self) -> Context:
        contributor = self.context.contributor_contexts[0].contributor
        for data_source_id in self.data_source_ids:
            data_source_context = self.context.get_contributor_data_source_context(contributor_id=contributor.id,
                                                                                   data_source_id=data_source_id)
            if not data_source_context:
                msg = 'impossible to build preprocess GtfsAgencyFile : ' \
                      'data source {} not exist for contributor {}'.format(data_source_id, contributor.id)
                logging.getLogger(__name__).warning(msg)
                raise ParameterException(msg)
            self.manage_agency_file(data_source_context)
        return self.context
