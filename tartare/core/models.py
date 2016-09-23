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
from tartare import mongo
from marshmallow import Schema, fields, post_load


class Coverage(object):
    mongo_collection = 'coverages'

    class TechnicalConfiguration(object):
        def __init__(self, input_dir, output_dir, current_data_dir):
            self.input_dir = input_dir
            self.output_dir = output_dir
            self.current_data_dir = current_data_dir

    def __init__(self, id, name, technical_conf):
        self.id = id
        self.name = name
        self.technical_conf = technical_conf

    def save(self):
        raw = MongoCoverageSchema().dump(self).data
        mongo.db[self.mongo_collection].insert_one(raw)

    @classmethod
    def get(cls, coverage_id=None):
        raw = mongo.db[cls.mongo_collection].find_one({'_id': coverage_id})
        if raw is None:
            return None

        return MongoCoverageSchema().load(raw).data

    @classmethod
    def delete(cls, coverage_id=None):
        raw = mongo.db[cls.mongo_collection].delete_one({'_id': coverage_id})
        return raw.deleted_count

    @classmethod
    def find(cls, filter):
        raw = mongo.db[cls.mongo_collection].find(filter)
        return MongoCoverageSchema(many=True).load(raw).data

    @classmethod
    def all(cls):
        return cls.find(filter={})

    @classmethod
    def update(cls, coverage_id=None, dataset={}):
        raw = mongo.db[cls.mongo_collection].update_one({'_id': coverage_id}, {'$set': dataset})
        if raw.matched_count == 0:
            return None

        return cls.get(coverage_id)


class MongoCoverageTechnicalConfSchema(Schema):
    input_dir = fields.String()
    output_dir = fields.String()
    current_data_dir = fields.String()

    @post_load
    def make_technical_conf(self, data):
        return Coverage.TechnicalConfiguration(**data)


class MongoCoverageSchema(Schema):
    id = fields.String(required=True, load_from='_id', dump_to='_id')
    name = fields.String(required=True)
    technical_conf = fields.Nested(MongoCoverageTechnicalConfSchema)

    @post_load
    def make_coverage(self, data):
        return Coverage(**data)
