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
import os

from tartare.core.context import Context
from tartare.core.models import PreProcess
from tartare.core.subprocess_wrapper import SubProcessWrapper
from tartare.exceptions import ParameterException
import tempfile
from tartare.core import zip
from tartare.processes.abstract_preprocess import AbstractContributorProcess

logger = logging.getLogger(__name__)


class Ruspell(AbstractContributorProcess):
    stops_filename = 'stops.txt'
    rules_filename = 'rules.csv'
    command_pattern = '{binary_path} -c {config} -i {input} -o {output} -r {rules}'

    def __init__(self, context: Context, preprocess: PreProcess) -> None:
        super().__init__(context, preprocess)
        # Default binary path in docker worker-ruspell
        self._binary_path = self.params.get('_binary_path', '/usr/src/app/bin/ruspell')

    def __get_gridfs_id_from_data_source_context(self, data_source_id: str) -> str:
        data_source_config_context = self.context.get_contributor_data_source_context(self.contributor_id,
                                                                                      data_source_id)
        if not data_source_config_context:
            raise ParameterException(
                'data_source_id "{data_source_id}" in preprocess links does not belong to contributor'.format(
                    data_source_id=data_source_id))
        return data_source_config_context.gridfs_id

    def __extract_data_source_from_gridfs(self, data_source_id: str, path: str) -> str:
        gridfs_id = self.__get_gridfs_id_from_data_source_context(data_source_id)
        gridout = self.gfs.get_file_from_gridfs(gridfs_id)
        file_path = os.path.join(path, gridout.filename)
        with open(file_path, 'wb+') as f:
            f.write(gridout.read())

        return file_path

    def do_ruspell(self, data_source_path: str, output_path: str, rules_path: str, config_path: str) -> None:
        command = self.command_pattern.format(binary_path=self._binary_path,
                                              config=config_path,
                                              input=data_source_path,
                                              output=output_path,
                                              rules=rules_path)
        subprocess_wrapper = SubProcessWrapper('ruspell')
        subprocess_wrapper.run_cmd(command)

    def do(self) -> Context:
        with tempfile.TemporaryDirectory() as extract_dir_name, tempfile.TemporaryDirectory() as ruspell_dir_name:
            # Get config
            config_path = self.__extract_data_source_from_gridfs(self.get_link('config'), ruspell_dir_name)

            # Get Banos
            for data_source_id in self.get_link('bano'):
                self.__extract_data_source_from_gridfs(data_source_id, ruspell_dir_name)

            for data_source_id_to_process in self.data_source_ids:
                data_source_to_process_context = self.context.get_contributor_data_source_context(
                    contributor_id=self.contributor_id,
                    data_source_id=data_source_id_to_process)

                data_source_gridout = self.gfs.get_file_from_gridfs(data_source_to_process_context.gridfs_id)

                output_path = os.path.join(extract_dir_name, self.stops_filename)
                rules_path = os.path.join(ruspell_dir_name, self.rules_filename)

                gtfs_computed_path = zip.edit_file_in_zip_file(data_source_gridout,
                                                               self.stops_filename,
                                                               extract_dir_name,
                                                               ruspell_dir_name,
                                                               self.do_ruspell,
                                                               output_path,
                                                               rules_path,
                                                               config_path)

                data_source_to_process_context.gridfs_id = self.create_archive_and_replace_in_grid_fs(
                    old_gridfs_id=data_source_to_process_context.gridfs_id,
                    files=gtfs_computed_path,
                    computed_file_name=os.path.basename(gtfs_computed_path))

        return self.context
