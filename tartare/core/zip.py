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
from functools import partial

import os
import shutil
from typing import Callable, Union
from zipfile import is_zipfile, ZipFile
from tartare.exceptions import InvalidFile

logger = logging.getLogger(__name__)


def edit_file_in_zip_file(zip_file: str, filename: str, extract_zip_path: str,
                          callback: Union[partial, Callable[[str], None]]) -> None:
    if not is_zipfile(zip_file):
        msg = '{} is not a zip file or does not exist.'.format(zip_file)
        logger.error(msg)
        raise InvalidFile(msg)
    with ZipFile(zip_file, 'r') as files_zip:
        files_zip.extractall(extract_zip_path)
        file_path = '{}/{}'.format(extract_zip_path, filename)
        callback(file_path)


def edit_file_in_zip_file_and_pack(zip_file: str, filename: str, extract_zip_path: str,
                                   new_zip_path: str, callback: Union[partial, Callable[[str], None]],
                                   computed_file_name: str='gtfs-processed') -> str:

        edit_file_in_zip_file(zip_file, filename, extract_zip_path, callback)

        return create_zip_file(extract_zip_path, new_zip_path, computed_file_name)


def create_zip_file(from_dir: str, to_dir: str, filename: str='gtfs-processed') -> str:
    new_archive_file_name = os.path.join(to_dir, filename)

    return shutil.make_archive(new_archive_file_name, 'zip', from_dir)
