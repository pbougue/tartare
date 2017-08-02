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
from tartare.core.context import Context
from tartare.processes.processes import AbstractProcess
import logging
from tartare.core.gridfs_handler import GridFsHandler
from zipfile import ZipFile
import csv
from tartare.core.calendar_handler import get_dict_from_zip
import tempfile
import shutil


class Ruspell(AbstractProcess):

    def do(self) -> Context:
        return self.context


class ComputeDirections(AbstractProcess):

    def do(self) -> Context:
        return self.context


class HeadsignShortName(AbstractProcess):

    def do(self) -> Context:
        return self.context


class GtfsAgencyFile(AbstractProcess):

    @staticmethod
    def get_content_agency(gtfs_zip):
        with ZipFile(gtfs_zip, 'r') as gtfs_zip:
            try:
                return get_dict_from_zip(gtfs_zip, 'agency.txt')
            except KeyError:
                pass
            return []
    @staticmethod
    def is_valid(data):
        if not data:
            return False
        return any([(v in data[0].keys()) for v in ['agency_name', 'agency_url', 'agency_timezone']])

    def get_data(self):
        # for more informations, see : https://developers.google.com/transit/gtfs/reference/agency-file
        agency_data = {
            "agency_id": 42,
            "agency_name": "",
            "agency_url": "",
            "agency_timezone": "",
            "agency_lang": "",
            "agency_phone": "",
            "agency_fare_url": "",
            "agency_email": ""
        }
        agency_data.update(self.params.get("data", {}))
        return agency_data

    def create_new_zip(self, files_zip, tmp_dir_name, filename):
        new_data = self.get_data()
        files_zip.extractall(tmp_dir_name)
        with open('{}/{}'.format(tmp_dir_name, 'agency.txt'), 'a') as agency:
            writer = csv.DictWriter(agency, fieldnames=list(new_data.keys()))
            writer.writeheader()
            writer.writerow(new_data)
        new_zip = '{}/{}'.format(tmp_dir_name, filename.split(".")[0])
        shutil.make_archive(new_zip, 'zip', tmp_dir_name)
        return new_zip

    def manage_agency_file(self, data_source_context):
        grid_out = GridFsHandler().get_file_from_gridfs(data_source_context.gridfs_id)
        filename = grid_out.filename
        data = self.get_content_agency(grid_out)
        if not self.is_valid(data):
            logging.getLogger(__name__).debug('data source {}  without agency.txt file'.
                                                  format(data_source_context.data_source_id))
            with ZipFile(grid_out, 'r') as files_zip:
                with tempfile.TemporaryDirectory() as tmp_dir_name:
                    new_zip = self.create_new_zip(files_zip, tmp_dir_name, grid_out.filename)
                    with open('{}.{}'.format(new_zip, 'zip'), 'rb') as file:
                        GridFsHandler().delete_file_from_gridfs(data_source_context.gridfs_id)
                        data_source_context.gridfs_id = GridFsHandler().save_file_in_gridfs(file=file,
                                                                                            filename=filename)

    def do(self) -> Context:
        contributor = self.context.contributor_contexts[0].contributor
        for data_source_id in self.data_source_ids:
            data_source_context = self.context.get_contributor_data_source_context(contributor_id=contributor.id,
                                                                                   data_source_id=data_source_id)
            if not data_source_context:
                msg = 'impossible to build preprocess {} : data source {} not exist for contributor {}'.format(
                    'GtfsAgencyFile',
                    data_source_id,
                    contributor.id)
                logging.getLogger(__name__).warning(msg)
                continue
            self.manage_agency_file(data_source_context)
        return self.context
