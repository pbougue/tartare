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

logger = logging.getLogger(__name__)

import urllib.request
from tartare.core.gridfs_handler import GridFsHandler
from abc import ABCMeta, abstractmethod


class AbstractDataSetFetcher(metaclass=ABCMeta):
    @abstractmethod
    def fetch(self):
        pass


class HttpOrFTPDataSetFetcher(AbstractDataSetFetcher):
    def __init__(self, data_source, context):
        self.data_source = data_source
        self.context = context

    def fetch(self):
        logger.info("fetching")
        data_input = self.data_source.input
        if data_input:
            logger.info(data_input.get('url'))
            tmp_file_name = "gtfs-{data_source_id}.zip".format(data_source_id=self.data_source.id)
            urllib.request.urlretrieve(data_input.get('url'), tmp_file_name)
            with open(tmp_file_name, 'rb') as file:
                grid_fs_id = GridFsHandler().save_file_in_gridfs(file)
                logger.info(grid_fs_id)
                # self.context.update({'contrib.id': {self.data_source.id: "id gridfs"}})
        return self.context
