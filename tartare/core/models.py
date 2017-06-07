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
from tartare.core.gridfs_handler import GridFsHandler

import pymongo
import uuid
from datetime import datetime
import logging

@app.before_first_request
def init_mongo():
    mongo.db['contributors'].create_index("data_prefix", unique=True)
    mongo.db['contributors'].create_index([("data_sources.id", pymongo.DESCENDING)], unique=True, sparse=True)


def get_contributor(contributor_id):
    contributor = Contributor.get(contributor_id)
    if contributor is None:
        raise ValueError('Bad contributor {}'.format(contributor_id))
    return contributor


class Environment(object):
    def __init__(self, name=None, current_ntfs_id=None, publication_platforms=[]):
        self.name = name
        self.current_ntfs_id = current_ntfs_id
        self.publication_platforms = publication_platforms


class Platform(object):
    def __init__(self, name, type, url):
        self.name = name
        self.type = type
        self.url = url


class Coverage(object):
    mongo_collection = 'coverages'

    def __init__(self, id, name, environments=None, grid_calendars_id=None, contributors=None):
        self.id = id
        self.name = name
        self.environments = {} if environments is None else environments
        self.grid_calendars_id = grid_calendars_id
        self.contributors = [] if contributors is None else contributors

    def save_grid_calendars(self, file):
        gridfs_handler = GridFsHandler()
        filename = '{coverage}_calendars.zip'.format(coverage=self.id)
        id = gridfs_handler.save_file_in_gridfs(file, filename=filename, coverage=self.id)
        Coverage.update(self.id, {'grid_calendars_id': id})
        # when we delete the file all process reading it will get invalid data
        # TODO: We will need to implement a better solution
        gridfs_handler.delete_file_from_gridfs(self.grid_calendars_id)
        self.grid_calendars_id = id

    def get_grid_calendars(self):
        if not self.grid_calendars_id:
            return None

        gridfs_handler = GridFsHandler()
        return gridfs_handler.get_file_from_gridfs(self.grid_calendars_id)

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
        gridfs_handler = GridFsHandler()
        id = gridfs_handler.save_file_in_gridfs(file, filename=filename, coverage=self.id)
        Coverage.update(self.id, {'environments.{}.current_ntfs_id'.format(environment_type): id})
        # when we delete the file all process reading it will get invalid data
        # TODO: We will need to implements a better solution
        gridfs_handler.delete_file_from_gridfs(self.environments[environment_type].current_ntfs_id)
        self.environments[environment_type].current_ntfs_id = id

    def has_contributor(self, contributor):
        return contributor.id in self.contributors

    def add_contributor(self, contributor):
        self.contributors.append(contributor.id)
        self.update(self.id, {"contributors": self.contributors})

    def remove_contributor(self, contributor_id):
        if contributor_id in self.contributors:
            self.contributors.remove(contributor_id)
            self.update(self.id, {"contributors": self.contributors})


class MongoPlatformSchema(Schema):
    name = fields.String(required=True)
    type = fields.String(required=True)
    url = fields.String(required=True)

    @post_load
    def make_platform(self, data):
        return Platform(**data)


class MongoEnvironmentSchema(Schema):
    name = fields.String(required=True)
    current_ntfs_id = fields.String(allow_none=True)
    publication_platforms = fields.Nested(MongoPlatformSchema, many=True)

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
    def __init__(self, id=None, name=None, data_format="gtfs", input={}):
        if not id:
            self.id = str(uuid.uuid4())
        else:
            self.id = id
        self.name = name
        self.data_format = data_format
        self.input = input

    def save(self, contributor_id):
        contributor = get_contributor(contributor_id)
        if self.id in [ds.id for ds in contributor.data_sources]:
            raise ValueError("Duplicate data_source id '{}'".format(self.id))
        contributor.data_sources.append(self)
        raw_contrib = MongoContributorSchema().dump(contributor).data
        mongo.db[Contributor.mongo_collection].find_one_and_replace({'_id': contributor.id}, raw_contrib)

    @classmethod
    def get(cls, contributor_id=None, data_source_id=None):
        if contributor_id is not None:
            contributor = get_contributor(contributor_id)
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
        contributor = get_contributor(contributor_id)
        nb_delete = len([ds for ds in contributor.data_sources if ds.id == data_source_id])
        contributor.data_sources = [ds for ds in contributor.data_sources if ds.id != data_source_id]
        raw_contrib = MongoContributorSchema().dump(contributor).data
        mongo.db[Contributor.mongo_collection].find_one_and_replace({'_id': contributor.id}, raw_contrib)
        return nb_delete

    @classmethod
    def update(cls, contributor_id, data_source_id=None, dataset={}):
        if data_source_id is None:
            raise ValueError('A data_source id is required')
        if not [ds for ds in get_contributor(contributor_id).data_sources if ds.id == data_source_id]:
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


class PreProcess(object):
    def __init__(self, id=None, type=None, source_params=None):
        self.id = str(uuid.uuid4()) if id is None else id
        self.type = type
        self.source_params = {} if source_params is None else source_params

    def save(self, contributor_id):
        contributor = get_contributor(contributor_id)

        if self.id in [p.id for p in contributor.preprocesses]:
            raise ValueError("Duplicate data_source id '{}'".format(self.id))

        contributor.preprocesses.append(self)
        raw_contrib = MongoContributorSchema().dump(contributor).data
        mongo.db[Contributor.mongo_collection].find_one_and_replace({'_id': contributor.id}, raw_contrib)

    @classmethod
    def get(cls, contributor_id=None, preprocess_id=None):
        if contributor_id is not None:
            contributor = get_contributor(contributor_id)
        elif preprocess_id is not None:
            raw = mongo.db[Contributor.mongo_collection].find_one({'preprocesses.id': preprocess_id})
            if raw is None:
                return None
            contributor = MongoContributorSchema(strict=True).load(raw).data
        else:
            raise ValueError("To get preprocess you must provide a contributor_id or a preprocess_id")

        preprocesses = contributor.preprocesses

        if preprocess_id is None:
            return preprocesses
        p = next((p for p in preprocesses if p.id == preprocess_id), None)
        return [p] if p else []


    @classmethod
    def delete(cls, contributor_id, preprocess_id):
        if preprocess_id is None:
            raise ValueError('A preprocess id is required')
        contributor = get_contributor(contributor_id)
        nb_delete = len([p for p in contributor.preprocesses if p.id == preprocess_id])
        contributor.preprocesses = [p for p in contributor.preprocesses if p.id != preprocess_id]
        raw_contrib = MongoContributorSchema().dump(contributor).data
        mongo.db[Contributor.mongo_collection].find_one_and_replace({'_id': contributor.id}, raw_contrib)
        return nb_delete

    @classmethod
    def update(cls, contributor_id, preprocess_id, preprocess=None):
        if preprocess_id is None:
            raise ValueError('A data_source id is required')
        if not [ps for ps in get_contributor(contributor_id).preprocesses if ps.id == preprocess_id]:
            raise ValueError("No preprocesses id {} exists in contributor with id {}"
                             .format(contributor_id, preprocess_id))
        if 'id' in preprocess and preprocess['id'] != preprocess_id:
            raise ValueError("Id from request {} doesn't match id from url {}"
                             .format(preprocess['id'], preprocess_id))

        preprocess['id'] = preprocess_id
        raw = mongo.db[Contributor.mongo_collection].update_one({'preprocesses.id': preprocess_id},
                                                                {'$set': {'preprocesses.$': preprocess}})
        if raw.matched_count == 0:
            return None

        return cls.get(contributor_id, preprocess_id)


class MongoDataSourceSchema(Schema):
    id = fields.String(required=True)
    name = fields.String(required=True)
    data_format = fields.String(required=False)
    input = fields.Dict(required=True)

    @post_load
    def build_data_source(self, data):
        return DataSource(**data)


class MongoPreProcessSchema(Schema):
    id = fields.String(required=True)
    type = fields.String(required=True)
    source_params = fields.Dict(required=True)

    @post_load
    def build_data_source(self, data):
        return PreProcess(**data)


class MongoCoverageSchema(Schema):
    id = fields.String(required=True, load_from='_id', dump_to='_id')
    name = fields.String(required=True)
    environments = fields.Nested(MongoEnvironmentListSchema)
    grid_calendars_id = fields.String(allow_none=True)
    contributors = fields.List(fields.String())

    @post_load
    def make_coverage(self, data):
        return Coverage(**data)


class Contributor(object):
    mongo_collection = 'contributors'

    def __init__(self, id, name, data_prefix, data_sources=None, preprocesses=None):
        self.id = id
        self.name = name
        self.data_prefix = data_prefix
        self.data_sources = [] if data_sources is None else data_sources
        self.preprocesses = [] if preprocesses is None else preprocesses

    def save(self):
        raw = MongoContributorSchema().dump(self).data
        mongo.db[self.mongo_collection].insert_one(raw)


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
    preprocesses = fields.Nested(MongoPreProcessSchema, many=True, required=False)

    @post_load
    def make_contributor(self, data):
        return Contributor(**data)


class Job(object):
    mongo_collection = 'jobs'

    def __init__(self, id, action_type, contributor_id=None, coverage_id=None, state='pending', step=None):
        self.id = id
        self.action_type = action_type
        self.contributor_id = contributor_id
        self.coverage_id = coverage_id
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
    def get(cls, contributor_id=None, coverage_id=None, job_id=None):
        find_filter = {}
        if contributor_id:
            find_filter.update({'contributor_id': contributor_id})
        if coverage_id:
            find_filter.update({'coverage_id': coverage_id})
        if job_id:
            find_filter.update({'_id': job_id})
            raw = mongo.db[cls.mongo_collection].find_one(find_filter)
            return MongoJobSchema(strict=False).load(raw).data

        return cls.find(filter=find_filter)

    @classmethod
    def update(cls, job_id, state=None, step=None, error_message=None):
        logger = logging.getLogger(__name__)
        if not job_id:
            logger.error('job_id cannot be empty')
            return None
        job = cls.get(job_id=job_id)
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
    contributor_id = fields.String(required=False)
    coverage_id = fields.String(required=False)
    state = fields.String(required=True)
    step = fields.String(required=False)
    started_at = fields.DateTime(required=False)
    updated_at = fields.DateTime(required=False)


class ContributorExport(object):
    mongo_collection = 'contributor_exports'

    def __init__(self, contributor_id, gridfs_id, data_sources=None):
        self.id = str(uuid.uuid4())
        self.contributor_id = contributor_id
        self.gridfs_id = gridfs_id
        self.created_at = datetime.utcnow()
        self.data_sources = [] if data_sources is None else data_sources

    def save(self):
        raw = MongoContributorExportSchema().dump(self).data
        mongo.db[self.mongo_collection].insert_one(raw)

    @classmethod
    def get(cls, contributor_id):
        if not contributor_id:
            return None
        raw = mongo.db[cls.mongo_collection].find({'contributor_id': contributor_id}).sort("created_at", -1)
        return MongoContributorExportSchema(many=True).load(raw).data

    @classmethod
    def get_last(cls, contributor_id):
        if not contributor_id:
            return None
        raw = mongo.db[cls.mongo_collection].find({'contributor_id': contributor_id}).sort("created_at", -1).limit(1)
        return MongoContributorExportSchema(many=True).load(raw).data


class MongoContributorExportSchema(Schema):
    id = fields.String(required=True, load_from='_id', dump_to='_id')
    contributor_id = fields.String(required=True)
    gridfs_id = fields.String(required=True)
    created_at = fields.DateTime(required=True)
    data_sources = fields.List(fields.String())


class CoverageExport(object):
    mongo_collection = 'coverage_exports'

    def __init__(self, coverage_id, gridfs_id, contributors=None):
        self.id = str(uuid.uuid4())
        self.coverage_id = coverage_id
        self.gridfs_id = gridfs_id
        self.created_at = datetime.utcnow()
        self.contributors = [] if contributors is None else contributors

    def save(self):
        raw = MongoCoverageExportSchema().dump(self).data
        mongo.db[self.mongo_collection].insert_one(raw)

    @classmethod
    def get(cls, coverage_id):
        if not coverage_id:
            return None
        raw = mongo.db[cls.mongo_collection].find({'coverage_id': coverage_id}).sort("created_at", -1)
        return MongoCoverageExportSchema(many=True).load(raw).data

    @classmethod
    def get_last(cls, coverage_id):
        if not coverage_id:
            return None
        raw = mongo.db[cls.mongo_collection].find({'coverage_id': coverage_id}).sort("created_at", -1).limit(1)
        return MongoCoverageExportSchema(many=True).load(raw).data

class MongoCoverageExportSchema(Schema):
    id = fields.String(required=True, load_from='_id', dump_to='_id')
    coverage_id = fields.String(required=True)
    gridfs_id = fields.String(required=True)
    created_at = fields.DateTime(required=True)
    contributors = fields.List(fields.String())
