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
from marshmallow import Schema, fields, post_load
from tartare import app
from tartare.helper import to_doted_notation
from gridfs import GridFS
from bson.objectid import ObjectId
import logging


@app.before_first_request
def init_mongo():
    mongo.db['contributors'].ensure_index("data_prefix", unique=True)


class Environment(object):
    def __init__(self, tyr_url=None, name=None):
        self.name = name
        self.tyr_url = tyr_url

class Coverage(object):
    mongo_collection = 'coverages'

    class TechnicalConfiguration(object):
        def __init__(self, input_dir=None, output_dir=None, current_data_dir=None):
            self.input_dir = input_dir
            self.output_dir = output_dir
            self.current_data_dir = current_data_dir

    def __init__(self, id, name, technical_conf, environments=None, grid_calendars_id=None):
        self.id = id
        self.name = name
        self.technical_conf = technical_conf
        if environments:
            self.environments = environments
        else:
            self.environments = {}
        self.grid_calendars_id = grid_calendars_id

    def save_grid_calendars(self, file):
        self.grid_calendars_id
        gridfs = GridFS(mongo.db)
        id = gridfs.put(file)
        Coverage.update(self.id, {'grid_calendars_id': str(id)})
        #when we delete the file all process reading it will get invalid data
        #TODO: We will need to implements a better solution
        gridfs.delete(ObjectId(self.grid_calendars_id))
        self.grid_calendars_id = id



    def save(self):
        raw = MongoCoverageSchema().dump(self).data
        mongo.db[self.mongo_collection].insert_one(raw)

    @classmethod
    def get(cls, coverage_id=None):
        raw = mongo.db[cls.mongo_collection].find_one({'_id': coverage_id})
        if raw is None:
            return None

        return MongoCoverageSchema(strict=True).load(raw).data

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
        #we have to use "doted notation' to only update some fields of a nested object
        raw = mongo.db[cls.mongo_collection].update_one({'_id': coverage_id}, {'$set': to_doted_notation(dataset)})
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

class MongoEnvironmentSchema(Schema):
    name = fields.String(required=True)
    tyr_url = fields.Url()

    @post_load
    def make_environment(self, data):
        return Environment(**data)

class MongoEnvironmentListSchema(Schema):
    production = fields.Nested(MongoEnvironmentSchema, allow_none=True)
    preproduction = fields.Nested(MongoEnvironmentSchema, allow_none=True)
    integration = fields.Nested(MongoEnvironmentSchema, allow_none=True)

    @post_load
    def remove_none(self, data):
        #We don't want to keep removed environments
        return {key: value for key, value in data.items() if value is not None}


class MongoCoverageSchema(Schema):
    id = fields.String(required=True, load_from='_id', dump_to='_id')
    name = fields.String(required=True)
    technical_conf = fields.Nested(MongoCoverageTechnicalConfSchema)
    environments = fields.Nested(MongoEnvironmentListSchema)
    grid_calendars_id = fields.String(allow_none=True)

    @post_load
    def make_coverage(self, data):
        return Coverage(**data)


class Contributor(object):
    mongo_collection = 'contributors'

    def __init__(self, id, name, data_prefix):
        self.id = id
        self.name = name
        self.data_prefix = data_prefix

    def save(self):
        raw = MongoContributorSchema().dump(self).data
        mongo.db[self.mongo_collection].insert_one(raw)

    @classmethod
    def get(cls, contributor_id=None):
        raw = mongo.db[cls.mongo_collection].find_one({'_id': contributor_id})
        if raw is None:
            return None
        return MongoContributorSchema().load(raw).data

    @classmethod
    def delete(cls, contributor_id=None):
        raw = mongo.db[cls.mongo_collection].delete_one({'_id': contributor_id})
        return raw.deleted_count

    @classmethod
    def find(cls, filter):
        raw = mongo.db[cls.mongo_collection].find(filter)
        return MongoContributorSchema(many=True).load(raw).data

    @classmethod
    def all(cls):
        return cls.find(filter={})

    @classmethod
    def update(cls, contributor_id=None, dataset={}):
        raw = mongo.db[cls.mongo_collection].update_one({'_id': contributor_id}, {'$set': dataset})
        if raw.matched_count == 0:
            return None

        return cls.get(contributor_id)


class MongoContributorSchema(Schema):
    id = fields.String(required=True, load_from='_id', dump_to='_id')
    name = fields.String(required=True)
    data_prefix = fields.String(required=True)

    @post_load
    def make_contributor(self, data):
        return Contributor(**data)
