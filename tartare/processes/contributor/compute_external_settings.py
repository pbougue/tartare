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
import logging
import os
import tempfile
import zipfile

import shutil
from gridfs import GridOut

from tartare.core.constants import DATA_FORMAT_PT_EXTERNAL_SETTINGS
from tartare.core.context import Context
from tartare.core.models import PreProcess
from tartare.core.readers import CsvReader, JsonReader
from tartare.exceptions import ParameterException
from tartare.processes.abstract_preprocess import AbstractContributorProcess


class ComputeExternalSettings(AbstractContributorProcess):
    def __init__(self, context: Context, preprocess: PreProcess) -> None:
        super().__init__(context, preprocess)
        self.contributor_trigram = self.context.contributor_contexts[0].contributor.data_prefix if \
            self.context.contributor_contexts and self.context.contributor_contexts[0].contributor else None

    fieldnames_codes = ['object_system', 'object_type', 'object_id', 'object_code']
    fieldnames_properties = ['object_type', 'object_id', 'object_property_name', 'object_property_value']
    objects_codes_file_name = 'fusio_objects_codes.csv'
    objects_properties_file_name = 'fusio_object_properties.csv'
    siri_stif_object_system = 'SIRI_STIF'
    stop_extensions_object_code_column = 'ZDEr_ID_REF_A'

    def __write_row_for_codes(self, writer: csv.DictWriter, object_type: str, object_system: str, object_id: str,
                              object_code: str) -> None:
        writer.writerow({
            "object_type": object_type,
            "object_system": object_system,
            "object_id": object_id,
            "object_code": object_code
        })

    def __write_row_for_properties(self, writer: csv.DictWriter, object_type: str, object_property_name: str,
                                   object_property_value: str, object_id: str) -> None:
        writer.writerow({
            "object_type": object_type,
            "object_property_name": object_property_name,
            "object_property_value": object_property_value,
            "object_id": object_id
        })

    def __get_navitia_code_from_gtfs_stop_point(self, gtfs_stop_code: str) -> str:
        return "{}:SP:{}".format(self.contributor_trigram, gtfs_stop_code[10:])

    def __init_route_id_to_navitia_code_mapping(self, zip_file: GridOut) -> None:
        columns_used = ['route_id', 'agency_id']
        routes_reader = CsvReader()
        routes_reader.load_csv_data_from_zip_file(zip_file, "routes.txt", usecols=columns_used)

        route_id_to_navitia_code_list = routes_reader.get_mapping_from_columns(
            'route_id',
            lambda row, contrib_trigram=self.contributor_trigram:
            '{tri}:{rid}{tri}{aid}'.format(tri=contrib_trigram, rid=row['route_id'], aid=str(row['agency_id'])))
        self.route_id_to_navitia_code = {route_id: navitia_code for row in route_id_to_navitia_code_list for
                                         route_id, navitia_code in row.items()}

    def __create_rules_deactivate_realtime_for_routes_from_gtfs(self, tmp_dir_name: str,
                                                                writer_properties: csv.DictWriter) -> None:
        routes_file_name = os.path.join(tmp_dir_name, "routes.txt")
        routes_reader = CsvReader()
        routes_reader.load_csv_data(routes_file_name, usecols=['route_id'])
        for route_id in routes_reader.data.to_dict('list')['route_id']:
            # On vérifie que c'est bien une ligne de substitution créée par Fusio sur le réseau Transilien
            if route_id.split(":")[-1].lower() == "bus" and route_id.split(":")[0] in ["800", "810"]:
                route_id = "{}:{}".format(self.contributor_trigram, route_id)
                for rid in [route_id, route_id + "_R"]:
                    self.__write_row_for_properties(writer_properties, "route", "realtime_deactivation", "True", rid)

    def __create_rules_from_stop_extensions(self, tmp_dir_name: str, writer_codes: csv.DictWriter) -> None:
        stop_extensions_file_name = os.path.join(tmp_dir_name, "stop_extensions.txt")
        stop_extensions_reader = CsvReader()
        stop_extensions_reader.load_csv_data(stop_extensions_file_name)
        for row in stop_extensions_reader.data.to_dict('records'):
            object_id = self.__get_navitia_code_from_gtfs_stop_point(row['stop_id'])
            self.__write_row_for_codes(writer_codes, "stop_point", self.stop_extensions_object_code_column, object_id,
                                       row[self.stop_extensions_object_code_column])
            self.__write_row_for_codes(writer_codes, "stop_point", self.siri_stif_object_system, object_id,
                                       'STIF:StopPoint:Q:{}:'.format(row[self.stop_extensions_object_code_column]))

    def __create_rules_from_codif_ligne(self, writer_codes: csv.DictWriter) -> None:
        lines_referential_data_source_context = self.context.get_contributor_data_source_context(
            self.contributor_id, self.params['links'].get('lines_referential'))
        reader = JsonReader()
        reader.load_json_data_from_io(
            self.gfs.get_file_from_gridfs(lines_referential_data_source_context.gridfs_id),
            ['fields.externalcode_line', 'fields.id_line'])
        nb_lines_not_in_gtfs = 0
        for row in reader.data.to_dict('records'):
            object_id = self.route_id_to_navitia_code.get(row['fields.externalcode_line'])
            if not object_id:
                object_id = 'line not found'
                nb_lines_not_in_gtfs += 1
            self.__write_row_for_codes(writer_codes, "line", self.siri_stif_object_system, object_id,
                                       row['fields.id_line'])
        if nb_lines_not_in_gtfs:
            logging.getLogger(__name__).warning(
                '{nb} lines in Codifligne are not in the GTFS'.format(nb=nb_lines_not_in_gtfs))

    def __create_rules_from_tr_perimeter(self, writer_codes: csv.DictWriter, writer_properties: csv.DictWriter) -> None:
        tr_perimeter_data_source_context = self.context.get_contributor_data_source_context(
            self.contributor_id, self.params['links'].get('tr_perimeter'))
        reader = JsonReader()
        reader.load_json_data_from_io(self.gfs.get_file_from_gridfs(tr_perimeter_data_source_context.gridfs_id),
                                      ['fields.codifligne_line_externalcode', 'fields.lineref'])
        for row in reader.data.to_dict('records'):
            object_id = self.route_id_to_navitia_code.get(row['fields.codifligne_line_externalcode'], 'line not found')
            self.__write_row_for_codes(writer_codes, "line", self.siri_stif_object_system, object_id,
                                       row['fields.lineref'])
            self.__write_row_for_properties(writer_properties, "line", "realtime_system", self.siri_stif_object_system,
                                            object_id)

    def __save_csv_files_as_data_set(self, tmp_csv_workspace: str) -> str:
        with tempfile.TemporaryDirectory() as tmp_out_dir_name:
            new_archive_file_name = os.path.join(tmp_out_dir_name, DATA_FORMAT_PT_EXTERNAL_SETTINGS)
            new_archive_file_name = shutil.make_archive(new_archive_file_name, 'zip', tmp_csv_workspace)
            with open(new_archive_file_name, 'rb') as new_archive_file:
                new_gridfs_id = self.gfs.save_file_in_gridfs(new_archive_file, filename=DATA_FORMAT_PT_EXTERNAL_SETTINGS + '.zip')
                return new_gridfs_id

    def __process_file_from_gridfs_id(self, gridfs_id_to_process: str) -> str:
        file_to_process = self.gfs.get_file_from_gridfs(gridfs_id_to_process)
        self.__init_route_id_to_navitia_code_mapping(file_to_process)
        with zipfile.ZipFile(file_to_process, 'r') as files_zip, \
                tempfile.TemporaryDirectory() as tmp_dir_name, \
                tempfile.TemporaryDirectory() as tmp_csv_workspace:
            files_zip.extractall(tmp_dir_name)
            csv_codes = os.path.join(tmp_csv_workspace, self.objects_codes_file_name)
            csv_properties = os.path.join(tmp_csv_workspace, self.objects_properties_file_name)
            with open(csv_codes, 'w') as rules_csv_codes_file, \
                    open(csv_properties, 'w') as rules_csv_properties_file:
                writer_codes = csv.DictWriter(rules_csv_codes_file, fieldnames=self.fieldnames_codes)
                writer_codes.writeheader()
                writer_properties = csv.DictWriter(rules_csv_properties_file, fieldnames=self.fieldnames_properties)
                writer_properties.writeheader()
                self.__create_rules_from_tr_perimeter(writer_codes, writer_properties)
                self.__create_rules_from_codif_ligne(writer_codes)
                self.__create_rules_from_stop_extensions(tmp_dir_name, writer_codes)
                self.__create_rules_deactivate_realtime_for_routes_from_gtfs(tmp_dir_name, writer_properties)

            return self.__save_csv_files_as_data_set(tmp_csv_workspace)

    def __check_config(self) -> None:
        if 'target_data_source_id' not in self.params or not self.params['target_data_source_id']:
            raise ParameterException('target_data_source_id missing in preprocess config')
        links_to_check = ['tr_perimeter', 'lines_referential']

        for param in links_to_check:
            data_source_id = self.get_link(param)
            data_source_config_context = self.context.get_contributor_data_source_context(self.contributor_id,
                                                                                          data_source_id)
            if not data_source_config_context:
                raise ParameterException(
                    'link {data_source_id} is not a data_source id present in contributor'.format(
                        data_source_id=data_source_id))
        if not self.context.get_contributor_data_source_context(self.contributor_id,
                                                                self.params['target_data_source_id']):
            raise ParameterException('target_data_source_id "{}" is not a data_source id present in contributor'.format(
                self.params['target_data_source_id']))

    def do(self) -> Context:
        self.__check_config()
        for data_source_id_to_process in self.data_source_ids:
            data_source_to_process_context = self.context.get_contributor_data_source_context(
                contributor_id=self.contributor_id,
                data_source_id=data_source_id_to_process)
            target_data_set_gridfs_id = self.__process_file_from_gridfs_id(data_source_to_process_context.gridfs_id)
            data_source_target_context = self.context.get_contributor_data_source_context(
                contributor_id=self.contributor_id,
                data_source_id=self.params['target_data_source_id'])
            data_source_target_context.gridfs_id = target_data_set_gridfs_id

        return self.context
