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
import zipfile
from abc import ABCMeta, abstractmethod
from typing import Any, List, Union, Optional
from zipfile import is_zipfile

from tartare.core.context import Context, ContributorExportContext, CoverageExportContext
from tartare.core.gridfs_handler import GridFsHandler
from tartare.core.models import DataSource, Contributor, Coverage, DataSet, ValidityPeriod, NewProcess, \
    OldProcess
from tartare.exceptions import ParameterException, RuntimeException, IntegrityException
from tartare.processes.fusio import Fusio


class AbstractProcess(metaclass=ABCMeta):
    def __init__(self, process: OldProcess) -> None:
        self.params = process.params if process else {}  # type: dict
        self.data_source_ids = process.data_source_ids
        self.process_id = process.id

    def save_result_into_target_data_source(self, data_source_owner: Union[Contributor, Coverage],
                                            target_data_set_gridfs_id: str,
                                            validity_period: Optional[ValidityPeriod] = None) -> None:
        data_source = data_source_owner.get_data_source(self.params['target_data_source_id'])
        data_set = DataSet(gridfs_id=target_data_set_gridfs_id, validity_period=validity_period)
        data_source.add_data_set_and_update_model(data_set, data_source_owner)

    @abstractmethod
    def do(self) -> Context:
        pass

    def format_error_message(self, msg: str) -> str:
        return '[process "{}"] {}'.format(self.process_id, msg)

    def get_link(self, key: str) -> Any:
        if not self.params.get('links') or key not in self.params.get('links'):
            raise ParameterException('{} missing in process links'.format(key))

        return self.params.get('links')[key]


class NewAbstractProcess(AbstractProcess, metaclass=ABCMeta):
    def __init__(self, process: NewProcess) -> None:
        self.process_id = process.id
        self.data_source_ids = process.input_data_source_ids
        self.params = {}


class AbstractFusioProcess(AbstractProcess, metaclass=ABCMeta):
    def __init__(self, context: CoverageExportContext, process: OldProcess) -> None:
        super().__init__(process)
        self.context = context
        if 'url' not in self.params:
            raise ParameterException('params.url not present in fusio process')
        self.fusio = Fusio(self.params['url'])

    @staticmethod
    def get_files_from_gridfs(gridfs_id: str) -> dict:
        return {"filename": GridFsHandler().get_file_from_gridfs(gridfs_id)}


class AbstractContributorProcess(AbstractProcess, metaclass=ABCMeta):
    def __init__(self, context: ContributorExportContext, process: OldProcess) -> None:
        super().__init__(process)
        self.context = context
        if self.context.contributor_contexts:
            self.contributor_id = self.context.contributor_contexts[0].contributor.id
        self.gfs = GridFsHandler()

    def check_expected_files(self, expected_files: List[str]) -> None:
        for data_source_id_to_process in self.data_source_ids:
            data_source_to_process_context = self.context.get_contributor_data_source_context(
                contributor_id=self.contributor_id,
                data_source_id=data_source_id_to_process)
            if not data_source_to_process_context:
                raise IntegrityException('data source to process {}.{} not found in contributor context'.format(
                    self.contributor_id, data_source_id_to_process
                ))
            data_source_gridout = self.gfs.get_file_from_gridfs(data_source_to_process_context.gridfs_id)
            with zipfile.ZipFile(data_source_gridout, 'r') as zip_file:
                if not set(expected_files).issubset(set(zip_file.namelist())):
                    raise RuntimeException('data source {dsid} does not contains required files {files}'.format(
                        dsid=data_source_id_to_process, files=', '.join(expected_files)
                    ))

    def replace_in_grid_fs(self, old_gridfs_id: str, zip_file: str, computed_file_name: str) -> str:
        new_gridfs_id = self.add_in_grid_fs(zip_file, computed_file_name)
        self.gfs.delete_file_from_gridfs(old_gridfs_id)
        return new_gridfs_id

    def add_in_grid_fs(self, zip_file: str, computed_file_name: str) -> str:
        with open(zip_file, 'rb') as new_archive_file:
            new_gridfs_id = self.gfs.save_file_in_gridfs(new_archive_file, filename=computed_file_name + '.zip')
            return new_gridfs_id

    def create_archive_and_replace_in_grid_fs(self, old_gridfs_id: str, files: str,
                                              computed_file_name: str = 'gtfs-processed') -> str:
        if is_zipfile(files):
            return self.replace_in_grid_fs(old_gridfs_id, files, computed_file_name)
        with tempfile.TemporaryDirectory() as tmp_out_dir_name:
            new_archive_file_name = os.path.join(tmp_out_dir_name, computed_file_name)
            new_archive_file_name = shutil.make_archive(new_archive_file_name, 'zip', files)
            return self.replace_in_grid_fs(old_gridfs_id, new_archive_file_name, computed_file_name)

    def create_archive_and_add_in_grid_fs(self, files: str, computed_file_name: str = 'gtfs-processed') -> str:
        if is_zipfile(files):
            return self.add_in_grid_fs(files, computed_file_name)
        with tempfile.TemporaryDirectory() as tmp_out_dir_name:
            new_archive_file_name = os.path.join(tmp_out_dir_name, computed_file_name)
            new_archive_file_name = shutil.make_archive(new_archive_file_name, 'zip', files)
            return self.add_in_grid_fs(new_archive_file_name, computed_file_name)

    def check_links(self, data_format_required: List[str]) -> None:
        data_format_exists = set()
        links = self.params.get("links")
        if links is None:
            raise ParameterException('links missing in process')
        elif len(links) == 0:
            raise ParameterException('empty links in process')

        for link in links:
            contributor_id = link.get('contributor_id')
            if not contributor_id:
                msg = "contributor_id missing in links"
                logging.getLogger(__name__).error(msg)
                raise ParameterException(msg)

            data_source_id = link.get('data_source_id')
            if not data_source_id:
                msg = "data_source_id missing in links"
                logging.getLogger(__name__).error(msg)
                raise ParameterException(msg)

            data_source_config_context = self.context.get_contributor_data_source_context(contributor_id,
                                                                                          data_source_id,
                                                                                          data_format_required)
            if not data_source_config_context:
                raise ParameterException(
                    'link {} is not a data_source id present'.format(data_source_id))
            data_source = DataSource.get_one(data_source_id)
            data_format_exists.add(data_source.data_format)
        diff = set(data_format_required) - data_format_exists

        if diff:
            raise ParameterException('data type {} missing in process links'.format(diff))


class NewAbstractContributorProcess(AbstractContributorProcess, metaclass=ABCMeta):
    def __init__(self, context: ContributorExportContext, process: NewProcess) -> None:
        NewAbstractProcess.__init__(self, process)  # type: ignore
        self.context = context
        if self.context.contributor_contexts:
            self.contributor_id = self.context.contributor_contexts[0].contributor.id
        self.gfs = GridFsHandler()
        self.configuration = process.configuration_data_sources
