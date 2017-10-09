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

import json
import logging
import os
import tempfile
from abc import ABCMeta
from typing import List, Any, Optional, Callable, Generator
from zipfile import ZipFile, is_zipfile

import pandas as pd
from gridfs import GridOut

from tartare.exceptions import InvalidFile


class AbstractPandaReader(metaclass=ABCMeta):
    def __init__(self) -> None:
        self.data = None  # type: pd.DataFrame

    def count_rows(self) -> int:
        """gives number of rows"""
        return self.data.shape[0]

    def get_max(self, column: str) -> Any:
        return self.data.iloc[:, self.data.columns.get_loc(column)].max()

    def get_min(self, column: str) -> Any:
        return self.data.iloc[:, self.data.columns.get_loc(column)].min()

    def get_mapping_from_columns(self, key_column: str, value_apply_function: Callable[..., Any]) -> Generator:
        """
        :param key_column: the column to use as a key in the dict generated
        :param value_apply_function: a lambda function to apply on the self.data restricted to columns used the get
        the value of the dict
        :return: a list of dict with value of column key_column as key and value_apply_function(columns_used, row)
        as value:
            [
                {"value_of_key_column_row_1": value_apply_function(columns_used, row1)},
                {"value_of_key_column_row_2": value_apply_function(columns_used, row2)},
                ...
                {"value_of_key_column_row_n": value_apply_function(columns_used, rown)}
            ]
        """
        for key, value in self.data.iterrows():
            yield {value[key_column]: value_apply_function(value)}

    def apply(self, column_name: str, callback: Callable[..., Any], fillna: str='') -> None:
        self.data[column_name] = self.data.apply(callback, axis=1).fillna(fillna)


class JsonReader(AbstractPandaReader):
    def load_json_data_from_io(self, json_file: GridOut, usecols: Optional[List[str]] = None) -> None:
        try:
            self.data = pd.io.json.json_normalize(json.load(json_file))
            if usecols:
                self.data = self.data.filter(items=usecols).drop_duplicates()
        except ValueError as e:
            raise InvalidFile('Impossible to parse file {}, Error {}'.format(json_file.filename, str(e)))


class CsvReader(AbstractPandaReader):
    def file_in_zip_files(self, zip_file: str, filename: str) -> bool:
        with ZipFile(zip_file, 'r') as files_zip:
            return filename in files_zip.namelist()

    def __get_columns_not_in_file(self, filename: str, columns: List[str], sep: str = ',') -> List[str]:
        if not columns:
            return []
        data = pd.read_csv(filename, sep=sep)
        return list(set(columns) - set(data.columns.tolist()))

    def load_csv_data_from_zip_file(self, zip_file: GridOut, filename: str, sep: str = ',',
                                    usecols: Optional[List[str]] = None,
                                    **kwargs: Any) -> None:
        if not is_zipfile(zip_file):
            msg = '{} is not a zip file or does not exist.'.format(zip_file)
            logging.getLogger(__name__).error(msg)
            raise InvalidFile(msg)
        with ZipFile(zip_file, 'r') as files_zip, tempfile.TemporaryDirectory() as tmp_path:
            files_zip.extract(filename, tmp_path)
            tmp_filename = '{}/{}'.format(tmp_path, filename)
            self.load_csv_data(tmp_filename, sep, usecols, **kwargs)

    def load_csv_data(self, csv_full_filename: str, sep: str = ',', usecols: Optional[List[str]] = None,
                      **kwargs: Any) -> None:
        filename = csv_full_filename.split(os.path.sep)[-1]
        not_in = self.__get_columns_not_in_file(csv_full_filename, usecols, sep)
        if not_in:
            raise InvalidFile("Header not found in file {}, Error : '{}' is not in list".
                              format(filename, ", ".join(not_in)))
        try:
            self.data = pd.read_csv(csv_full_filename, sep=sep, usecols=usecols, **kwargs)
        except ValueError as e:
            raise InvalidFile('Impossible to parse file {}, Error {}'.format(filename, str(e)))

    def save_as_csv(self, csv_full_filename: str) -> None:
        self.data.to_csv(csv_full_filename, index=False)
