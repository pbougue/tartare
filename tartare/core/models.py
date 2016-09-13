#coding: utf-8

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

from tartare import mongo
from tartare.interfaces import schema


class Coverage(object):
    mongo_collection = 'coverages'

    def __init__(self, _id, name):
        self._id = _id
        self.name = name

    def save(self):
        mongo.db[self.mongo_collection].insert_one(self.__dict__)

    @classmethod
    def get(cls, coverage_id=None):
        raw = mongo.db[cls.mongo_collection].find_one({'_id': coverage_id})
        if raw is None:
            return None

        return schema.CoverageSchema().load(raw).data

    @classmethod
    def delete(cls, coverage_id=None):
        raw = mongo.db[cls.mongo_collection].delete_one({'_id': coverage_id})
        return raw.deleted_count

    @classmethod
    def find(cls, filter={}):
        raw = mongo.db[cls.mongo_collection].find(filter)

        return schema.CoverageSchema(many=True).load(raw).data

    @classmethod
    def update(cls, coverage_id=None, dataset={}):
        raw = mongo.db[cls.mongo_collection].update_one({'_id': coverage_id}, {'$set': dataset})
        if raw.matched_count == 0:
            return None

        return cls.get(coverage_id)
