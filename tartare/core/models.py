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
import pymongo
import uuid
from datetime import datetime
import logging

@app.before_first_request
def init_mongo():
    mongo.db['contributors'].create_index("data_prefix", unique=True)
    mongo.db['contributors'].create_index([("data_sources.id", pymongo.DESCENDING)], unique=True, sparse=True)


def save_file_in_gridfs(file, gridfs=None, **kwargs):
    if not gridfs:
        gridfs = GridFS(mongo.db)
    return str(gridfs.put(file, **kwargs))


def get_file_from_gridfs(id, gridfs=None):
    if not gridfs:
        gridfs = GridFS(mongo.db)
    return gridfs.get(ObjectId(id))


def delete_file_from_gridfs(id, gridfs=None):
    if not gridfs:
        gridfs = GridFS(mongo.db)
    return gridfs.delete(ObjectId(id))


class Environment(object):
    def __init__(self, tyr_url=None, name=None, current_ntfs_id=None):
        self.name = name
        self.tyr_url = tyr_url
        self.current_ntfs_id = current_ntfs_id


class Coverage(object):
    mongo_collection = 'coverages'

    def __init__(self, id, name, environments=None, grid_calendars_id=None, data_sources=[]):
        self.id = id
        self.name = name
        if environments:
            self.environments = environments
        else:
            self.environments = {}
        self.grid_calendars_id = grid_calendars_id
        self.data_sources = data_sources

    def save_grid_calendars(self, file):
        gridfs = GridFS(mongo.db)
        filename = '{coverage}_calendars.zip'.format(coverage=self.id)
        id = save_file_in_gridfs(file, gridfs=gridfs, filename=filename, coverage=self.id)
        Coverage.update(self.id, {'grid_calendars_id': id})
        # when we delete the file all process reading it will get invalid data
        # TODO: We will need to implement a better solution
        delete_file_from_gridfs(self.grid_calendars_id, gridfs=gridfs)
        self.grid_calendars_id = id

    def get_grid_calendars(self):
        if not self.grid_calendars_id:
            return None
        return get_file_from_gridfs(self.grid_calendars_id)

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
        # we have to use "doted notation' to only update some fields of a nested object
        raw = mongo.db[cls.mongo_collection].update_one({'_id': coverage_id}, {'$set': to_doted_notation(dataset)})
        if raw.matched_count == 0:
            return None

        return cls.get(coverage_id)

    def save_ntfs(self, environment_type, file):
        if environment_type not in self.environments.keys():
            raise ValueError('invalid value for environment_type')
        filename = '{coverage}_{type}_ntfs.zip'.format(coverage=self.id, type=environment_type)
        gridfs = GridFS(mongo.db)
        id = save_file_in_gridfs(file, gridfs=gridfs, filename=filename, coverage=self.id)
        Coverage.update(self.id, {'environments.{}.current_ntfs_id'.format(environment_type): id})
        # when we delete the file all process reading it will get invalid data
        # TODO: We will need to implements a better solution
        delete_file_from_gridfs(self.environments[environment_type].current_ntfs_id)
        self.environments[environment_type].current_ntfs_id = id

    def has_data_source(self, data_source):
        return data_source.id in self.data_sources

    def add_data_source(self, data_source):
        self.data_sources.append(data_source.id)

    def remove_data_source(self, data_source_id):
        if data_source_id in self.data_sources:
            self.data_sources.remove(data_source_id)
            self.update(self.id, {"data_sources": self.data_sources})


class MongoEnvironmentSchema(Schema):
    name = fields.String(required=True)
    tyr_url = fields.Url()
    current_ntfs_id = fields.String(allow_none=True)

    @post_load
    def make_environment(self, data):
        return Environment(**data)


class MongoEnvironmentListSchema(Schema):
    production = fields.Nested(MongoEnvironmentSchema, allow_none=True)
    preproduction = fields.Nested(MongoEnvironmentSchema, allow_none=True)
    integration = fields.Nested(MongoEnvironmentSchema, allow_none=True)

    @post_load
    def remove_none(self, data):
        # We don't want to keep removed environments
        return {key: value for key, value in data.items() if value is not None}


class DataSource(object):
    def __init__(self, id=None, name=None, data_format="gtfs", data_prefix=None, input=[]):
        if not id:
            self.id = str(uuid.uuid4())
        else:
            self.id = id
        self.name = name
        self.data_format = data_format
        self.data_prefix = data_prefix
        self.input = input

    def save(self, contributor_id):
        contributor = self.get_contributor(contributor_id)
        if self.id in [ds.id for ds in contributor.data_sources]:
            raise ValueError("Duplicate data_source id '{}'".format(self.id))
        contributor.data_sources.append(self)
        raw_contrib = MongoContributorSchema().dump(contributor).data
        mongo.db[Contributor.mongo_collection].find_one_and_replace({'_id': contributor.id}, raw_contrib)

    @classmethod
    def get(cls, contributor_id=None, data_source_id=None):
        if contributor_id is not None:
            contributor = cls.get_contributor(contributor_id)
        elif data_source_id is not None:
            raw = mongo.db[Contributor.mongo_collection].find_one({'data_sources.id': data_source_id})
            if raw is None:
                return None
            contributor = MongoContributorSchema(strict=True).load(raw).data
        else:
            raise ValueError("To get data_sources you must provide a contributor_id or a data_source_id")

        data_sources = contributor.data_sources
        if data_source_id is not None:
            data_sources = [ds for ds in data_sources if ds.id == data_source_id]
            if not data_sources:
                return None
        return data_sources

    @classmethod
    def delete(cls, contributor_id, data_source_id=None):
        if data_source_id is None:
            raise ValueError('A data_source id is required')
        contributor = cls.get_contributor(contributor_id)
        nb_delete = len([ds for ds in contributor.data_sources if ds.id == data_source_id])
        contributor.data_sources = [ds for ds in contributor.data_sources if ds.id != data_source_id]
        raw_contrib = MongoContributorSchema().dump(contributor).data
        mongo.db[Contributor.mongo_collection].find_one_and_replace({'_id': contributor.id}, raw_contrib)
        return nb_delete

    @classmethod
    def update(cls, contributor_id, data_source_id=None, dataset={}):
        if data_source_id is None:
            raise ValueError('A data_source id is required')
        if not [ds for ds in cls.get_contributor(contributor_id).data_sources if ds.id == data_source_id]:
            raise ValueError("No data_source id {} exists in contributor with id {}"
                             .format(contributor_id, data_source_id))
        if 'id' in dataset and dataset['id'] != data_source_id:
            raise ValueError("Id from request {} doesn't match id from url {}"
                             .format(dataset['id'], data_source_id))

        # `$` acts as a placeholder of the first match in the list
        contrib_dataset = {'data_sources': {'$': dataset}}
        raw = mongo.db[Contributor.mongo_collection].update_one({'data_sources.id': data_source_id},
                                                                {'$set': to_doted_notation(contrib_dataset)})
        if raw.matched_count == 0:
            return None

        return cls.get(contributor_id, data_source_id)

    @classmethod
    def get_contributor(cls, contributor_id):
        contributor = Contributor.get(contributor_id)
        if contributor is None:
            raise ValueError('Bad contributor {}'.format(contributor_id))
        return contributor


class Input(object):
    def __init__(self, key=None, value=None):
        self.key = key
        self.value = value


class MongoInputSchema(Schema):
    key = fields.String(required=True)
    value = fields.String(required=True)

    @post_load
    def build_input(self, data):
        return Input(**data)


class MongoDataSourceSchema(Schema):
    id = fields.String(required=True)
    name = fields.String(required=True)
    data_format = fields.String(required=False)
    input = fields.Nested(MongoInputSchema, required=True, many=True)

    @post_load
    def build_data_source(self, data):
        return DataSource(**data)


class MongoCoverageSchema(Schema):
    id = fields.String(required=True, load_from='_id', dump_to='_id')
    name = fields.String(required=True)
    environments = fields.Nested(MongoEnvironmentListSchema)
    grid_calendars_id = fields.String(allow_none=True)
    data_sources = fields.List(fields.String())

    @post_load
    def make_coverage(self, data):
        return Coverage(**data)


class Contributor(object):
    mongo_collection = 'contributors'

    def __init__(self, id, name, data_prefix, data_sources=[]):
        self.id = id
        self.name = name
        self.data_prefix = data_prefix
        self.data_sources = data_sources

    def save(self):
        raw = MongoContributorSchema().dump(self).data
        mongo.db[self.mongo_collection].insert_one(raw)

    def data_source_ids(self):
        return [d.id for d in self.data_sources]

    @classmethod
    def get(cls, contributor_id=None):
        raw = mongo.db[cls.mongo_collection].find_one({'_id': contributor_id})
        if raw is None:
            return None
        return MongoContributorSchema(strict=True).load(raw).data

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
    data_sources = fields.Nested(MongoDataSourceSchema, many=True, required=False)

    @post_load
    def make_contributor(self, data):
        return Contributor(**data)


class Job(object):
    mongo_collection = 'jobs'

    def __init__(self, id, action_type, state='pending', step=None):
        self.id = id
        self.action_type = action_type
        self.step = step
        # 'pending', 'running', 'done', 'failed'
        self.state = state
        self.error_message = ""
        self.started_at = datetime.utcnow()
        self.updated_at = None

    def save(self):
        raw = MongoJobSchema().dump(self).data
        mongo.db[self.mongo_collection].insert_one(raw)

    @classmethod
    def find(cls, filter):
        raw = mongo.db[cls.mongo_collection].find(filter)
        return MongoJobSchema(many=True).load(raw).data

    @classmethod
    def get(cls, job_id=None):
        if job_id:
            raw = mongo.db[cls.mongo_collection].find_one({'_id': job_id})
            if raw is None:
                return None
            return MongoJobSchema(strict=False).load(raw).data
        else:
            return cls.find(filter={})

    @classmethod
    def update(cls, job_id, state=None, step=None, error_message=None):
        logger = logging.getLogger(__name__)
        if not job_id:
            logger.error('job_id cannot be empty')
            return None
        job = cls.get(job_id)
        if not job:
            logger.error("Cannot find job to update %s", job_id)
            return None
        if state is not None:
            job["state"] = state
        if step is not None:
            job["step"] = step
        if error_message is not None:
            job["error_message"] = error_message

        job['updated_at'] = datetime.utcnow()

        raw = mongo.db[cls.mongo_collection].update_one({'_id': job_id}, {'$set': MongoJobSchema().dump(job).data})
        if raw.matched_count == 0:
            return None
        return job


class MongoJobSchema(Schema):
    id = fields.String(required=True, load_from='_id', dump_to='_id')
    action_type = fields.String(required=True)
    state = fields.String(required=True)
    step = fields.String(required=False)
    started_at = fields.DateTime(required=False)
    updated_at = fields.DateTime(required=False)
