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

from gridfs import GridFS
from bson.objectid import ObjectId
from tartare import mongo
from typing import Union
from io import IOBase
from gridfs.grid_file import GridOut


class GridFsHandler(object):
    def __init__(self, database=None):
        if database is None:
            database = mongo.db
        self.gridfs = GridFS(database)

    def save_file_in_gridfs(self, file: Union[str, bytes, IOBase, GridOut], **kwargs) -> str:
        """
            :rtype: the id of the gridfs
        """
        return str(self.gridfs.put(file, **kwargs))

    def get_file_from_gridfs(self, id: str) -> GridOut:
        return self.gridfs.get(ObjectId(id))

    def delete_file_from_gridfs(self, id: str):
        self.gridfs.delete(ObjectId(id))

    def copy_file(self, id: str) -> str:
        file = self.get_file_from_gridfs(id)
        return self.save_file_in_gridfs(file=file, filename=file.filename)
