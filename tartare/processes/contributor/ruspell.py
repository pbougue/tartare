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
import shutil
import tempfile
from functools import partial

from tartare.core import zip
from tartare.core.constants import DATA_FORMAT_BY_DATA_TYPE, DATA_TYPE_GEOGRAPHIC
from tartare.core.context import Context
from tartare.core.models import DataSource
from tartare.core.models import PreProcess
from tartare.core.subprocess_wrapper import SubProcessWrapper
from tartare.exceptions import ParameterException, RuntimeException
from tartare.processes.abstract_preprocess import AbstractContributorProcess
from tartare.processes.utils import preprocess_registry

logger = logging.getLogger(__name__)


@preprocess_registry()
class Ruspell(AbstractContributorProcess):
    stops_filename = 'stops.txt'
    stops_output_filename = 'stops_output.txt'
    rules_filename = 'rules.csv'
    command_pattern = '{binary_path} -c {config} -i {input} -o {output}'

    def __init__(self, context: Context, preprocess: PreProcess) -> None:
        super().__init__(context, preprocess)
        # Default binary path in docker worker-ruspell
        self._binary_path = self.params.get('_binary_path', '/usr/src/app/bin/ruspell')

    def __get_gridfs_id_from_data_source_context(self, data_source_id: str, contributor_id: str) -> str:
        data_source_config_context = self.context.get_contributor_data_source_context(contributor_id,
                                                                                      data_source_id)
        if not data_source_config_context:
            msg = 'contributor "{}" has not been exported'.format(contributor_id)
            raise RuntimeException(self.format_error_message(msg))
        return data_source_config_context.gridfs_id

    def __extract_data_sources_from_gridfs(self, data_format: str, path: str) -> str:
        links = self.params.get("links")
        if not links:
            raise ParameterException('links missing in preprocess')
        for contrib_ds in links:
            contributor_id = contrib_ds.get('contributor_id')
            data_source_id = contrib_ds.get('data_source_id')
            try:
                data_source = DataSource.get_one(contributor_id, data_source_id)
                if data_source.data_format != data_format:
                    continue
                gridfs_id = self.__get_gridfs_id_from_data_source_context(data_source_id, contributor_id)
                gridout = self.gfs.get_file_from_gridfs(gridfs_id)
                file_path = os.path.join(path, gridout.filename)
                with open(file_path, 'wb+') as f:
                    f.write(gridout.read())
            except ValueError:
                msg = 'data_source_id "{}" and/or contributor "{}" unknown or not correctly linked'.format(data_source_id,
                                                                                                           contributor_id)
                raise ParameterException(self.format_error_message(msg))
        return file_path

    def do_ruspell(self, file_path: str, stops_output_path: str, config_path: str) -> None:
        command = self.command_pattern.format(binary_path=self._binary_path,
                                              config=config_path,
                                              input=file_path,
                                              output=stops_output_path)
        subprocess_wrapper = SubProcessWrapper('ruspell')
        subprocess_wrapper.run_cmd(command)

        shutil.copy(stops_output_path, file_path)

    def do(self) -> Context:
        self.check_expected_files(['stops.txt'])
        with tempfile.TemporaryDirectory() as extract_dir_path, tempfile.TemporaryDirectory() as ruspell_dir_path:
            stops_output_path = os.path.join(ruspell_dir_path, self.stops_output_filename)
            from tartare.core.constants import DATA_FORMAT_BANO_FILE, DATA_FORMAT_RUSPELL_CONFIG
            # Get config
            config_path = self.__extract_data_sources_from_gridfs(DATA_FORMAT_RUSPELL_CONFIG, ruspell_dir_path)

            # Get Banos
            self.__extract_data_sources_from_gridfs(DATA_FORMAT_BANO_FILE, ruspell_dir_path)

            for data_source_id_to_process in self.data_source_ids:
                data_source_to_process_context = self.context.get_contributor_data_source_context(
                    contributor_id=self.contributor_id,
                    data_source_id=data_source_id_to_process)

                data_source_gridout = self.gfs.get_file_from_gridfs(data_source_to_process_context.gridfs_id)
                gtfs_computed_path = zip.edit_file_in_zip_file(data_source_gridout,
                                                               self.stops_filename,
                                                               extract_dir_path,
                                                               ruspell_dir_path,
                                                               callback=partial(self.do_ruspell,
                                                                                stops_output_path=stops_output_path,
                                                                                config_path=config_path)
                                                               )

                data_source_to_process_context.gridfs_id = self.create_archive_and_replace_in_grid_fs(
                    old_gridfs_id=data_source_to_process_context.gridfs_id,
                    files=gtfs_computed_path,
                    computed_file_name=os.path.basename(gtfs_computed_path))

        return self.context
