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
from abc import ABCMeta
from io import IOBase
from gridfs import GridOut
from tartare import mongo
from marshmallow import Schema, post_load, utils,  fields
from tartare import app
from tartare.helper import to_doted_notation, get_values_by_key
from tartare.core.gridfs_handler import GridFsHandler
import pymongo
import uuid
from datetime import datetime
from datetime import date
import logging
from typing import Optional, List, Union, Dict, Type
from tartare.core.constants import DATA_FORMAT_VALUES


@app.before_first_request
def init_mongo() -> None:
    mongo.db['contributors'].create_index("data_prefix", unique=True)
    mongo.db['contributors'].create_index([("data_sources.id", pymongo.DESCENDING)], unique=True, sparse=True)


class DataFormat(fields.Field):

    """A DataFormat field.
    """

    default_error_messages = {
        'invalid': 'data_format not in possible values {values}.'.format(values=DATA_FORMAT_VALUES)
    }

    def _serialize(self, value: str, attr: str, obj: 'DataSource') -> str:
        if value in DATA_FORMAT_VALUES:
            return utils.ensure_text_type(value)
        else:
            self.fail('invalid')

    def _deserialize(self, value: str, attr: str, data: dict) -> str:
        if value in DATA_FORMAT_VALUES:
            return utils.ensure_text_type(value)
        else:
            self.fail('invalid')

class PreProcessContainer(metaclass=ABCMeta):
    mongo_collection = ''
    label = ''

    def __init__(self, preprocesses: List['PreProcess'] = None) -> None:
        self.preprocesses = [] if preprocesses is None else preprocesses

    @classmethod
    def get(cls, contributor_id: str) -> Union['Contributor', 'Coverage']:
        pass


class Platform(object):
    def __init__(self, protocol: str, type: str, url: str, options: dict=None, sequence: Optional[int]=0) -> None:
        self.type = type
        self.protocol = protocol
        self.url = url
        self.options = {} if options is None else options
        self.sequence = sequence


class Environment(object):
    def __init__(self, name: str=None, current_ntfs_id: str=None, publication_platforms: List[Platform]=None,
                 sequence: Optional[int]=0) -> None:
        self.name = name
        self.current_ntfs_id = current_ntfs_id
        self.publication_platforms = publication_platforms if publication_platforms else []
        self.sequence = sequence


class ValidityPeriod(object):
    def __init__(self, start_date: date, end_date: date) -> None:
        self.start_date = start_date
        self.end_date = end_date


class ContributorExportDataSource(object):
    def __init__(self, data_source_id: str=None, gridfs_id: str=None, validity_period: ValidityPeriod=None) -> None:
        self.data_source_id = data_source_id
        self.validity_period = validity_period
        self.gridfs_id = gridfs_id


class License(object):
    def __init__(self, name: str = app.config.get('DEFAULT_LICENSE_NAME'),
                 url: str = app.config.get('DEFAULT_LICENSE_URL')) -> None:
        self.name = name
        self.url = url


class DataSource(object):
    def __init__(self, id: Optional[str]=None, name: Optional[str]=None,
                 data_format: Optional[str]="gtfs",
                 input: Optional[dict]=None, license: Optional[License]=None) -> None:
        self.id = id if id else str(uuid.uuid4())
        self.name = name
        self.data_format = data_format
        self.input = {} if not input else input
        self.license = license if license else License()

    @classmethod
    def get_number_of_historical(cls, data_source_id: str) -> int:
        data_sources = cls.get(data_source_id=data_source_id)
        if not data_sources:
            raise ValueError("Unknown data source id {}.".format(data_source_id))
        return app.config.get('HISTORICAL', {}).get(data_sources[0].data_format, 3)

    def save(self, contributor_id: str) -> None:
        contributor = get_contributor(contributor_id)
        if self.id in [ds.id for ds in contributor.data_sources]:
            raise ValueError("Duplicate data_source id '{}'".format(self.id))
        contributor.data_sources.append(self)
        raw_contrib = MongoContributorSchema().dump(contributor).data
        mongo.db[Contributor.mongo_collection].find_one_and_replace({'_id': contributor.id}, raw_contrib)

    @classmethod
    def get(cls, contributor_id: str=None, data_source_id: str=None) -> Optional[List['DataSource']]:
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
    def delete(cls, contributor_id: str, data_source_id: str = None) -> int:
        if data_source_id is None:
            raise ValueError('A data_source id is required')
        contributor = get_contributor(contributor_id)
        nb_delete = len([ds for ds in contributor.data_sources if ds.id == data_source_id])
        contributor.data_sources = [ds for ds in contributor.data_sources if ds.id != data_source_id]
        raw_contrib = MongoContributorSchema().dump(contributor).data
        mongo.db[Contributor.mongo_collection].find_one_and_replace({'_id': contributor.id}, raw_contrib)
        return nb_delete

    @classmethod
    def update(cls, contributor_id: str, data_source_id: str = None, dataset: dict = None) -> 'DataSource':
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

        return cls.get(contributor_id, data_source_id)[0]

    @classmethod
    def is_type_data_format(cls, data_source_id: str, data_format: str) -> bool:
        data_sources = cls.get(data_source_id=data_source_id)
        if not data_sources:
            False
        else:
            return data_sources[0].data_format == data_format


class GenericPreProcess(object):
    def __init__(self, id: Optional[str]=None, type: Optional[str]=None, params: Optional[dict]=None,
                 sequence: Optional[int]=0, data_source_ids: Optional[List[str]]=None) -> None:
        self.id = str(uuid.uuid4()) if not id else id
        self.sequence = sequence
        self.data_source_ids = data_source_ids if data_source_ids else []
        self.params = params if params else {}
        self.type = type

    def save_data(self, class_name: Type[PreProcessContainer],
                  mongo_schema: Type['MongoPreProcessContainerSchema'], object_id: str,
                  ref_model_object: 'PreProcess') -> None:
        data = class_name.get(object_id)
        if data is None:
            raise ValueError('Bad {} {}'.format(class_name.label, object_id))
        if self.id in [p.id for p in data.preprocesses]:
            raise ValueError("Duplicate PreProcess id '{}'".format(self.id))

        data.preprocesses.append(ref_model_object)
        raw_contrib = mongo_schema().dump(data).data
        mongo.db[class_name.mongo_collection].find_one_and_replace({'_id': data.id}, raw_contrib)

    @classmethod
    def get_data(cls, class_name: Type[PreProcessContainer],
                 mongo_schema: Type['MongoPreProcessContainerSchema'], object_id: str,
                 preprocess_id: str) -> Optional[List['PreProcess']]:
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
    def delete_data(cls, class_name: Type[PreProcessContainer],
                    mongo_schema: Type['MongoPreProcessContainerSchema'], object_id: str,
                    preprocess_id: str) -> int:
        data = class_name.get(object_id)
        if data is None:
            raise ValueError('Bad {} {}'.format(class_name.label, object_id))

        nb_delete = len([p for p in data.preprocesses if p.id == preprocess_id])
        data.preprocesses = [p for p in data.preprocesses if p.id != preprocess_id]
        raw_contrib = mongo_schema().dump(data).data
        mongo.db[class_name.mongo_collection].find_one_and_replace({'_id': data.id}, raw_contrib)
        return nb_delete

    @classmethod
    def update_data(cls, class_name: Type[PreProcessContainer],
                    mongo_schema: Type['MongoPreProcessContainerSchema'], object_id: str,
                    preprocess_id: str, preprocess: Optional[dict] = None) -> Optional[List['PreProcess']]:
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
    def save(self, contributor_id: Optional[str]=None, coverage_id: Optional[str]=None) -> None:
        if not any([coverage_id, contributor_id]):
            raise ValueError('Bad arguments.')
        # self passed as 4th argument is child object from GenericPreProcess.save_data method point of vue
        # so it's the one that will need to be saved as a PreProcess
        if contributor_id:
            self.save_data(Contributor, MongoContributorSchema, contributor_id, self)
        if coverage_id:
            self.save_data(Coverage, MongoCoverageSchema, coverage_id, self)

    @classmethod
    def get(cls, preprocess_id: Optional[str]=None, contributor_id: Optional[str]=None,
            coverage_id: Optional[str]=None) -> Optional[List['PreProcess']]:
        if not any([coverage_id, contributor_id]):
            raise ValueError('Bad arguments.')
        if contributor_id:
            return cls.get_data(Contributor, MongoContributorSchema, contributor_id, preprocess_id)
        if coverage_id:
            return cls.get_data(Coverage, MongoCoverageSchema, coverage_id, preprocess_id)

    @classmethod
    def delete(cls, preprocess_id: str, contributor_id: Optional[str]=None, coverage_id: Optional[str]=None) -> int:
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
               preprocess: Optional[dict]=None) -> Optional[List['PreProcess']]:
        if preprocess_id is None:
            raise ValueError('A PreProcess id is required')

        if not any([coverage_id, contributor_id]):
            raise ValueError('Bad arguments.')

        if contributor_id:
            return cls.update_data(Contributor, MongoContributorSchema, contributor_id, preprocess_id, preprocess)
        if coverage_id:
            return cls.update_data(Coverage, MongoCoverageSchema, coverage_id, preprocess_id, preprocess)


class Contributor(PreProcessContainer):
    mongo_collection = 'contributors'
    label = 'Contributor'

    def __init__(self, id: str, name: str, data_prefix: str, data_sources: List[DataSource]=None,
                 preprocesses: List[PreProcess]=None) -> None:
        super(Contributor, self).__init__(preprocesses)
        self.id = id
        self.name = name
        self.data_prefix = data_prefix
        self.data_sources = [] if data_sources is None else data_sources

    def save(self) -> None:
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
        return MongoContributorSchema(many=True, strict=True).load(raw).data

    @classmethod
    def all(cls) -> List['Contributor']:
        return cls.find(filter={})

    @classmethod
    def update(cls, contributor_id: str = None, dataset: dict = None) -> Optional['Contributor']:
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


class Coverage(PreProcessContainer):
    mongo_collection = 'coverages'
    label = 'Coverage'

    def __init__(self, id: str, name: str, environments: Dict[str, Environment] = None, grid_calendars_id: str = None,
                 contributors: List[str] = None, license: License = None,
                 preprocesses: List[PreProcess] = None) -> None:
        super(Coverage, self).__init__(preprocesses)
        self.id = id
        self.name = name
        self.environments = {} if environments is None else environments
        self.grid_calendars_id = grid_calendars_id
        self.contributors = [] if contributors is None else contributors
        self.license = license if license else License()

    def save_grid_calendars(self, file: Union[str, bytes, IOBase, GridOut]) -> None:
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

    def save(self) -> None:
        raw = MongoCoverageSchema(strict=True).dump(self).data
        mongo.db[self.mongo_collection].insert_one(raw)

    @classmethod
    def get(cls, coverage_id: str = None) -> 'Coverage':
        raw = mongo.db[cls.mongo_collection].find_one({'_id': coverage_id})
        if raw is None:
            return None

        return MongoCoverageSchema(strict=True).load(raw).data

    @classmethod
    def delete(cls, coverage_id: str = None) -> int:
        raw = mongo.db[cls.mongo_collection].delete_one({'_id': coverage_id})
        return raw.deleted_count

    @classmethod
    def find(cls, filter: dict) -> List['Coverage']:
        raw = mongo.db[cls.mongo_collection].find(filter)
        return MongoCoverageSchema(many=True, strict=True).load(raw).data

    @classmethod
    def all(cls) -> List['Coverage']:
        return cls.find(filter={})

    @classmethod
    def update(cls, coverage_id: str = None, dataset: dict = None) -> 'Coverage':
        # we have to use "doted notation' to only update some fields of a nested object
        tmp_dataset = dataset if dataset else {}
        raw = mongo.db[cls.mongo_collection].update_one({'_id': coverage_id}, {'$set': to_doted_notation(tmp_dataset)})
        if raw.matched_count == 0:
            return None

        return cls.get(coverage_id)

    def save_ntfs(self, environment_type: str, file: Union[str, bytes, IOBase, GridOut]) -> None:
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

    def add_contributor(self, contributor: Contributor) -> None:
        self.contributors.append(contributor.id)
        self.update(self.id, {"contributors": self.contributors})

    def remove_contributor(self, contributor_id: str) -> None:
        if contributor_id in self.contributors:
            self.contributors.remove(contributor_id)
            self.update(self.id, {"contributors": self.contributors})


class MongoValidityPeriodSchema(Schema):
    start_date = fields.Date(required=True)
    end_date = fields.Date(required=True)

    @post_load
    def make_validityperiod(self, data: dict) -> ValidityPeriod:
        return ValidityPeriod(**data)


class MongoContributorExportDataSourceSchema(Schema):
    data_source_id = fields.String(required=True)
    gridfs_id = fields.String(required=True)
    validity_period = fields.Nested(MongoValidityPeriodSchema)

    @post_load
    def make_contributorexportdatasource(self, data: dict) -> ContributorExportDataSource:
        return ContributorExportDataSource(**data)


class MongoPlatformSchema(Schema):
    type = fields.String(required=True)
    protocol = fields.String(required=True)
    sequence = fields.Integer(required=True)
    url = fields.String(required=True)
    options = fields.Dict(required=False)

    @post_load
    def make_platform(self, data: dict) -> Platform:
        return Platform(**data)


class MongoEnvironmentSchema(Schema):
    name = fields.String(required=True)
    sequence = fields.Integer(required=True)
    current_ntfs_id = fields.String(allow_none=True)
    publication_platforms = fields.Nested(MongoPlatformSchema, many=True)

    @post_load
    def make_environment(self, data: dict) -> Environment:
        return Environment(**data)


class MongoEnvironmentListSchema(Schema):
    production = fields.Nested(MongoEnvironmentSchema, allow_none=True)
    preproduction = fields.Nested(MongoEnvironmentSchema, allow_none=True)
    integration = fields.Nested(MongoEnvironmentSchema, allow_none=True)

    @post_load
    def remove_none(self, data: dict) -> dict:
        # We don't want to keep removed environments
        return {key: value for key, value in data.items() if value is not None}


class Historisable(object):
    mongo_collection = ''

    def get_all_before_n_last(self, n: int, filter: dict) -> List[dict]:
        cursor = mongo.db[self.mongo_collection] \
            .find(filter) \
            .sort("created_at", -1) \
            .skip(n)

        return list(cursor)

    @classmethod
    def delete_many(cls, ids: List[str]) -> int:
        delete_result = mongo.db[cls.mongo_collection].delete_many({
            '_id': {
                '$in': ids
            }
        })

        return delete_result.deleted_count

    def keep_historical(self, num: int, filter: dict) -> None:
        """Keep only `num` data sources fetched and GridFS for the contributor

        Args:
            num (int): The number of data sources fetched you want to keep
        """
        old_rows = self.get_all_before_n_last(num, filter)

        if old_rows:
            # Delete old data_sources_fetched
            num_deleted = self.delete_many([row.get('_id') for row in old_rows])
            # Delete all associated gridFS
            if num_deleted:
                gridfs_ids = [] # type: List[str]
                get_values_by_key(old_rows, gridfs_ids)
                for gridf_ids in gridfs_ids:
                    GridFsHandler().delete_file_from_gridfs(gridf_ids)


class DataSourceFetched(Historisable):
    mongo_collection = 'data_source_fetched'

    def __init__(self, contributor_id: str, data_source_id: str,
                 validity_period: Optional[ValidityPeriod]=None, gridfs_id: str=None,
                 created_at: datetime=None, id: str=None) -> None:
        self.id = id if id else str(uuid.uuid4())
        self.data_source_id = data_source_id
        self.contributor_id = contributor_id
        self.gridfs_id = gridfs_id
        self.created_at = created_at if created_at else datetime.utcnow()
        self.validity_period = validity_period

    def save(self) -> None:
        raw = MongoDataSourceFetchedSchema().dump(self).data
        mongo.db[self.mongo_collection].insert_one(raw)

        self.keep_historical(DataSource.get_number_of_historical(self.data_source_id),
                             {'contributor_id': self.contributor_id, 'data_source_id': self.data_source_id})

    @classmethod
    def get_last(cls, contributor_id: str, data_source_id: str) -> Optional['DataSourceFetched']:
        if not contributor_id:
            return None
        where = {
            'contributor_id': contributor_id,
            'data_source_id': data_source_id
        }
        raw = mongo.db[cls.mongo_collection].find(where).sort("created_at", -1).limit(1)
        lasts = MongoDataSourceFetchedSchema(many=True, strict=True).load(raw).data
        return lasts[0] if lasts else None

    def get_md5(self) -> str:
        if not self.gridfs_id:
            return None
        file = GridFsHandler().get_file_from_gridfs(self.gridfs_id)
        return file.md5

    def save_dataset(self, tmp_file: Union[str, bytes, int], filename: str) -> None:
        with open(tmp_file, 'rb') as file:
            self.gridfs_id = GridFsHandler().save_file_in_gridfs(file, filename=filename,
                                                                 contributor_id=self.contributor_id)


class MongoDataSourceLicenseSchema(Schema):
    name = fields.String(required=False)
    url = fields.String(required=False)

    @post_load
    def build_license(self, data: dict) -> License:
        return License(**data)


class MongoDataSourceFetchedSchema(Schema):
    id = fields.String(required=True, load_from='_id', dump_to='_id')
    data_source_id = fields.String(required=True)
    contributor_id = fields.String(required=True)
    gridfs_id = fields.String(required=False)
    created_at = fields.DateTime(required=False)
    validity_period = fields.Nested(MongoValidityPeriodSchema, required=False, allow_none=True)

    @post_load
    def build_data_source_fetched(self, data: dict) -> DataSourceFetched:
        return DataSourceFetched(**data)


class MongoDataSourceSchema(Schema):
    id = fields.String(required=True)
    name = fields.String(required=True)
    data_format = DataFormat()
    license = fields.Nested(MongoDataSourceLicenseSchema, allow_none=False)
    input = fields.Dict(required=True)

    @post_load
    def build_data_source(self, data: dict) -> DataSource:
        return DataSource(**data)


class MongoPreProcessSchema(Schema):
    id = fields.String(required=True)
    sequence = fields.Integer(required=True)
    type = fields.String(required=True)
    params = fields.Dict(required=False)
    data_source_ids = fields.List(fields.String(), required=False)

    @post_load
    def build_data_source(self, data: dict) -> PreProcess:
        return PreProcess(**data)


class MongoPreProcessContainerSchema(Schema):
    pass


class MongoCoverageSchema(MongoPreProcessContainerSchema):
    id = fields.String(required=True, load_from='_id', dump_to='_id')
    name = fields.String(required=True)
    environments = fields.Nested(MongoEnvironmentListSchema)
    grid_calendars_id = fields.String(allow_none=True)
    contributors = fields.List(fields.String())
    license = fields.Nested(MongoDataSourceLicenseSchema, allow_none=True)
    preprocesses = fields.Nested(MongoPreProcessSchema, many=True, required=False, allow_none=False)

    @post_load
    def make_coverage(self, data: dict) -> Coverage:
        return Coverage(**data)


class MongoContributorSchema(MongoPreProcessContainerSchema):
    id = fields.String(required=True, load_from='_id', dump_to='_id')
    name = fields.String(required=True)
    data_prefix = fields.String(required=True)
    data_sources = fields.Nested(MongoDataSourceSchema, many=True, required=False)
    preprocesses = fields.Nested(MongoPreProcessSchema, many=True, required=False)

    @post_load
    def make_contributor(self, data: dict) -> Contributor:
        return Contributor(**data)


class Job(object):
    mongo_collection = 'jobs'

    def __init__(self, action_type: str, contributor_id: str = None, coverage_id: str = None, state: str = 'pending',
                 step: str = None, id: str = None, started_at: datetime = None, updated_at: Optional[datetime] = None,
                 error_message: str = "") -> None:
        self.id = id if id else str(uuid.uuid4())
        self.action_type = action_type
        self.contributor_id = contributor_id
        self.coverage_id = coverage_id
        self.step = step
        # 'pending', 'running', 'done', 'failed'
        self.state = state
        self.error_message = error_message
        self.started_at = started_at if started_at else datetime.utcnow()
        self.updated_at = updated_at if updated_at else self.started_at

    def save(self) -> None:
        raw = MongoJobSchema().dump(self).data
        mongo.db[self.mongo_collection].insert_one(raw)

    @classmethod
    def find(cls, filter: dict) -> List['Job']:
        raw = mongo.db[cls.mongo_collection].find(filter)
        return MongoJobSchema(many=True).load(raw).data

    @classmethod
    def get_some(cls, contributor_id: str = None, coverage_id: str = None) -> List['Job']:
        find_filter = {}
        if contributor_id:
            find_filter.update({'contributor_id': contributor_id})
        if coverage_id:
            find_filter.update({'coverage_id': coverage_id})
        return cls.find(filter=find_filter)

    @classmethod
    def get_one(cls, job_id: str) -> Optional['Job']:
        raw = mongo.db[cls.mongo_collection].find_one({'_id': job_id})
        if not raw:
            return None
        return MongoJobSchema(strict=True).load(raw).data

    @classmethod
    def update(cls, job_id: str, state: str = None, step: str = None, error_message: str = None) -> Optional['Job']:
        logger = logging.getLogger(__name__)
        if not job_id:
            logger.error('job_id cannot be empty')
            return None
        job = cls.get_one(job_id)
        if not job:
            logger.error("Cannot find job to update %s", job_id)
            return None
        if state is not None:
            job.state = state
        if step is not None:
            job.step = step
        if error_message is not None:
            job.error_message = error_message

        job.updated_at = datetime.utcnow()

        raw = mongo.db[cls.mongo_collection].update_one({'_id': job_id}, {'$set': MongoJobSchema().dump(job).data})
        if raw.matched_count == 0:
            return None
        return job


class MongoJobSchema(Schema):
    id = fields.String(required=True, load_from='_id', dump_to='_id')
    action_type = fields.String(required=True)
    contributor_id = fields.String(required=False, allow_none=True)
    coverage_id = fields.String(required=False, allow_none=True)
    state = fields.String(required=True)
    step = fields.String(required=False, allow_none=True)
    started_at = fields.DateTime(required=False)
    updated_at = fields.DateTime(required=False)
    error_message = fields.String(required=False)

    @post_load
    def make(self, data: dict) -> Job:
        return Job(**data)


class ContributorExport(Historisable):
    mongo_collection = 'contributor_exports'

    def __init__(self, contributor_id: str,
                 gridfs_id: str,
                 validity_period: ValidityPeriod,
                 data_sources: List[ContributorExportDataSource]=None,
                 id: str=None,
                 created_at: datetime=None) -> None:
        self.id = id if id else str(uuid.uuid4())
        self.contributor_id = contributor_id
        self.gridfs_id = gridfs_id
        self.created_at = created_at if created_at else datetime.utcnow()
        self.validity_period = validity_period
        self.data_sources = [] if data_sources is None else data_sources

    def save(self) -> None:
        raw = MongoContributorExportSchema().dump(self).data
        mongo.db[self.mongo_collection].insert_one(raw)

        self.keep_historical(3, {'contributor_id': self.contributor_id})

    @classmethod
    def get(cls, contributor_id: str) -> Optional[List['ContributorExport']]:
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
    def make_contributor_export(self, data: dict) -> ContributorExport:
        return ContributorExport(**data)


class CoverageExportContributor(object):
    def __init__(self, contributor_id: str, validity_period: ValidityPeriod = None,
                 data_sources: List[ContributorExportDataSource] = None) -> None:
        self.contributor_id = contributor_id
        self.validity_period = validity_period
        self.data_sources = [] if data_sources is None else data_sources


class MongoCoverageExportContributorSchema(Schema):
    contributor_id = fields.String(required=True)
    validity_period = fields.Nested(MongoValidityPeriodSchema)
    data_sources = fields.Nested(MongoContributorExportDataSourceSchema, many=True)

    @post_load
    def make_coverageexportcontributor(self, data: dict) -> CoverageExportContributor:
        return CoverageExportContributor(**data)


class CoverageExport(Historisable):
    mongo_collection = 'coverage_exports'

    def __init__(self, coverage_id: str, gridfs_id: str, validity_period: ValidityPeriod,
                 contributors: List[CoverageExportContributor] = None, id: str = None, created_at: str = None) -> None:
        self.id = id if id else str(uuid.uuid4())
        self.coverage_id = coverage_id
        self.gridfs_id = gridfs_id
        self.validity_period = validity_period
        self.created_at = created_at if created_at else datetime.utcnow()
        self.contributors = [] if contributors is None else contributors

    def save(self) -> None:
        raw = MongoCoverageExportSchema().dump(self).data
        mongo.db[self.mongo_collection].insert_one(raw)

        self.keep_historical(3, {'coverage_id': self.coverage_id})

    @classmethod
    def get(cls, coverage_id: str) -> Optional['CoverageExport']:
        if not coverage_id:
            return None
        raw = mongo.db[cls.mongo_collection].find({'coverage_id': coverage_id}).sort("created_at", -1)
        return MongoCoverageExportSchema(many=True).load(raw).data

    @classmethod
    def get_last(cls, coverage_id: str) -> Optional['CoverageExport']:
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
    def make_coverage_export(self, data: dict) -> CoverageExport:
        return CoverageExport(**data)
