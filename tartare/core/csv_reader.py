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

import pandas as pd
import logging
from zipfile import ZipFile, is_zipfile
from tartare.exceptions import InvalidFile
import tempfile
from typing import List, Any, Optional


class CsvReader:
    def __init__(self) -> None:
        self.data = None  # type: pd.DataFrame

    def count_rows(self) -> int:
        """gives number of rows"""
        return self.data.shape[0]

    def file_in_zip_files(self, zip_file: str, filename: str) -> bool:
        with ZipFile(zip_file, 'r') as files_zip:
            return filename in files_zip.namelist()

    def get_max(self, column: str) -> Any:
        return self.data.iloc[:, self.data.columns.get_loc(column)].max()

    def get_min(self, column: str) -> Any:
        return self.data.iloc[:, self.data.columns.get_loc(column)].min()

    def __get_columns_not_in_file(self, filename: str, columns: List[str], sep: str= ',') -> List[str]:
        if not columns:
            return []
        data = pd.read_csv(filename, sep=sep)
        return list(set(columns) - set(data.columns.tolist()))

    def load_data(self, zip_file: str, filename: str, sep: str=',', usecols: Optional[List[str]]=None,
                  **kwargs: Any)->None:
        if not is_zipfile(zip_file):
            msg = '{} is not a zip file or does not exist.'.format(zip_file)
            logging.getLogger(__name__).error(msg)
            raise InvalidFile(msg)
        with ZipFile(zip_file, 'r') as files_zip, tempfile.TemporaryDirectory() as tmp_path:
            files_zip.extract(filename, tmp_path)
            tmp_filename = '{}/{}'.format(tmp_path, filename)
            not_in = self.__get_columns_not_in_file(tmp_filename, usecols, sep)
            if not_in:
                raise InvalidFile("Header not found in file {}, Error : '{}' is not in list".
                                  format(filename, ", ".join(not_in)))
            try:
                self.data = pd.read_csv(tmp_filename, sep=sep, usecols=usecols, **kwargs)
            except ValueError as e:
                raise InvalidFile('Impossible to parse file {}, Error {}'.format(filename, str(e)))

