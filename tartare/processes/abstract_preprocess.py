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
import os
import shutil
import tempfile
from abc import ABCMeta, abstractmethod
from typing import List

from tartare.core.context import Context
from tartare.core.gridfs_handler import GridFsHandler
from tartare.core.models import PreProcess


class AbstractProcess(metaclass=ABCMeta):
    def __init__(self, context: Context, preprocess: PreProcess) -> None:
        self.context = context
        self.params = preprocess.params if preprocess else {}  # type: dict
        self.data_source_ids = preprocess.data_source_ids if preprocess else []

    @abstractmethod
    def do(self) -> Context:
        pass


class AbstractContributorProcess(AbstractProcess, metaclass=ABCMeta):
    def __init__(self, context: Context, preprocess: PreProcess) -> None:
        super().__init__(context, preprocess)
        if self.context.contributor_contexts:
            self.contributor_id = self.context.contributor_contexts[0].contributor.id
        self.gfs = GridFsHandler()

    def create_archive_and_replace_in_grid_fs(self, old_gridfs_id: str, tmp_dir_name: str, backup_files: List[str] = [],
                                              computed_file_name: str = 'gtfs-processed') -> str:
        for backup_file in backup_files:
            os.remove(backup_file)
        with tempfile.TemporaryDirectory() as tmp_out_dir_name:
            new_archive_file_name = os.path.join(tmp_out_dir_name, computed_file_name)
            new_archive_file_name = shutil.make_archive(new_archive_file_name, 'zip', tmp_dir_name)
            with open(new_archive_file_name, 'rb') as new_archive_file:
                new_gridfs_id = self.gfs.save_file_in_gridfs(new_archive_file, filename=computed_file_name + '.zip')
                self.gfs.delete_file_from_gridfs(old_gridfs_id)
                return new_gridfs_id
