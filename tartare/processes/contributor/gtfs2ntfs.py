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
from tartare.core.context import Context
from tartare.core.models import DataSource
from tartare.core.models import PreProcess
from tartare.core.subprocess_wrapper import SubProcessWrapper
from tartare.exceptions import ParameterException, RuntimeException
from tartare.processes.abstract_preprocess import AbstractContributorProcess
from tartare.processes.utils import preprocess_registry

logger = logging.getLogger(__name__)


@preprocess_registry()
class Gtfs2Ntfs(AbstractContributorProcess):
    stops_filename = 'stops.txt'
    config_filename = 'config.json'
    command_pattern = '{binary_path} -c {config} -i {input} -o {output}'

    def __init__(self, context: Context, preprocess: PreProcess) -> None:
        super().__init__(context, preprocess)
        # Default binary path in docker worker-gtfs2ntfs
        self._binary_path = self.params.get('_binary_path', '/usr/src/app/bin/gtfs2ntfs')
        self.contributor = self.context.contributor_contexts[0].contributor

    def do_gtfs2ntfs(self, config_path: str, input_dir: str, output_dir: str) -> str:
        command = self.command_pattern.format(binary_path=self._binary_path,
                                              config=config_path,
                                              input=input_dir,
                                              output=output_dir)
        subprocess_wrapper = SubProcessWrapper('gtfs2ntfs')
        subprocess_wrapper.run_cmd(command)

    def __create_config(self, config_dir_path: str, data_source_id: str) -> str:
        data_source_to_process = self.contributor.get_data_source(data_source_id)

        # Create config file
        config = {
            'contributor': {
                'contributor_id': self.contributor.id,
                'contributor_name': self.contributor.name,
                'contributor_license': data_source_to_process.license.name,
                'contributor_website': data_source_to_process.license.url,
            },
            'dataset': {
                'dataset_id': data_source_to_process.id,
            }
        }

        config_file_path = os.path.join(config_dir_path, self.config_filename)

        import json
        with open(config_file_path, 'w') as f:
            json.dump(config, f)

        return config_file_path

    def do(self) -> Context:
        logger.info("GTFS 2 NTFS")

        # TODO: Check every files in a gtfs?
        with tempfile.TemporaryDirectory() as config_dir_path, \
                tempfile.TemporaryDirectory() as extract_dir_path, tempfile.TemporaryDirectory() as dst_dir_path:
            for data_source_id_to_process in self.data_source_ids:
                data_source_to_process_context = self.context.get_contributor_data_source_context(
                    contributor_id=self.contributor.id,
                    data_source_id=data_source_id_to_process)

                data_source_gridout = self.gfs.get_file_from_gridfs(data_source_to_process_context.gridfs_id)

                from zipfile import ZipFile
                with ZipFile(data_source_gridout, 'r') as files_zip:
                    files_zip.extractall(extract_dir_path)

                    self.do_gtfs2ntfs(self.__create_config(config_dir_path, data_source_id_to_process),
                                      extract_dir_path,
                                      dst_dir_path)

                    data_source_to_process_context.gridfs_id = self.create_archive_and_replace_in_grid_fs(
                        old_gridfs_id=data_source_to_process_context.gridfs_id,
                        files=dst_dir_path,
                        computed_file_name=data_source_id_to_process)

        return self.context
