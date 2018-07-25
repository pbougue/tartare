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
from datetime import datetime
import os
import tempfile
from zipfile import ZipFile, ZIP_DEFLATED

from typing import List

from tartare.core.context import Context
from tartare.core.models import DataSource
from tartare.exceptions import RuntimeException
from tartare.helper import dic_to_memory_csv
from tartare.processes.abstract_process import NewAbstractCoverageProcess
from tartare.processes.utils import process_registry


@process_registry()
class ComputeODS(NewAbstractCoverageProcess):
    format_date = '%Y%m%d'

    @property
    def metadata_ordered_columns(self) -> List[str]:
        return ['ID', 'Description', 'Format', 'Download', 'Validity start date', 'Validity end date',
                'Licence', 'License link', 'Size', 'Update date']

    def do(self) -> Context:
        meta_data_dict = []
        data_sets_with_file_names = {}
        for input_data_source_id in self.data_source_ids:
            data_source = DataSource.get_one(input_data_source_id)
            data_format_formatted = data_source.data_format.upper()
            data_set = data_source.get_last_data_set()
            if not data_set.validity_period:
                raise RuntimeException(
                    'data set of data source {} has no validity period for ods publication'.format(data_source.id))
            coverage = self.context.coverage
            data_set_file = self.gfs.get_file_from_gridfs(data_set.gridfs_id)
            data_set_file_name = '{}_{}.zip'.format(coverage.id, data_format_formatted)
            data_sets_with_file_names[data_set_file_name] = data_set_file
            file_size = data_set_file.length
            meta_data_dict.append(
                {
                    'ID': '{}-{}'.format(coverage.id, data_format_formatted),
                    'Description': coverage.short_description,
                    'Format': data_format_formatted,
                    'Download': data_set_file_name,
                    'Validity start date': data_set.validity_period.start_date.strftime(self.format_date),
                    'Validity end date': data_set.validity_period.end_date.strftime(self.format_date),
                    'Licence': coverage.license.name,
                    'License link': coverage.license.url,
                    'Size': file_size,
                    'Update date': datetime.now().strftime(self.format_date)
                }
            )
        memory_csv = dic_to_memory_csv(meta_data_dict, self.metadata_ordered_columns)
        with tempfile.TemporaryDirectory() as tmp_dirname:
            zip_file_name = '{coverage}.zip'.format(coverage=coverage.id)
            zip_full_path = os.path.join(tmp_dirname, zip_file_name)
            with ZipFile(zip_full_path, 'a', ZIP_DEFLATED, False) as zip_out:
                zip_out.writestr('{coverage}.txt'.format(coverage=coverage.id), memory_csv.getvalue())
                for data_set_file_name, data_set_file in data_sets_with_file_names.items():
                    zip_out.writestr(data_set_file_name, data_set_file.read())

            with open(zip_full_path, 'rb') as zip_full_file:
                gridfs_id = self.gfs.save_file_in_gridfs(zip_full_file, filename=zip_file_name)
                self.save_result_into_target_data_source(self.context.coverage, gridfs_id)

        return self.context
