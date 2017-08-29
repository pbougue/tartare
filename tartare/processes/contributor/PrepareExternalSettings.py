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
from tartare.core.csv_reader import CsvReader
from tartare.exceptions import ParameterException
from tartare.processes.abstract_preprocess import AbstractContributorProcess


class PrepareExternalSettings(AbstractContributorProcess):
    def __get_navitia_code_from_gtfs_stop_point(self, gtfs_stop_code):
        return "{}:SP:{}".format(self.params.get('contributor_trigram'), gtfs_stop_code[10:])

    def __init_route_id_to_navitia_code_mapping(self, zip_file_name):
        routes_reader=CsvReader()
        routes_reader.load_csv_data_from_zip_file(zip_file_name, "routes.txt")
        self.route_id_to_navitia_code = routes_reader.get_mapping_from_columns(
            'route_id',
            lambda row, contrib_trigram=self.params.get('contributor_trigram'):
            '{tri}:{rid}{tri}{aid}'.format(tri=contrib_trigram, rid=row['route_id'], aid=str(row['agency_id'])),
            ['route_id', 'agency_id'])

    def __process_file_from_gridfs_id(self, gridfs_id_to_process: str) -> str:
        file_to_process = self.gfs.get_file_from_gridfs(gridfs_id_to_process)
        self.__init_route_id_to_navitia_code_mapping(file_to_process)

        # return self.__create_archive_and_replace_in_grid_fs(gridfs_id_to_process, tmp_dir_name,
        #                                                     [trips_backup_file])

    def __check_config(self):
        if 'contributor_trigram' not in self.params:
            raise ParameterException('contributor_trigram missing in preprocess config')
        to_check = ['tr_perimeter', 'lines_referential']
        if 'links' not in self.params:
            raise ParameterException('links missing in preprocess config')
        for param in to_check:
            if not self.params['links'].get(param):
                raise ParameterException('link {param} missing in preprocess config'.format(param=param))
        for param in to_check:
            data_source_id = self.params['links'].get(param)
            data_source_config_context = self.context.get_contributor_data_source_context(self.contributor_id,
                                                                                          data_source_id)
            if not data_source_config_context:
                raise ParameterException(
                    'link {data_source_id} is not a data_source id present in contributor'.format(
                        data_source_id=data_source_id))

    def do(self) -> Context:
        self.__check_config()
        for data_source_id_to_process in self.data_source_ids:
            data_source_to_process_context = self.context.get_contributor_data_source_context(
                contributor_id=self.contributor_id,
                data_source_id=data_source_id_to_process)
            data_source_to_process_context.gridfs_id = self.__process_file_from_gridfs_id(
                data_source_to_process_context.gridfs_id)

        return self.context
