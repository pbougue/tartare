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

from tartare.core.readers import JsonReader, CsvReader
from tests.utils import _get_file_fixture_full_path


class TestCsvReader:
    def __load_sample(self):
        csv_reader = CsvReader()
        csv_reader.load_csv_data(_get_file_fixture_full_path('readers/sample.csv'))
        return csv_reader

    def test_reader_load(self):
        reader = CsvReader()
        reader.load_csv_data(_get_file_fixture_full_path('prepare_external_settings/expected_fusio_object_codes.txt'))
        assert reader.count_rows() == 25

    def test_reader_count(self):
        reader = self.__load_sample()
        assert reader.count_rows() == 4

    def test_reader_min(self):
        reader = self.__load_sample()
        reader.get_min('age') == 18
        reader.get_min('id') == 1
        reader.get_min('city') == 'bordeaux'

    def test_reader_max(self):
        reader = self.__load_sample()
        reader.get_max('age') == 77
        reader.get_max('id') == 92
        reader.get_max('city') == 'paris'

    def test_get_mapping_from_columns(self):
        reader = self.__load_sample()
        iter = reader.get_mapping_from_columns('id', lambda row: "{name} ({age}): {city}".format(name=row['name'],
                                                                                                 age=row['age'],
                                                                                                 city=row['city']))
        map = list(iter)
        assert map == [{42: 'bob (23): bordeaux'}, {92: 'toto (25): lyon'}, {66: 'tata (77): nantes'},
                       {1: 'kenny (18): paris'}], print(map)


class TestJsonReader:
    def test_load(self):
        reader = JsonReader()
        with open(_get_file_fixture_full_path('prepare_external_settings/tr_perimeter_id.json')) as perimeter_file:
            reader.load_json_data_from_io(perimeter_file)
            assert reader.count_rows() == 5

    def __load_sample(self):
        json_reader = JsonReader()
        with open(_get_file_fixture_full_path('readers/sample.json')) as sample_file:
            json_reader.load_json_data_from_io(sample_file)
        return json_reader

    def test_reader_count(self):
        reader = self.__load_sample()
        assert reader.count_rows() == 6

    def test_reader_min(self):
        reader = self.__load_sample()
        assert reader.get_min('height') == 155
        assert reader.get_min('weight') == 52
        assert reader.get_min('name') == 'Bob'

    def test_reader_max(self):
        reader = self.__load_sample()
        assert reader.get_max('height') == 215
        assert reader.get_max('weight') == 80
        assert reader.get_max('name') == 'Stan'

    def test_get_mapping_from_columns(self):
        reader = self.__load_sample()
        iter = reader.get_mapping_from_columns('name', lambda row: "{weight} / {height}".format(weight=row['weight'],
                                                                                                height=row['height']))
        map = list(iter)
        assert map == [{'Bob': '70 / 180'}, {'Kenny': '72 / 155'}, {'Stan': '74 / 190'}, {'Cartman': '80 / 215'},
                       {'Chef': '66 / 177'}, {'Kyle': '52 / 180'}], print(map)
