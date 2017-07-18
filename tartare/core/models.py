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
from io import IOBase

from gridfs import GridOut

from tartare import mongo
from marshmallow import Schema, fields, post_load
from tartare import app
from tartare.helper import to_doted_notation
from tartare.core.gridfs_handler import GridFsHandler
import pymongo
import uuid
from datetime import datetime
import logging
from typing import Optional, List, Union


@app.before_first_request
def init_mongo():
    mongo.db['contributors'].create_index("data_prefix", unique=True)
    mongo.db['contributors'].create_index([("data_sources.id", pymongo.DESCENDING)], unique=True, sparse=True)


class Platform(object):
    def __init__(self, protocol: str, type: str, url: str, options: dict=None):
        self.type = type
        self.protocol = protocol
        self.url = url
        self.options = {} if options is None else options


class Environment(object):
    def __init__(self, name: str=None, current_ntfs_id: str=None, publication_platforms: List[Platform]=None):
        self.name = name
        self.current_ntfs_id = current_ntfs_id
        self.publication_platforms = publication_platforms if publication_platforms else []


class ValidityPeriod(object):
    def __init__(self, start_date: datetime, end_date: datetime):
        self.start_date = start_date
        self.end_date = end_date


class ContributorExportDataSource(object):
    def __init__(self, data_source_id: str=None, validity_period: ValidityPeriod=None):
        self.data_source_id = data_source_id
        self.validity_period = validity_period


class License(object):
    def __init__(self, name: str = app.config.get('DEFAULT_LICENSE_NAME'),
                 url: str = app.config.get('DEFAULT_LICENSE_URL')):
        self.name = name
        self.url = url


class DataSource(object):
    def __init__(self, id: Optional[str]=None, name: Optional[str]=None, data_format: Optional[str]="gtfs",
                 input: Optional[dict]=None, license: Optional[License]=None):
        self.id = id if id else str(uuid.uuid4())
        self.name = name
        self.data_format = data_format
        self.input = {} if not input else input
        self.license = license if license else License()

    def save(self, contributor_id: str):
        contributor = get_contributor(contributor_id)
        if self.id in [ds.id for ds in contributor.data_sources]:
            raise ValueError("Duplicate data_source id '{}'".format(self.id))
        contributor.data_sources.append(self)
        raw_contrib = MongoContributorSchema().dump(contributor).data
        mongo.db[Contributor.mongo_collection].find_one_and_replace({'_id': contributor.id}, raw_contrib)

    @classmethod
    def get(cls, contributor_id: str=None, data_source_id: str=None) -> 'DataSource':
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
    def delete(cls, contributor_id: str, data_source_id: str=None) -> int:
        if data_source_id is None:
            raise ValueError('A data_source id is required')
        contributor = get_contributor(contributor_id)
        nb_delete = len([ds for ds in contributor.data_sources if ds.id == data_source_id])
        contributor.data_sources = [ds for ds in contributor.data_sources if ds.id != data_source_id]
        raw_contrib = MongoContributorSchema().dump(contributor).data
        mongo.db[Contributor.mongo_collection].find_one_and_replace({'_id': contributor.id}, raw_contrib)
        return nb_delete

    @classmethod
    def update(cls, contributor_id: str, data_source_id: str=None, dataset: dict=None) -> 'DataSource':
        tmp_dataset = dataset if dataset else {}
        if data_source_id is None:
            raise ValueError('A data_source id is required')
        if not [ds for ds in get_contributor(contributor_id).data_sources if ds.id == data_source_id]:
            raise ValueError("No data_source id {} exists in contributor with id {}"
                             .format(contributor_id, data_source_id))
        if 'id' in tmp_dataset and tmp_dataset['id'] != data_source_id:
            raise ValueError("Id from request {} doesn't match id from url {}"
                             .format(tmp_dataset['id'], data_source_id))

        # `$` acts as a placeholder of the first match in the list
        contrib_dataset = {'data_sources': {'$': tmp_dataset}}
        raw = mongo.db[Contributor.mongo_collection].update_one({'data_sources.id': data_source_id},
                                                                {'$set': to_doted_notation(contrib_dataset)})
        if raw.matched_count == 0:
            return None

        return cls.get(contributor_id, data_source_id)


class GenericPreProcess(object):
    def __init__(self, id: Optional[str]=None, type: Optional[str]=None, params: Optional[dict]=None,
                 sequence: Optional[int]=0):
        self.id = str(uuid.uuid4()) if not id else id
        self.sequence = sequence
        self.params = params if params else {}
        self.type = type

    def save_data(self, class_name: Union['Contributor', 'Coverage'], mongo_schema: type, object_id: str):
        data = class_name.get(object_id)
        if data is None:
            raise ValueError('Bad {} {}'.format(class_name.label, object_id))
        if self.id in [p.id for p in data.preprocesses]:
            raise ValueError("Duplicate PreProcess id '{}'".format(self.id))

        data.preprocesses.append(self)
        raw_contrib = mongo_schema().dump(data).data
        mongo.db[class_name.mongo_collection].find_one_and_replace({'_id': data.id}, raw_contrib)

    @classmethod
    def get_data(cls, class_name: Union['Contributor', 'Coverage'],
                 mongo_schema: Union['MongoContributorSchema', 'MongoCoverageSchema'], object_id,
                 preprocess_id) -> 'PreProcess':
        if object_id is not None:
            data = class_name.get(object_id)
            if data is None:
                raise ValueError('Bad {} {}'.format(class_name.label, object_id))
        elif preprocess_id is not None:
            raw = mongo.db[class_name.mongo_collection].find_one({'preprocesses.id': preprocess_id})
            if raw is None:
                return None
            data = mongo_schema(strict=True).load(raw).data
        else:
            raise ValueError("To get preprocess you must provide a contributor_id or a preprocess_id")

        preprocesses = data.preprocesses

        if preprocess_id is None:
            return preprocesses
        p = next((p for p in preprocesses if p.id == preprocess_id), None)
        return [p] if p else []

    @classmethod
    def delete_data(cls, class_name: Union['Contributor', 'Coverage'],
                    mongo_schema: Union['MongoContributorSchema', 'MongoCoverageSchema'], object_id,
                    preprocess_id) -> int:
        data = class_name.get(object_id)
        if data is None:
            raise ValueError('Bad {} {}'.format(class_name.label, object_id))

        nb_delete = len([p for p in data.preprocesses if p.id == preprocess_id])
        data.preprocesses = [p for p in data.preprocesses if p.id != preprocess_id]
        raw_contrib = mongo_schema().dump(data).data
        mongo.db[class_name.mongo_collection].find_one_and_replace({'_id': data.id}, raw_contrib)
        return nb_delete

    @classmethod
    def update_data(cls, class_name: Union['Contributor', 'Coverage'],
                    mongo_schema: Union['MongoContributorSchema', 'MongoCoverageSchema'], object_id, preprocess_id,
                    preprocess: Optional[dict] = None) -> 'PreProcess':
        data = class_name.get(object_id)
        if not data:
            raise ValueError('Bad {} {}'.format(class_name.label, object_id))

        if not [ps for ps in data.preprocesses if ps.id == preprocess_id]:
            raise ValueError("No preprocesses id {} exists in {} with id {}"
                             .format(object_id, class_name.label, preprocess_id))
        if 'id' in preprocess and preprocess['id'] != preprocess_id:
            raise ValueError("Id from request {} doesn't match id from url {}"
                             .format(preprocess['id'], preprocess_id))

        preprocess['id'] = preprocess_id
        raw = mongo.db[class_name.mongo_collection].update_one({'preprocesses.id': preprocess_id},
                                                               {'$set': {'preprocesses.$': preprocess}})
        if raw.matched_count == 0:
            return None

        return cls.get_data(class_name, mongo_schema, object_id, preprocess_id)


class PreProcess(GenericPreProcess):
    def save(self, contributor_id: Optional[str]=None, coverage_id: Optional[str]=None):
        if not any([coverage_id, contributor_id]):
            raise ValueError('Bad arguments.')
        if contributor_id:
            self.save_data(Contributor, MongoContributorSchema, contributor_id)
        if coverage_id:
            self.save_data(Coverage, MongoCoverageSchema, coverage_id)

    @classmethod
    def get(cls, preprocess_id: Optional[str]=None, contributor_id: Optional[str]=None,
            coverage_id: Optional[str]=None) -> GenericPreProcess:
        if not any([coverage_id, contributor_id]):
            raise ValueError('Bad arguments.')
        if contributor_id:
            return cls.get_data(Contributor, MongoContributorSchema, contributor_id, preprocess_id)
        if coverage_id:
            return cls.get_data(Coverage, MongoCoverageSchema, coverage_id, preprocess_id)

    @classmethod
    def delete(cls, preprocess_id: str, contributor_id: Optional[str]=None, coverage_id: Optional[str]=None):
        if preprocess_id is None:
            raise ValueError('A preprocess id is required')
        if not any([coverage_id, contributor_id]):
            raise ValueError('Bad arguments.')
        if contributor_id:
            return cls.delete_data(Contributor, MongoContributorSchema, contributor_id, preprocess_id)
        if coverage_id:
            return cls.delete_data(Coverage, MongoCoverageSchema, coverage_id, preprocess_id)

    @classmethod
    def update(cls, preprocess_id: str, contributor_id: Optional[str]=None, coverage_id: Optional[str]=None,
               preprocess: Optional[dict]=None):
        if preprocess_id is None:
            raise ValueError('A PreProcess id is required')

        if not any([coverage_id, contributor_id]):
            raise ValueError('Bad arguments.')

        if contributor_id:
            return cls.update_data(Contributor, MongoContributorSchema, contributor_id, preprocess_id, preprocess)
        if coverage_id:
            return cls.update_data(Coverage, MongoCoverageSchema, coverage_id, preprocess_id, preprocess)


class Contributor(object):
    mongo_collection = 'contributors'
    label = 'Contributor'

    def __init__(self, id: str, name: str, data_prefix: str, data_sources: List[DataSource]=None,
                 preprocesses: List[PreProcess]=None):
        self.id = id
        self.name = name
        self.data_prefix = data_prefix
        self.data_sources = [] if data_sources is None else data_sources
        self.preprocesses = [] if preprocesses is None else preprocesses

    def save(self):
        raw = MongoContributorSchema().dump(self).data
        mongo.db[self.mongo_collection].insert_one(raw)

    @classmethod
    def get(cls, contributor_id: str) -> 'Contributor':
        raw = mongo.db[cls.mongo_collection].find_one({'_id': contributor_id})
        if raw is None:
            return None
        return MongoContributorSchema(strict=True).load(raw).data

    @classmethod
    def delete(cls, contributor_id: str) -> int:
        raw = mongo.db[cls.mongo_collection].delete_one({'_id': contributor_id})
        return raw.deleted_count

    @classmethod
    def find(cls, filter: dict) -> List['Contributor']:
        raw = mongo.db[cls.mongo_collection].find(filter)
        return MongoContributorSchema(many=True).load(raw).data

    @classmethod
    def all(cls) -> List['Contributor']:
        return cls.find(filter={})

    @classmethod
    def update(cls, contributor_id: str=None, dataset: dict=None) -> Optional['Contributor']:
        tmp_dataset = dataset if dataset else {}
        raw = mongo.db[cls.mongo_collection].update_one({'_id': contributor_id}, {'$set': tmp_dataset})
        if raw.matched_count == 0:
            return None

        return cls.get(contributor_id)


def get_contributor(contributor_id: str) -> Contributor:
    contributor = Contributor.get(contributor_id)
    if contributor is None:
        raise ValueError('Bad contributor {}'.format(contributor_id))
    return contributor


class Coverage(object):
    mongo_collection = 'coverages'
    label = 'Coverage'

    def __init__(self, id: str, name: str, environments: List[Environment]=None, grid_calendars_id: str=None,
                 contributors: List[Contributor]=None, license: License=None,
                 preprocesses: List[PreProcess]=None):
        self.id = id
        self.name = name
        self.environments = {} if environments is None else environments
        self.grid_calendars_id = grid_calendars_id
        self.contributors = [] if contributors is None else contributors
        self.license = license if license else License()
        self.preprocesses = [] if preprocesses is None else preprocesses

    def save_grid_calendars(self, file: Union[str, bytes, IOBase, GridOut]):
        gridfs_handler = GridFsHandler()
        filename = '{coverage}_calendars.zip'.format(coverage=self.id)
        id = gridfs_handler.save_file_in_gridfs(file, filename=filename, coverage=self.id)
        Coverage.update(self.id, {'grid_calendars_id': id})
        # when we delete the file all process reading it will get invalid data
        # TODO: We will need to implement a better solution
        gridfs_handler.delete_file_from_gridfs(self.grid_calendars_id)
        self.grid_calendars_id = id

    def get_environment(self, environment_id: str) -> Environment:
        return self.environments.get(environment_id)

    def get_grid_calendars(self) -> str:
        if not self.grid_calendars_id:
            return None

        gridfs_handler = GridFsHandler()
        return gridfs_handler.get_file_from_gridfs(self.grid_calendars_id)

    def save(self):
        raw = MongoCoverageSchema().dump(self).data
        mongo.db[self.mongo_collection].insert_one(raw)

    @classmethod
    def get(cls, coverage_id=None) -> 'Coverage':
        raw = mongo.db[cls.mongo_collection].find_one({'_id': coverage_id})
        if raw is None:
            return None

        return MongoCoverageSchema(strict=True).load(raw).data

    @classmethod
    def delete(cls, coverage_id=None):
        raw = mongo.db[cls.mongo_collection].delete_one({'_id': coverage_id})
        return raw.deleted_count

    @classmethod
    def find(cls, filter) -> List['Coverage']:
        raw = mongo.db[cls.mongo_collection].find(filter)
        return MongoCoverageSchema(many=True).load(raw).data

    @classmethod
    def all(cls) -> List['Coverage']:
        return cls.find(filter={})

    @classmethod
    def update(cls, coverage_id: str=None, dataset: dict=None) -> 'Coverage':
        # we have to use "doted notation' to only update some fields of a nested object
        tmp_dataset = dataset if dataset else {}
        raw = mongo.db[cls.mongo_collection].update_one({'_id': coverage_id}, {'$set': to_doted_notation(tmp_dataset)})
        if raw.matched_count == 0:
            return None

        return cls.get(coverage_id)

    def save_ntfs(self, environment_type: str, file: Union[str, bytes, IOBase, GridOut]):
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

    def has_contributor(self, contributor: Contributor) -> bool:
        return contributor.id in self.contributors

    def add_contributor(self, contributor: Contributor):
        self.contributors.append(contributor.id)
        self.update(self.id, {"contributors": self.contributors})

    def remove_contributor(self, contributor_id: str):
        if contributor_id in self.contributors:
            self.contributors.remove(contributor_id)
            self.update(self.id, {"contributors": self.contributors})


class MongoValidityPeriodSchema(Schema):
    start_date = fields.Date(required=True)
    end_date = fields.Date(required=True)

    @post_load
    def make_validityperiod(self, data):
        return ValidityPeriod(**data)


class MongoContributorExportDataSourceSchema(Schema):
    data_source_id = fields.String(required=True)
    validity_period = fields.Nested(MongoValidityPeriodSchema)

    @post_load
    def make_contributorexportdatasource(self, data):
        return ContributorExportDataSource(**data)


class MongoPlatformSchema(Schema):
    type = fields.String(required=True)
    protocol = fields.String(required=True)
    url = fields.String(required=True)
    options = fields.Dict(required=False)

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


class DataSourceFetched(object):
    mongo_collection = 'data_source_fetched'

    def __init__(self, contributor_id: str, data_source_id: str, validity_period: ValidityPeriod, gridfs_id: str=None,
                 created_at: datetime=None):
        self.data_source_id = data_source_id
        self.contributor_id = contributor_id
        self.gridfs_id = gridfs_id
        self.created_at = created_at if created_at else datetime.utcnow()
        self.validity_period = validity_period

    def save(self):
        raw = MongoDataSourceFetchedSchema().dump(self).data
        mongo.db[self.mongo_collection].insert_one(raw)

    @classmethod
    def get_last(cls, contributor_id: str, data_source_id: str) -> Optional['DataSourceFetched']:
        if not contributor_id:
            return None
        where = {
            'contributor_id': contributor_id,
            'data_source_id': data_source_id
        }
        raw = mongo.db[cls.mongo_collection].find(where).sort("created_at", -1).limit(1)
        lasts = MongoDataSourceFetchedSchema(many=True).load(raw).data
        return lasts[0] if lasts else None

    def get_md5(self) -> str:
        if not self.gridfs_id:
            return None
        file = GridFsHandler().get_file_from_gridfs(self.gridfs_id)
        return file.md5

    def save_dataset(self, tmp_file: Union[str, bytes, IOBase, GridOut], filename: str):
        with open(tmp_file, 'rb') as file:
            self.gridfs_id = GridFsHandler().save_file_in_gridfs(file, filename=filename,
                                                                 contributor_id=self.contributor_id)


class MongoDataSourceLicenseSchema(Schema):
    name = fields.String(required=False)
    url = fields.String(required=False)

    @post_load
    def build_license(self, data):
        return License(**data)


class MongoDataSourceFetchedSchema(Schema):
    data_source_id = fields.String(required=True)
    contributor_id = fields.String(required=True)
    gridfs_id = fields.String(required=False)
    created_at = fields.DateTime(required=False)
    validity_period = fields.Nested(MongoValidityPeriodSchema)

    @post_load
    def build_data_source_fetched(self, data):
        return DataSourceFetched(**data)


class MongoDataSourceSchema(Schema):
    id = fields.String(required=True)
    name = fields.String(required=True)
    data_format = fields.String(required=False)
    license = fields.Nested(MongoDataSourceLicenseSchema, allow_none=False)
    input = fields.Dict(required=True)

    @post_load
    def build_data_source(self, data):
        return DataSource(**data)


class MongoPreProcessSchema(Schema):
    id = fields.String(required=True)
    sequence = fields.Integer(required=True)
    type = fields.String(required=True)
    params = fields.Dict(required=False)

    @post_load
    def build_data_source(self, data):
        return PreProcess(**data)


class MongoCoverageSchema(Schema):
    id = fields.String(required=True, load_from='_id', dump_to='_id')
    name = fields.String(required=True)
    environments = fields.Nested(MongoEnvironmentListSchema)
    grid_calendars_id = fields.String(allow_none=True)
    contributors = fields.List(fields.String())
    license = fields.Nested(MongoDataSourceLicenseSchema, allow_none=True)
    preprocesses = fields.Nested(MongoPreProcessSchema, many=True, required=False)

    @post_load
    def make_coverage(self, data):
        return Coverage(**data)


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

    def __init__(self, action_type: str, contributor_id: str=None, coverage_id: str=None, state: str='pending',
                 step: str=None, id: str=None, started_at: datetime=None):
        self.id = id if id else str(uuid.uuid4())
        self.action_type = action_type
        self.contributor_id = contributor_id
        self.coverage_id = coverage_id
        self.step = step
        # 'pending', 'running', 'done', 'failed'
        self.state = state
        self.error_message = ""
        self.started_at = started_at if started_at else datetime.utcnow()
        self.updated_at = None

    def save(self):
        raw = MongoJobSchema().dump(self).data
        mongo.db[self.mongo_collection].insert_one(raw)

    @classmethod
    def find(cls, filter) -> Union[dict, List[dict]]:
        raw = mongo.db[cls.mongo_collection].find(filter)
        return MongoJobSchema(many=True).load(raw).data

    @classmethod
    def get(cls, contributor_id: str=None, coverage_id: str=None, job_id: str=None) -> Union[dict, List[dict]]:
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
    def update(cls, job_id: str, state: str=None, step: str=None, error_message: str=None) -> Optional[dict]:
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
    error_message = fields.String(required=False)


class ContributorExport(object):
    mongo_collection = 'contributor_exports'

    def __init__(self, contributor_id: str,
                 gridfs_id: str,
                 validity_period: ValidityPeriod,
                 data_sources: List[DataSource]=None, id: str=None,
                 created_at=None):
        self.id = id if id else str(uuid.uuid4())
        self.contributor_id = contributor_id
        self.gridfs_id = gridfs_id
        self.created_at = created_at if created_at else datetime.utcnow()
        self.validity_period = validity_period
        self.data_sources = [] if data_sources is None else data_sources

    def save(self):
        raw = MongoContributorExportSchema().dump(self).data
        mongo.db[self.mongo_collection].insert_one(raw)

    @classmethod
    def get(cls, contributor_id: str) -> Optional(List['ContributorExport']):
        if not contributor_id:
            return None
        raw = mongo.db[cls.mongo_collection].find({'contributor_id': contributor_id}).sort("created_at", -1)
        return MongoContributorExportSchema(many=True).load(raw).data

    @classmethod
    def get_last(cls, contributor_id: str) -> Optional['ContributorExport']:
        if not contributor_id:
            return None
        raw = mongo.db[cls.mongo_collection].find({'contributor_id': contributor_id}).sort("created_at", -1).limit(1)
        lasts = MongoContributorExportSchema(many=True).load(raw).data
        return lasts[0] if lasts else None


class MongoContributorExportSchema(Schema):
    id = fields.String(required=True, load_from='_id', dump_to='_id')
    contributor_id = fields.String(required=True)
    gridfs_id = fields.String(required=True)
    created_at = fields.DateTime(required=True)
    validity_period = fields.Nested(MongoValidityPeriodSchema, required=False)
    data_sources = fields.Nested(MongoContributorExportDataSourceSchema, many=True, required=False)

    @post_load
    def make_contributor_export(self, data):
        return ContributorExport(**data)


class CoverageExportContributor(object):
    def __init__(self, contributor_id, validity_period=None, data_sources=None):
        self.contributor_id = contributor_id
        self.validity_period = validity_period
        self.data_sources = [] if data_sources is None else data_sources


class MongoCoverageExportContributorSchema(Schema):
    contributor_id = fields.String(required=True)
    validity_period = fields.Nested(MongoValidityPeriodSchema)
    data_sources = fields.Nested(MongoContributorExportDataSourceSchema, many=True)

    @post_load
    def make_coverageexportcontributor(self, data):
        return CoverageExportContributor(**data)


class CoverageExport(object):
    mongo_collection = 'coverage_exports'

    def __init__(self, coverage_id: str, gridfs_id: str, validity_period: str, contributors: List[Contributor]=None,
                 id: str=None, created_at: str=None):
        self.id = id if id else str(uuid.uuid4())
        self.coverage_id = coverage_id
        self.gridfs_id = gridfs_id
        self.validity_period = validity_period
        self.created_at = created_at if created_at else datetime.utcnow()
        self.contributors = [] if contributors is None else contributors

    def save(self):
        raw = MongoCoverageExportSchema().dump(self).data
        mongo.db[self.mongo_collection].insert_one(raw)

    @classmethod
    def get(cls, coverage_id: str) -> Optional['ContributorExport']:
        if not coverage_id:
            return None
        raw = mongo.db[cls.mongo_collection].find({'coverage_id': coverage_id}).sort("created_at", -1)
        return MongoCoverageExportSchema(many=True).load(raw).data

    @classmethod
    def get_last(cls, coverage_id: str) -> Optional['ContributorExport']:
        if not coverage_id:
            return None
        raw = mongo.db[cls.mongo_collection].find({'coverage_id': coverage_id}).sort("created_at", -1).limit(1)
        lasts = MongoCoverageExportSchema(many=True).load(raw).data
        return lasts[0] if lasts else None


class MongoCoverageExportSchema(Schema):
    id = fields.String(required=True, load_from='_id', dump_to='_id')
    coverage_id = fields.String(required=True)
    gridfs_id = fields.String(required=True)
    created_at = fields.DateTime(required=True)
    validity_period = fields.Nested(MongoValidityPeriodSchema)
    contributors = fields.Nested(MongoCoverageExportContributorSchema, many=True)

    @post_load
    def make_coverage_export(self, data):
        return CoverageExport(**data)
