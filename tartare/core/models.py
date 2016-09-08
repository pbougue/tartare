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


def get_as_obj(cls, cursor):
    for o in cursor:
        yield cls.create_from_mongo(o)


class Coverage(object):
    def __init__(self, _id, name):
        self._id = _id
        self.name = name

    @classmethod
    def get(cls, coverage_id=None):
        raw = mongo.db.coverages.find_one({'_id': coverage_id})

        return cls.create_from_mongo(raw)

    @classmethod
    def find(cls, filter={}):
        return get_as_obj(cls, mongo.db.coverages.find(filter))

    @classmethod
    def create_from_mongo(cls, raw):
        return Coverage(_id=raw['_id'], name=raw['name'])

