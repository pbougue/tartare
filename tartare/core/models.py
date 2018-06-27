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
import copy
import logging
import uuid
from abc import ABCMeta
from datetime import date, timedelta
from datetime import datetime
from io import IOBase
from typing import Optional, List, Union, Dict, Type, Any, TypeVar, BinaryIO

import pymongo
import pytz
from marshmallow import Schema, post_load, utils, fields, validates, ValidationError
from marshmallow_oneofschema import OneOfSchema

from tartare import app
from tartare import mongo
from tartare.core.constants import DATA_FORMAT_VALUES, DATA_FORMAT_DEFAULT, \
    DATA_TYPE_DEFAULT, DATA_TYPE_VALUES, DATA_SOURCE_STATUS_NEVER_FETCHED, \
    DATA_SOURCE_STATUS_UPDATED, PLATFORM_TYPE_VALUES, PLATFORM_PROTOCOL_VALUES, \
    DATA_TYPE_GEOGRAPHIC, ACTION_TYPE_DATA_SOURCE_FETCH, DATA_SOURCE_STATUS_UNCHANGED, JOB_STATUSES, \
    JOB_STATUS_PENDING, JOB_STATUS_FAILED, JOB_STATUS_DONE, JOB_STATUS_RUNNING, INPUT_TYPE_COMPUTED, INPUT_TYPE_AUTO, \
    INPUT_TYPE_MANUAL, DATA_SOURCE_STATUS_FETCHING, DATA_SOURCE_STATUS_FAILED
from tartare.core.gridfs_handler import GridFsHandler
from tartare.exceptions import ValidityPeriodException, EntityNotFound, ParameterException, IntegrityException, \
    RuntimeException
from tartare.helper import to_doted_notation, get_values_by_key, get_md5_content_file


@app.before_first_request
def init_mongo() -> None:
    mongo.db['contributors'].create_index("data_prefix", unique=True)
    mongo.db['contributors'].create_index([("data_sources.id", pymongo.DESCENDING)], unique=True, sparse=True)


class ChoiceField(fields.Field):
    def __init__(self, possible_values: List[str], **metadata: dict) -> None:
        super().__init__(**metadata)
        self.possible_values = possible_values

    """
    A Choice field.
    """
    default_error_messages = {
        'invalid': 'choice "{current_value}" not in possible values ({possible_values}).'
    }

    def _serialize(self, value: str, attr: str, _: Any) -> str:
        if value in self.possible_values:
            return utils.ensure_text_type(value)
        else:
            self.fail('invalid', current_value=value, possible_values=', '.join(self.possible_values))

    def _deserialize(self, value: str, attr: str, data: dict) -> str:
        if value in self.possible_values:
            return utils.ensure_text_type(value)
        else:
            self.fail('invalid', current_value=value, possible_values=', '.join(self.possible_values))


class DataFormat(ChoiceField):
    def __init__(self, **metadata: dict) -> None:
        super().__init__(DATA_FORMAT_VALUES, **metadata)


class DataType(ChoiceField):
    def __init__(self, **metadata: dict) -> None:
        super().__init__(DATA_TYPE_VALUES, **metadata)


class PlatformType(ChoiceField):
    def __init__(self, **metadata: Any) -> None:
        super().__init__(PLATFORM_TYPE_VALUES, **metadata)


class PlatformProtocol(ChoiceField):
    def __init__(self, **metadata: Any) -> None:
        super().__init__(PLATFORM_PROTOCOL_VALUES, **metadata)


class JobStatus(ChoiceField):
    def __init__(self, **metadata: Any) -> None:
        super().__init__(JOB_STATUSES, **metadata)


class CoverageType(ChoiceField):
    def __init__(self, **metadata: Any) -> None:
        super().__init__(['navitia.io', 'keolis', 'regional', 'other'], **metadata)


SequenceContainerType = TypeVar('SequenceContainerType', bound='SequenceContainer')


class SequenceContainer(metaclass=ABCMeta):
    def __init__(self, sequence: int) -> None:
        self.sequence = sequence

    @classmethod
    def sort_by_sequence(cls, list_to_sort: List[SequenceContainerType]) -> List[SequenceContainerType]:
        return sorted(list_to_sort, key=lambda sequence_container: sequence_container.sequence)


class DataSourceAndPreProcessContainer(metaclass=ABCMeta):
    mongo_collection = ''
    label = ''

    def __init__(self, preprocesses: List['PreProcess'] = None, data_sources: List['DataSource'] = None) -> None:
        self.preprocesses = [] if preprocesses is None else preprocesses  # type: List['PreProcess']
        self.data_sources = data_sources if data_sources else []  # type: List['DataSource']

    def add_computed_data_sources(self) -> None:
        for data_source in self.data_sources:
            if data_source.export_data_source_id:
                data_source_computed = DataSource(
                    id=data_source.export_data_source_id,
                    name=data_source.export_data_source_id,
                    data_format=data_source.data_format,
                    input=InputComputed(),
                )
                self.data_sources.append(data_source_computed)
        for preprocess in self.preprocesses:
            if "target_data_source_id" in preprocess.params and "export_type" in preprocess.params:
                if not any(data_source for data_source in self.data_sources if
                           data_source.id == preprocess.params.get("target_data_source_id")):
                    data_source_computed = DataSource(
                        id=preprocess.params.get("target_data_source_id"),
                        name=preprocess.params.get("target_data_source_id"),
                        data_format=preprocess.params.get("export_type"),
                        input=InputComputed(),
                    )
                    if not preprocess.params.get("target_data_source_id"):
                        preprocess.params['target_data_source_id'] = data_source_computed.id
                    self.data_sources.append(data_source_computed)

    def fill_data_source_passwords_from_existing_object(self,
                                                        existing_object: 'DataSourceAndPreProcessContainer') -> None:
        for data_source in self.data_sources:
            if data_source.input and isinstance(data_source.input, InputAuto):
                input = data_source.input
                if input.options and input.options.authent and input.options.authent.username and \
                        not input.options.authent.password:
                    existing_data_source = next((
                        existing_data_source for existing_data_source in existing_object.data_sources if
                        existing_data_source.id == data_source.id), None)

                    if existing_data_source \
                            and existing_data_source.is_auto() \
                            and existing_data_source.input.options \
                            and existing_data_source.input.options.authent \
                            and existing_data_source.input.options.authent.username == input.options.authent.username \
                            and existing_data_source.input.options.authent.password:
                        data_source.input.options.authent.password = existing_data_source.input.options.authent.password

    def delete_files_linked(self) -> None:
        for gridfs_id in [data_set.gridfs_id for data_source in self.data_sources for data_set in
                          data_source.data_sets]:
            GridFsHandler().delete_file_from_gridfs(gridfs_id)

    @classmethod
    def get(cls, object_id: str) -> Union['Contributor', Optional['Coverage']]:
        pass


class PlatformOptionsAuthent:
    def __init__(self, username: str = None, password: str = None) -> None:
        self.username = username
        self.password = password


class PlatformOptions:
    def __init__(self, authent: PlatformOptionsAuthent = None, directory: str = None) -> None:
        self.authent = authent
        self.directory = directory


class Platform(object):
    def __init__(self, protocol: str, url: str, options: PlatformOptions = None) -> None:
        self.protocol = protocol
        self.url = url
        self.options = options


class PublicationPlatform(SequenceContainer, Platform):
    def __init__(self, protocol: str, type: str, url: str, options: PlatformOptions = None, sequence: int = 0,
                 input_data_source_ids: List[str] = None) -> None:
        SequenceContainer.__init__(self, sequence)
        Platform.__init__(self, protocol, url, options)
        self.input_data_source_ids = input_data_source_ids if input_data_source_ids else []
        self.type = type


class Environment(SequenceContainer):
    def __init__(self, name: str = None, current_ntfs_id: str = None,
                 publication_platforms: List[PublicationPlatform] = None,
                 sequence: int = 0) -> None:
        super().__init__(sequence)
        self.name = name
        self.current_ntfs_id = current_ntfs_id
        self.publication_platforms = publication_platforms if publication_platforms else []

    def get_publication_platform_for_type_with_user(self, type: str, username: str) -> Optional[PublicationPlatform]:
        return next((existing_platform for existing_platform in self.publication_platforms
                     if existing_platform.type == type and existing_platform.options and
                     existing_platform.options.authent and existing_platform.options.authent.username == username),
                    None)


class ValidityPeriod(object):
    def __init__(self, start_date: date, end_date: date) -> None:
        self.start_date = start_date
        self.end_date = end_date

    def __repr__(self) -> str:
        return str(vars(self))

    @classmethod
    def union(cls, validity_period_list: List['ValidityPeriod']) -> 'ValidityPeriod':
        if not validity_period_list:
            raise ValidityPeriodException('empty validity period list given to calculate union')

        begin_date = min([d.start_date for d in validity_period_list])
        end_date = max([d.end_date for d in validity_period_list])
        return ValidityPeriod(begin_date, end_date)

    def to_valid(self, current_date: date = None) -> 'ValidityPeriod':
        begin_date = self.start_date
        end_date = self.end_date
        now_date = current_date if current_date else date.today()
        if self.end_date < now_date:
            raise ValidityPeriodException(
                'calculating validity period union on past periods (end_date: {end} < now: {now})'.format(
                    end=end_date.strftime('%d/%m/%Y'), now=now_date.strftime('%d/%m/%Y')))
        if abs(begin_date - end_date).days > 365:
            logging.getLogger(__name__).warning(
                'period bounds for union of validity periods exceed one year')
            begin_date = max(begin_date, now_date - timedelta(days=7))
            end_date = min(begin_date + timedelta(days=364), end_date)
        return ValidityPeriod(begin_date, end_date)


class ValidityPeriodContainer(object):
    def __init__(self, validity_period: ValidityPeriod = None) -> None:
        self.validity_period = validity_period


class ContributorExportDataSource(ValidityPeriodContainer):
    def __init__(self, data_source_id: str = None, gridfs_id: str = None,
                 validity_period: ValidityPeriod = None) -> None:
        super().__init__(validity_period)
        self.data_source_id = data_source_id
        self.gridfs_id = gridfs_id


class License(object):
    def __init__(self, name: str = app.config.get('DEFAULT_LICENSE_NAME'),
                 url: str = app.config.get('DEFAULT_LICENSE_URL')) -> None:
        self.name = name
        self.url = url

    def __repr__(self) -> str:
        return str(vars(self))


class DataSetStatus(object):
    def __init__(self, status: str, updated_at: datetime = datetime.now(pytz.utc)) -> None:
        self.status = status
        self.updated_at = updated_at


class DataSet(object):
    def __init__(self, id: str = None, gridfs_id: str = None, validity_period: Optional[ValidityPeriod] = None,
                 created_at: datetime = None, status_history: List[DataSetStatus] = None) -> None:
        self.id = id if id else str(uuid.uuid4())
        self.gridfs_id = gridfs_id
        self.created_at = created_at if created_at else datetime.now(pytz.utc)
        self.validity_period = validity_period
        self.status_history = status_history if status_history else []

    def get_md5(self) -> Optional[str]:
        if not self.gridfs_id:
            return None
        file = GridFsHandler().get_file_from_gridfs(self.gridfs_id)
        return file.md5

    def is_identical_to(self, file_path: str) -> bool:
        return self.get_md5() == get_md5_content_file(file_path)

    def add_file_from_path(self, file_full_path: str, file_name: str) -> None:
        with open(file_full_path, 'rb') as file:
            self.add_file_from_io(file, file_name)

    def add_file_from_io(self, io: Union[IOBase, BinaryIO], file_name: str) -> None:
        self.gridfs_id = GridFsHandler().save_file_in_gridfs(io, filename=file_name, data_set_id=self.id)

    def __repr__(self) -> str:
        return str(vars(self))


class Enabled(object):
    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled


class FrequencyContinuously(Enabled):
    def __init__(self, minutes: int, enabled: bool = True) -> None:
        super().__init__(enabled)
        self.minutes = minutes

    def should_fetch(self, last_fetched_at: datetime, now: datetime) -> bool:
        return not last_fetched_at or (now - last_fetched_at) >= timedelta(minutes=self.minutes)

    def __repr__(self) -> str:
        return "type: {}, data: {}".format(type(self), str(vars(self)))


class FrequencyDaily(Enabled):
    def __init__(self, hour_of_day: int, enabled: bool = True) -> None:
        super().__init__(enabled)
        self.hour_of_day = hour_of_day

    def should_fetch(self, last_fetched_at: datetime, now: datetime) -> bool:
        if not last_fetched_at:
            return now.hour == self.hour_of_day
        else:
            delta = now - last_fetched_at
            # last fetch was on schedule
            if last_fetched_at.hour == self.hour_of_day:
                # fetch if it's been at least one day or almost one day and it's hour of day
                return delta.days >= 1 or (
                    now.day != last_fetched_at.day and now.hour == self.hour_of_day
                )
            else:
                return delta.days >= 1 or now.hour == self.hour_of_day


class FrequencyWeekly(Enabled):
    def __init__(self, day_of_week: int, hour_of_day: int, enabled: bool = True) -> None:
        super().__init__(enabled)
        self.day_of_week = day_of_week
        self.hour_of_day = hour_of_day

    def should_fetch(self, last_fetched_at: datetime, now: datetime) -> bool:
        if not last_fetched_at:
            return now.hour == self.hour_of_day and now.isoweekday() == self.day_of_week
        else:
            delta = now - last_fetched_at
            # last fetch was on schedule
            if last_fetched_at.hour == self.hour_of_day and last_fetched_at.isoweekday() == self.day_of_week:
                # fetch if it's been at least one week or almost one week and it's day of week and hour of day
                return delta.days >= 7 or (
                    now.day != last_fetched_at.day and now.hour == self.hour_of_day and now.isoweekday() == self.day_of_week
                )
            else:
                return delta.days >= 7 or (now.hour == self.hour_of_day and now.isoweekday() == self.day_of_week)


class FrequencyMonthly(Enabled):
    def __init__(self, day_of_month: int, hour_of_day: int, enabled: bool = True) -> None:
        super().__init__(enabled)
        self.day_of_month = day_of_month
        self.hour_of_day = hour_of_day

    def should_fetch(self, last_fetched_at: datetime, now: datetime) -> bool:
        if not last_fetched_at:
            return now.day == self.day_of_month and now.hour == self.hour_of_day
        else:
            delta = now - last_fetched_at
            # last fetch was on schedule
            if last_fetched_at.hour == self.hour_of_day and last_fetched_at.day == self.day_of_month:
                # fetch if it's been at least one month or almost one month and it's day of month and hour of day
                return delta.days >= 31 or (
                    now.day != last_fetched_at.day and now.hour == self.hour_of_day and now.day == self.day_of_month
                )
            else:
                return delta.days >= 31 or (now.hour == self.hour_of_day and now.day == self.day_of_month)


FrequenceType = Union[FrequencyContinuously, FrequencyDaily, FrequencyWeekly, FrequencyMonthly]
InputType = Any  # Union[InputAuto, InputManual, InputComputed] will be better mypy does not manage unions well


class AbstractInput(metaclass=ABCMeta):
    def __init__(self, expected_file_name: str = None) -> None:
        self.expected_file_name = expected_file_name


class InputAuto(AbstractInput):
    def __init__(self, url: str, frequency: FrequenceType,
                 expected_file_name: str = None, options: PlatformOptions = None) -> None:
        super().__init__(expected_file_name)
        self.url = url
        self.options = options
        self.frequency = frequency

    def __repr__(self) -> str:
        return str(vars(self))


class InputManual(AbstractInput):
    def __init__(self, expected_file_name: str = None) -> None:
        super().__init__(expected_file_name)

    def __repr__(self) -> str:
        return str(vars(self))


class InputComputed(AbstractInput):
    def __init__(self, expected_file_name: str = None) -> None:
        super().__init__(expected_file_name)

    def __repr__(self) -> str:
        return str(vars(self))


class DataSource(object):
    def __init__(self, id: Optional[str] = None,
                 name: Optional[str] = None,
                 data_format: str = DATA_FORMAT_DEFAULT,
                 input: InputType = InputManual(),
                 license: Optional[License] = None,
                 export_data_source_id: str = None,
                 service_id: str = None,
                 data_sets: List[DataSet] = None,
                 fetch_started_at: datetime = None,
                 updated_at: datetime = None,
                 status: str = DATA_SOURCE_STATUS_NEVER_FETCHED,
                 validity_period: ValidityPeriod = None
                 ) -> None:
        self.id = id if id else str(uuid.uuid4())
        self.name = name
        self.data_format = data_format
        self.input = input
        self.license = license if license else License()
        self.service_id = service_id
        self.export_data_source_id = export_data_source_id
        self.data_sets = data_sets if data_sets else []
        self.fetch_started_at = fetch_started_at
        self.updated_at = updated_at
        self.status = status
        self.validity_period = validity_period

    def __repr__(self) -> str:
        return str(vars(self))

    def save(self, contributor_id: str) -> None:
        contributor = Contributor.get(contributor_id)
        if self.id in [ds.id for ds in contributor.data_sources]:
            raise ValueError("duplicate data_source id '{}' for contributor '{}'".format(self.id, contributor_id))
        contributor.data_sources.append(self)
        raw_contrib = MongoContributorSchema().dump(contributor).data
        mongo.db[Contributor.mongo_collection].find_one_and_replace({'_id': contributor.id}, raw_contrib)

    @classmethod
    def get(cls, contributor_id: str = None, data_source_id: str = None) -> Optional[List['DataSource']]:
        if contributor_id is not None:
            contributor = Contributor.get(contributor_id)
        elif data_source_id is not None:
            contributor = cls.get_contributor_of_data_source(data_source_id)
        else:
            raise ValueError("to get data_sources you must provide a contributor_id or a data_source_id")

        data_sources = contributor.data_sources
        if data_source_id is not None:
            data_sources = [ds for ds in data_sources if ds.id == data_source_id]
            if not data_sources:
                return None
        return data_sources

    @classmethod
    def get_one(cls, contributor_id: str = None, data_source_id: str = None) -> 'DataSource':
        data_sources = DataSource.get(contributor_id, data_source_id)

        if data_sources is None:
            raise ValueError("data source {} not found for contributor {}".format(data_source_id, contributor_id))

        return data_sources[0]

    @classmethod
    def get_contributor_of_data_source(cls, data_source_id: str) -> Optional['Contributor']:
        raw = mongo.db[Contributor.mongo_collection].find_one({'data_sources.id': data_source_id})

        if not raw:
            return None

        return MongoContributorSchema(strict=True).load(raw).data

    @classmethod
    def update(cls, contributor_id: str, data_source_id: str = None, dataset: dict = None) -> Optional['DataSource']:
        tmp_dataset = dataset if dataset else {}
        if data_source_id is None:
            raise ValueError('a data_source id is required')
        if not [ds for ds in Contributor.get(contributor_id).data_sources if ds.id == data_source_id]:
            raise ValueError("no data_source id {} exists in contributor with id {}"
                             .format(contributor_id, data_source_id))
        if 'id' in tmp_dataset and tmp_dataset['id'] != data_source_id:
            raise ValueError("id from request {} doesn't match id from url {}"
                             .format(tmp_dataset['id'], data_source_id))

        # `$` acts as a placeholder of the first match in the list
        contrib_dataset = {'data_sources': {'$': tmp_dataset}}
        mongo.db[Contributor.mongo_collection].update_one({'data_sources.id': data_source_id},
                                                          {'$set': to_doted_notation(contrib_dataset)})

        data_sources = cls.get(contributor_id, data_source_id)
        return data_sources[0] if data_sources else None

    def add_data_set_and_update_model(self, data_set: DataSet, model: Union['Contributor', 'Coverage']) -> None:
        self.data_sets.append(data_set)
        data_sets_number = app.config.get('HISTORICAL', 3)
        if len(self.data_sets) > data_sets_number:
            sorted_data_set = sorted(self.data_sets, key=lambda ds: ds.created_at, reverse=True)
            for data_set_to_be_removed in sorted_data_set[data_sets_number:]:
                if data_set_to_be_removed.gridfs_id:
                    GridFsHandler().delete_file_from_gridfs(data_set_to_be_removed.gridfs_id)
            self.data_sets = sorted_data_set[0:data_sets_number]
        self.validity_period = data_set.validity_period
        self.updated_at = data_set.created_at
        self.status = DATA_SOURCE_STATUS_UPDATED
        model.update()

    def is_of_data_format(self, data_format: str) -> bool:
        return self.data_format == data_format

    def is_of_one_of_data_format(self, data_format_list: List[str]) -> bool:
        return any(self.is_of_data_format(data_format) for data_format in data_format_list)

    def is_auto(self) -> bool:
        return isinstance(self.input, InputAuto)

    def is_computed(self) -> bool:
        return isinstance(self.input, InputComputed)

    def get_last_data_set_if_exists(self) -> Optional[DataSet]:
        return max(self.data_sets, key=lambda ds: ds.created_at, default=None)

    def get_last_data_set(self) -> DataSet:
        last_data_set = self.get_last_data_set_if_exists()
        if not last_data_set:
            raise RuntimeException("data source '{}' has no data sets".format(self.id))
        return last_data_set

    def starts_fetch(self, model: Union['Contributor', 'Coverage']) -> None:
        self.fetch_started_at = datetime.now(pytz.utc)
        self.status = DATA_SOURCE_STATUS_FETCHING
        model.update()

    def fetch_fails(self, model: Union['Contributor', 'Coverage']) -> None:
        self.status = DATA_SOURCE_STATUS_FAILED
        model.update()

    def fetch_unchanged(self, model: Union['Contributor', 'Coverage']) -> None:
        self.status = DATA_SOURCE_STATUS_UNCHANGED
        model.update()

    def should_fetch(self) -> bool:
        return self.is_auto() and self.input.frequency.should_fetch(self.fetch_started_at, datetime.now(pytz.utc))


class GenericPreProcess(SequenceContainer):
    def __init__(self, id: Optional[str] = None, type: Optional[str] = None, params: Optional[dict] = None,
                 sequence: int = 0, data_source_ids: Optional[List[str]] = None,
                 enabled: bool = True) -> None:
        super().__init__(sequence)
        self.id = str(uuid.uuid4()) if not id else id
        self.data_source_ids = data_source_ids if data_source_ids else []
        self.params = params if params else {}
        self.type = type
        self.enabled = enabled

    def save_data(self, class_name: Type[DataSourceAndPreProcessContainer],
                  mongo_schema: Type['MongoPreProcessContainerSchema'], object_id: str,
                  ref_model_object: 'PreProcess') -> None:
        data = class_name.get(object_id)
        if data is None:
            raise ValueError('bad {} {}'.format(class_name.label, object_id))
        if self.id in [p.id for p in data.preprocesses]:
            raise ValueError("duplicate PreProcess id '{}'".format(self.id))

        data.preprocesses.append(ref_model_object)
        data.add_computed_data_sources()
        raw_contrib = mongo_schema().dump(data).data
        mongo.db[class_name.mongo_collection].find_one_and_replace({'_id': data.id}, raw_contrib)

    @classmethod
    def get_data(cls, class_name: Type[DataSourceAndPreProcessContainer],
                 mongo_schema: Type['MongoPreProcessContainerSchema'], object_id: str,
                 preprocess_id: str) -> Optional[List['PreProcess']]:
        if object_id is not None:
            data = class_name.get(object_id)
            if data is None:
                raise ValueError('bad {} {}'.format(class_name.label, object_id))
        elif preprocess_id is not None:
            raw = mongo.db[class_name.mongo_collection].find_one({'preprocesses.id': preprocess_id})
            if raw is None:
                return None
            data = mongo_schema(strict=True).load(raw).data
        else:
            raise ValueError("to get preprocess you must provide a contributor_id or a preprocess_id")

        preprocesses = data.preprocesses

        if preprocess_id is None:
            return preprocesses
        p = next((p for p in preprocesses if p.id == preprocess_id), None)
        return [p] if p else []

    @classmethod
    def delete_data(cls, class_name: Type[DataSourceAndPreProcessContainer],
                    mongo_schema: Type['MongoPreProcessContainerSchema'], object_id: str,
                    preprocess_id: str) -> int:
        data = class_name.get(object_id)
        if data is None:
            raise ValueError('bad {} {}'.format(class_name.label, object_id))

        nb_delete = len([p for p in data.preprocesses if p.id == preprocess_id])
        data.preprocesses = [p for p in data.preprocesses if p.id != preprocess_id]
        raw_contrib = mongo_schema().dump(data).data
        mongo.db[class_name.mongo_collection].find_one_and_replace({'_id': data.id}, raw_contrib)
        return nb_delete

    @classmethod
    def update_data(cls, class_name: Type[DataSourceAndPreProcessContainer],
                    mongo_schema: Type['MongoPreProcessContainerSchema'], object_id: str,
                    preprocess_id: str, preprocess: Optional[Dict[str, Any]] = None) -> Optional[List['PreProcess']]:
        data = class_name.get(object_id)
        if not data:
            raise ValueError('bad {} {}'.format(class_name.label, object_id))

        if not [ps for ps in data.preprocesses if ps.id == preprocess_id]:
            raise ValueError("no preprocesses id {} exists in {} with id {}"
                             .format(object_id, class_name.label, preprocess_id))
        if preprocess and 'id' in preprocess and preprocess['id'] != preprocess_id:
            raise ValueError("id from request {} doesn't match id from url {}"
                             .format(preprocess['id'], preprocess_id))

        preprocess['id'] = preprocess_id
        raw = mongo.db[class_name.mongo_collection].update_one({'preprocesses.id': preprocess_id},
                                                               {'$set': {'preprocesses.$': preprocess}})
        if raw.matched_count == 0:
            return None

        return cls.get_data(class_name, mongo_schema, object_id, preprocess_id)


class PreProcess(GenericPreProcess):
    def save(self, contributor_id: Optional[str] = None, coverage_id: Optional[str] = None) -> None:
        if not any([coverage_id, contributor_id]):
            raise ValueError('bad arguments')
        # self passed as 4th argument is child object from GenericPreProcess.save_data method point of vue
        # so it's the one that will need to be saved as a PreProcess
        if contributor_id:
            self.save_data(Contributor, MongoContributorSchema, contributor_id, self)
        if coverage_id:
            self.save_data(Coverage, MongoCoverageSchema, coverage_id, self)

    @classmethod
    def get(cls, preprocess_id: str, contributor_id: Optional[str] = None,
            coverage_id: Optional[str] = None) -> Optional[List['PreProcess']]:
        if not any([coverage_id, contributor_id]):
            raise ValueError('bad arguments')
        if contributor_id:
            return cls.get_data(Contributor, MongoContributorSchema, contributor_id, preprocess_id)
        if coverage_id:
            return cls.get_data(Coverage, MongoCoverageSchema, coverage_id, preprocess_id)

    @classmethod
    def delete(cls, preprocess_id: str, contributor_id: Optional[str] = None, coverage_id: Optional[str] = None) -> int:
        if preprocess_id is None:
            raise ValueError('a preprocess id is required')
        if not any([coverage_id, contributor_id]):
            raise ValueError('bad arguments')
        if contributor_id:
            return cls.delete_data(Contributor, MongoContributorSchema, contributor_id, preprocess_id)
        if coverage_id:
            return cls.delete_data(Coverage, MongoCoverageSchema, coverage_id, preprocess_id)

    @classmethod
    def update(cls, preprocess_id: str, contributor_id: Optional[str] = None, coverage_id: Optional[str] = None,
               preprocess: Optional[dict] = None) -> Optional[List['PreProcess']]:
        if preprocess_id is None:
            raise ValueError('a PreProcess id is required')

        if not any([coverage_id, contributor_id]):
            raise ValueError('bad arguments')

        if contributor_id:
            return cls.update_data(Contributor, MongoContributorSchema, contributor_id, preprocess_id, preprocess)
        if coverage_id:
            return cls.update_data(Coverage, MongoCoverageSchema, coverage_id, preprocess_id, preprocess)

    def __repr__(self) -> str:
        return str(vars(self))


class Contributor(DataSourceAndPreProcessContainer):
    mongo_collection = 'contributors'
    label = 'Contributor'

    def __init__(self, id: str, name: str, data_prefix: str, data_sources: List[DataSource] = None,
                 preprocesses: List[PreProcess] = None, data_type: str = DATA_TYPE_DEFAULT) -> None:
        super(Contributor, self).__init__(preprocesses, data_sources)
        self.id = id
        self.name = name
        self.data_prefix = data_prefix
        self.data_type = data_type

    def __repr__(self) -> str:
        return str(vars(self))

    def save(self) -> None:
        raw = MongoContributorSchema().dump(self).data
        mongo.db[self.mongo_collection].insert_one(raw)

    @classmethod
    def get(cls, contributor_id: str) -> 'Contributor':
        raw = mongo.db[cls.mongo_collection].find_one({'_id': contributor_id})
        if raw is None:
            msg = "contributor '{}' not found".format(contributor_id)
            logging.getLogger(__name__).error(msg)
            raise EntityNotFound(msg)
        return MongoContributorSchema(strict=True).load(raw).data

    def __check_contributors_using_integrity(self) -> None:
        contributors_using = self.find({
            'preprocesses.params.links.contributor_id': self.id
        })
        if contributors_using:
            contributors_ids = [contributor.id for contributor in contributors_using]
            raise IntegrityException(
                'unable to delete contributor {} because the following contributors are using one of its data sources: {}'.format(
                    self.id, ', '.join(contributors_ids)
                ))

    def __check_coverages_using_integrity(self) -> None:
        coverages_using = Coverage.find({
            'input_data_source_ids': {'$in': [data_source.id for data_source in self.data_sources]}
        })
        if coverages_using:
            coverages_ids = [coverage.id for coverage in coverages_using]
            raise IntegrityException(
                'unable to delete contributor {} because the following coverages are using one of its data sources: {}'.format(
                    self.id, ', '.join(coverages_ids)
                ))

    @classmethod
    def delete(cls, contributor_id: str) -> int:
        contributor = cls.get(contributor_id)
        contributor.__check_contributors_using_integrity()
        contributor.__check_coverages_using_integrity()
        raw = mongo.db[cls.mongo_collection].delete_one({'_id': contributor_id})
        if raw.deleted_count:
            contributor.delete_files_linked()
        return raw.deleted_count

    @classmethod
    def find(cls, filter: dict) -> List['Contributor']:
        raw = mongo.db[cls.mongo_collection].find(filter)
        return MongoContributorSchema(many=True, strict=True).load(raw).data

    @classmethod
    def all(cls) -> List['Contributor']:
        return cls.find(filter={})

    def update(self) -> None:
        self.update_with_object(self)

    def update_with_object(self, contributor_object: 'Contributor') -> None:
        contributor_object.fill_data_source_passwords_from_existing_object(self)
        mongo.db[self.mongo_collection].update_one(
            {'_id': self.id},
            {'$set': MongoContributorSchema().dump(contributor_object).data})

    def get_data_source(self, data_source_id: str) -> Optional['DataSource']:
        return next((data_source for data_source in self.data_sources if data_source.id == data_source_id), None)

    def is_geographic(self) -> bool:
        return self.data_type == DATA_TYPE_GEOGRAPHIC


class Coverage(DataSourceAndPreProcessContainer):
    mongo_collection = 'coverages'
    label = 'Coverage'

    def __init__(self, id: str, name: str, environments: Dict[str, Environment] = None,
                 input_data_source_ids: List[str] = None, license: License = None,
                 preprocesses: List[PreProcess] = None, data_sources: List[DataSource] = None,
                 type: str = 'other', short_description: str = '', comment: str = '') -> None:
        super(Coverage, self).__init__(preprocesses)
        self.id = id
        self.name = name
        self.environments = {} if environments is None else environments
        self.input_data_source_ids = [] if input_data_source_ids is None else input_data_source_ids
        self.license = license if license else License()
        self.data_sources = data_sources if data_sources else []
        self.type = type
        self.short_description = short_description
        self.comment = comment

    def save(self) -> None:
        raw = MongoCoverageSchema(strict=True).dump(self).data
        mongo.db[self.mongo_collection].insert_one(raw)

    @classmethod
    def get(cls, coverage_id: str) -> 'Coverage':
        raw = mongo.db[cls.mongo_collection].find_one({'_id': coverage_id})
        if raw is None:
            msg = "coverage '{}' not found".format(coverage_id)
            logging.getLogger(__name__).error(msg)
            raise EntityNotFound(msg)
        return MongoCoverageSchema(strict=True).load(raw).data

    @classmethod
    def delete(cls, coverage_id: str = None) -> int:
        coverage = Coverage.get(coverage_id)
        raw = mongo.db[cls.mongo_collection].delete_one({'_id': coverage_id})
        if raw.deleted_count:
            coverage.delete_files_linked()
        return raw.deleted_count

    @classmethod
    def find(cls, filter: dict) -> List['Coverage']:
        raw = mongo.db[cls.mongo_collection].find(filter)
        return MongoCoverageSchema(many=True, strict=True).load(raw).data

    @classmethod
    def all(cls) -> List['Coverage']:
        return cls.find(filter={})

    def __fill_platform_passwords_from_existing_coverage(self, existing_coverage: 'Coverage') -> None:
        for env_key, environment in self.environments.items():
            for platform in environment.publication_platforms:
                if platform.options and platform.options.authent and platform.options.authent.username and \
                        not platform.options.authent.password:
                    if env_key in existing_coverage.environments:
                        existing_platform = existing_coverage.environments[env_key] \
                            .get_publication_platform_for_type_with_user(
                            platform.type, platform.options.authent.username
                        )
                        if existing_platform:
                            platform.options.authent.password = existing_platform.options.authent.password

    def update_with_object(self, coverage_object: 'Coverage') -> None:
        coverage_object.fill_data_source_passwords_from_existing_object(self)
        coverage_object.__fill_platform_passwords_from_existing_coverage(self)
        mongo.db[self.mongo_collection].update_one(
            {'_id': self.id},
            {'$set': MongoCoverageSchema().dump(coverage_object).data})

    def update(self) -> None:
        self.update_with_object(self)

    def get_data_source(self, data_source_id: str) -> 'DataSource':
        return next(data_source for data_source in self.data_sources if data_source.id == data_source_id)

    def __repr__(self) -> str:
        return str(vars(self))


class MongoValidityPeriodSchema(Schema):
    start_date = fields.Date(required=True)
    end_date = fields.Date(required=True)

    @post_load
    def make_validityperiod(self, data: dict) -> ValidityPeriod:
        return ValidityPeriod(**data)


class MongoDataSetStatusSchema(Schema):
    status = fields.String(required=True)
    updated_at = fields.DateTime(required=True)


class MongoDataSetSchema(Schema):
    id = fields.String(required=True)
    gridfs_id = fields.String(required=True)
    created_at = fields.DateTime(required=True)
    validity_period = fields.Nested(MongoValidityPeriodSchema, required=False, allow_none=True)
    status_history = fields.Nested(MongoDataSetStatusSchema, many=True)

    @post_load
    def make_data_set(self, data: dict) -> DataSet:
        return DataSet(**data)


class MongoContributorExportDataSourceSchema(Schema):
    data_source_id = fields.String(required=True)
    gridfs_id = fields.String(required=True)
    validity_period = fields.Nested(MongoValidityPeriodSchema, required=False, allow_none=True)

    @post_load
    def make_contributorexportdatasource(self, data: dict) -> ContributorExportDataSource:
        return ContributorExportDataSource(**data)


class MongoPlatformOptionsAuthentSchema(Schema):
    username = fields.String(required=True)
    password = fields.String(required=False, allow_none=True)

    @post_load
    def make_platform_options_authent(self, data: dict) -> PlatformOptionsAuthent:
        return PlatformOptionsAuthent(**data)


class MongoPlatformOptionsSchema(Schema):
    authent = fields.Nested(MongoPlatformOptionsAuthentSchema, required=False)
    directory = fields.String(required=False, allow_none=True)

    @post_load
    def make_platform_options(self, data: dict) -> PlatformOptions:
        return PlatformOptions(**data)


class MongoPlatformSchema(Schema):
    protocol = PlatformProtocol(required=True)
    url = fields.String(required=True)
    options = fields.Nested(MongoPlatformOptionsSchema, required=False, allow_none=True)

    @post_load
    def make_platform(self, data: dict) -> Platform:
        return Platform(**data)


class MongoPublicationPlatformSchema(Schema):
    # inherited attributes from MongoPlatformSchema because if we extend it, it makes 2 decorators
    # and confuses the post_load
    protocol = PlatformProtocol(required=True)
    url = fields.String(required=True)
    options = fields.Nested(MongoPlatformOptionsSchema, required=False, allow_none=True)
    # end of duplicate
    type = PlatformType(required=True)
    input_data_source_ids = fields.List(fields.String())
    sequence = fields.Integer(required=True)

    @post_load
    def make_publication_platform(self, data: dict) -> PublicationPlatform:
        return PublicationPlatform(**data)


class MongoEnvironmentSchema(Schema):
    name = fields.String(required=True)
    sequence = fields.Integer(required=True)
    current_ntfs_id = fields.String(allow_none=True)
    publication_platforms = fields.Nested(MongoPublicationPlatformSchema, many=True)

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
            :param num: The number of data sources fetched you want to keep
            :param filter: the filter to apply to the data_sources selected
        """
        old_rows = self.get_all_before_n_last(num, filter)

        if old_rows:
            # Delete old data_sources_fetched
            num_deleted = self.delete_many([row.get('_id') for row in old_rows])
            # Delete all associated gridFS
            gridfs_ids = []  # type: List[str]
            if num_deleted:
                get_values_by_key(old_rows, gridfs_ids)
            for gridf_id in gridfs_ids:
                GridFsHandler().delete_file_from_gridfs(gridf_id)


class MongoDataSourceLicenseSchema(Schema):
    name = fields.String(required=False)
    url = fields.String(required=False)

    @post_load
    def build_license(self, data: dict) -> License:
        return License(**data)


class EnabledSchema(Schema):
    enabled = fields.Bool(required=False)


class ValidateHour(object):
    hour_of_day = fields.Int(required=True)

    @validates('hour_of_day')
    def validates(self, hour_of_day: int) -> None:
        if hour_of_day < 0 or hour_of_day > 23:
            raise ValidationError("hour_of_day should be between 0 and 23")


class FrequencyContinuouslySchema(EnabledSchema):
    minutes = fields.Int(required=True)

    @post_load
    def make(self, data: dict) -> FrequencyContinuously:
        return FrequencyContinuously(**data)

    @validates('minutes')
    def validate(self, minutes: int) -> None:
        if minutes < 1:
            raise ValidationError("minutes should be greater than 1")


class FrequencyDailySchema(EnabledSchema, ValidateHour):
    @post_load
    def make(self, data: dict) -> FrequencyDaily:
        return FrequencyDaily(**data)


class FrequencyWeeklySchema(EnabledSchema, ValidateHour):
    day_of_week = fields.Int(required=True)

    @post_load
    def make(self, data: dict) -> FrequencyWeekly:
        return FrequencyWeekly(**data)

    @validates('day_of_week')
    def validates_day_of_week(self, day_of_week: int) -> None:
        if day_of_week < 1 or day_of_week > 7:
            raise ValidationError("day_of_week should be between 1 and 7")


class FrequencyMonthlySchema(EnabledSchema, ValidateHour):
    day_of_month = fields.Int(required=True)

    @post_load
    def make(self, data: dict) -> FrequencyMonthly:
        return FrequencyMonthly(**data)

    @validates('day_of_month')
    def validates_day_of_month(self, day_of_month: int) -> None:
        if day_of_month < 1 or day_of_month > 28:
            raise ValidationError("day_of_month should be between 1 and 28")


class FrequencySchema(OneOfSchema):
    type_schemas = {
        'continuously': FrequencyContinuouslySchema,
        'daily': FrequencyDailySchema,
        'weekly': FrequencyWeeklySchema,
        'monthly': FrequencyMonthlySchema,
    }

    def get_obj_type(self, obj: FrequenceType) -> str:
        if isinstance(obj, FrequencyContinuously):
            return 'continuously'
        elif isinstance(obj, FrequencyDaily):
            return 'daily'
        elif isinstance(obj, FrequencyWeekly):
            return 'weekly'
        elif isinstance(obj, FrequencyMonthly):
            return 'monthly'
        else:
            raise ParameterException('unknown frequency object type: %s' % obj.__class__.__name__)


class InputAutoSchema(Schema):
    url = fields.String(required=False, allow_none=True)
    expected_file_name = fields.String(required=False, allow_none=True)
    options = fields.Nested(MongoPlatformOptionsSchema, required=False, allow_none=True)
    frequency = fields.Nested(FrequencySchema, required=True)

    @post_load
    def make_input(self, data: dict) -> InputAuto:
        return InputAuto(**data)


class InputManualSchema(Schema):
    expected_file_name = fields.String(required=False, allow_none=True)

    @post_load
    def make_input(self, data: dict) -> InputManual:
        return InputManual(**data)


class InputComputedSchema(Schema):
    expected_file_name = fields.String(required=False, allow_none=True)

    @post_load
    def make_input(self, data: dict) -> InputComputed:
        return InputComputed(**data)


class MongoDataSourceInputSchema(OneOfSchema):
    type_schemas = {
        INPUT_TYPE_AUTO: InputAutoSchema,
        INPUT_TYPE_MANUAL: InputManualSchema,
        INPUT_TYPE_COMPUTED: InputComputedSchema,
    }

    def get_obj_type(self, obj: InputType) -> str:
        if isinstance(obj, InputAuto):
            return INPUT_TYPE_AUTO
        elif isinstance(obj, InputManual):
            return INPUT_TYPE_MANUAL
        elif isinstance(obj, InputComputed):
            return INPUT_TYPE_COMPUTED
        else:
            raise ParameterException('unknown data source input object: %s' % obj.__class__.__name__)


class MongoDataSourceSchema(Schema):
    id = fields.String(required=True)
    name = fields.String(required=True)
    data_format = DataFormat()
    license = fields.Nested(MongoDataSourceLicenseSchema, allow_none=False)
    input = fields.Nested(MongoDataSourceInputSchema, required=False, allow_none=True)
    service_id = fields.String(required=False, allow_none=True)
    export_data_source_id = fields.String(required=False, allow_none=True)
    data_sets = fields.Nested(MongoDataSetSchema, many=True, required=False, allow_none=True)
    fetch_started_at = fields.DateTime(required=False, allow_none=True)
    updated_at = fields.DateTime(required=False, allow_none=True)
    status = fields.String(required=False, allow_none=True)
    validity_period = fields.Nested(MongoValidityPeriodSchema, required=False, allow_none=True)

    @post_load
    def build_data_source(self, data: dict) -> DataSource:
        return DataSource(**data)


class MongoPreProcessSchema(Schema):
    id = fields.String(required=True)
    enabled = fields.Boolean(required=False)
    sequence = fields.Integer(required=True)
    type = fields.String(required=True)
    params = fields.Dict(required=False)
    data_source_ids = fields.List(fields.String(), required=False)

    @post_load
    def build_preprocess(self, data: dict) -> PreProcess:
        return PreProcess(**data)


class MongoPreProcessContainerSchema(Schema):
    pass


class MongoCoverageSchema(MongoPreProcessContainerSchema):
    id = fields.String(required=True, load_from='_id', dump_to='_id')
    name = fields.String(required=True)
    environments = fields.Nested(MongoEnvironmentListSchema)
    input_data_source_ids = fields.List(fields.String())
    license = fields.Nested(MongoDataSourceLicenseSchema, allow_none=True)
    preprocesses = fields.Nested(MongoPreProcessSchema, many=True, required=False, allow_none=False)
    data_sources = fields.Nested(MongoDataSourceSchema, many=True, required=False, allow_none=True)
    type = CoverageType()
    short_description = fields.String()
    comment = fields.String()

    @post_load
    def make_coverage(self, data: dict) -> Coverage:
        return Coverage(**data)


class MongoContributorSchema(MongoPreProcessContainerSchema):
    id = fields.String(required=True, load_from='_id', dump_to='_id')
    name = fields.String(required=True)
    data_prefix = fields.String(required=True)
    data_sources = fields.Nested(MongoDataSourceSchema, many=True, required=False)
    preprocesses = fields.Nested(MongoPreProcessSchema, many=True, required=False)
    data_type = DataType()

    @post_load
    def make_contributor(self, data: dict) -> Contributor:
        return Contributor(**data)


class Job(object):
    mongo_collection = 'jobs'

    def __init__(self, action_type: str, contributor_id: str = None, coverage_id: str = None, parent_id: str = None,
                 state: str = JOB_STATUS_PENDING, step: str = None, id: str = None, started_at: datetime = None,
                 updated_at: Optional[datetime] = None, error_message: str = "", data_source_id: str = None) -> None:
        self.id = id if id else str(uuid.uuid4())
        self.parent_id = parent_id
        self.action_type = action_type
        self.contributor_id = contributor_id
        self.data_source_id = data_source_id
        self.coverage_id = coverage_id
        self.step = step
        self.state = state
        self.error_message = error_message
        self.started_at = started_at if started_at else  datetime.now(pytz.utc)
        self.updated_at = updated_at if updated_at else self.started_at

    def save(self) -> None:
        raw = MongoJobSchema().dump(self).data
        mongo.db[self.mongo_collection].insert_one(raw)

    @classmethod
    def find(cls, filter: dict) -> List['Job']:
        raw = mongo.db[cls.mongo_collection].find(filter)
        return MongoJobSchema(many=True).load(raw).data

    @classmethod
    def cancel_pending_updated_before(cls, nb_hours: int, statuses: List[str],
                                      current_date: datetime = datetime.today()) -> List['Job']:
        filter_statuses = [{'state': status} for status in statuses]
        filter = {
            '$or': filter_statuses,
            'updated_at': {'$lt': (current_date - timedelta(hours=nb_hours)).isoformat()}
        }
        raw = mongo.db[cls.mongo_collection].find(filter)
        pending_jobs = MongoJobSchema(many=True).load(raw).data
        pending_jobs_before_update = copy.deepcopy(pending_jobs)
        for pending_job in pending_jobs:
            pending_job.update(JOB_STATUS_FAILED, error_message='automatically cancelled')
        return pending_jobs_before_update

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
    def get_last(cls, filter: dict) -> Optional['Job']:
        raw = mongo.db[cls.mongo_collection].find(filter).sort("updated_at", -1).limit(1)
        lasts = MongoJobSchema(many=True, strict=True).load(raw).data
        return lasts[0] if lasts else None

    def update(self, state: str = None, step: str = None, error_message: str = None) -> Optional['Job']:
        if state is not None:
            self.state = state
        if step is not None:
            self.step = step
        if error_message is not None:
            self.error_message = error_message

        self.updated_at = datetime.now(pytz.utc)
        raw = mongo.db[Job.mongo_collection].update_one({'_id': self.id}, {'$set': MongoJobSchema().dump(self).data})
        if raw.matched_count == 0:
            return None
        return self

    def has_failed(self) -> bool:
        return self.state == JOB_STATUS_FAILED

    @classmethod
    def get_last_data_fetch_job(cls, data_source_id: str) -> Optional['Job']:
        filter = {
            'action_type': ACTION_TYPE_DATA_SOURCE_FETCH,
            'data_source_id': data_source_id,
        }
        raw = mongo.db[cls.mongo_collection].find(filter).sort("updated_at", -1).limit(1)
        lasts = MongoJobSchema(strict=True, many=True).load(raw).data
        return lasts[0] if lasts else None

    def __repr__(self) -> str:
        return str(vars(self))


class MongoJobSchema(Schema):
    id = fields.String(required=True, load_from='_id', dump_to='_id')
    parent_id = fields.String(required=False, allow_none=True)
    action_type = fields.String(required=True)
    contributor_id = fields.String(required=False, allow_none=True)
    data_source_id = fields.String(required=False, allow_none=True)
    coverage_id = fields.String(required=False, allow_none=True)
    state = JobStatus(required=True)
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
                 validity_period: ValidityPeriod,
                 data_sources: List[ContributorExportDataSource] = None,
                 id: str = None,
                 created_at: datetime = None) -> None:
        self.id = id if id else str(uuid.uuid4())
        self.contributor_id = contributor_id
        self.created_at = created_at if created_at else  datetime.now(pytz.utc)
        self.validity_period = validity_period
        self.data_sources = [] if data_sources is None else data_sources

    def save(self) -> None:
        raw = MongoContributorExportSchema(strict=True).dump(self).data
        mongo.db[self.mongo_collection].insert_one(raw)

        self.keep_historical(app.config.get('HISTORICAL', 3), {'contributor_id': self.contributor_id})

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
        lasts = MongoContributorExportSchema(many=True, strict=True).load(raw).data
        return lasts[0] if lasts else None


class MongoContributorExportSchema(Schema):
    id = fields.String(required=True, load_from='_id', dump_to='_id')
    contributor_id = fields.String(required=True)
    created_at = fields.DateTime(required=True)
    validity_period = fields.Nested(MongoValidityPeriodSchema, required=False, allow_none=True)
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

    def __repr__(self) -> str:
        return str(vars(self))


class MongoCoverageExportContributorSchema(Schema):
    contributor_id = fields.String(required=True)
    validity_period = fields.Nested(MongoValidityPeriodSchema, required=False, allow_none=True)
    data_sources = fields.Nested(MongoContributorExportDataSourceSchema, many=True)

    @post_load
    def make_coverageexportcontributor(self, data: dict) -> CoverageExportContributor:
        return CoverageExportContributor(**data)


class CoverageExport(Historisable):
    mongo_collection = 'coverage_exports'

    def __init__(self, coverage_id: str, gridfs_id: str, validity_period: ValidityPeriod,
                 id: str = None, created_at: str = None) -> None:
        self.id = id if id else str(uuid.uuid4())
        self.coverage_id = coverage_id
        self.gridfs_id = gridfs_id
        self.validity_period = validity_period
        self.created_at = created_at if created_at else  datetime.now(pytz.utc)

    def save(self) -> None:
        raw = MongoCoverageExportSchema().dump(self).data
        mongo.db[self.mongo_collection].insert_one(raw)

        self.keep_historical(app.config.get('HISTORICAL', 3), {'coverage_id': self.coverage_id})

    @classmethod
    def get(cls, coverage_id: str) -> Optional[List['CoverageExport']]:
        if not coverage_id:
            return None
        raw = mongo.db[cls.mongo_collection].find({'coverage_id': coverage_id}).sort("created_at", -1)
        return MongoCoverageExportSchema(many=True).load(raw).data

    @classmethod
    def get_last(cls, coverage_id: str) -> Optional['CoverageExport']:
        raw = mongo.db[cls.mongo_collection].find({'coverage_id': coverage_id}).sort("created_at", -1).limit(1)
        lasts = MongoCoverageExportSchema(many=True).load(raw).data
        return lasts[0] if lasts else None

    def __repr__(self) -> str:
        return str(vars(self))


class MongoCoverageExportSchema(Schema):
    id = fields.String(required=True, load_from='_id', dump_to='_id')
    coverage_id = fields.String(required=True)
    gridfs_id = fields.String(required=True)
    created_at = fields.DateTime(required=True)
    validity_period = fields.Nested(MongoValidityPeriodSchema, required=False, allow_none=True)

    @post_load
    def make_coverage_export(self, data: dict) -> CoverageExport:
        return CoverageExport(**data)


class DataSourceStatus(object):
    """
   Calculate following attributes:
       - status: status of the last try on fetching data
       - fetch_started_at: datetime at which the last try on fetching data started
       - updated_at: datetime at which the last fetched data set was valid and inserted in database
       - validity_period: validity period of the data source
   """

    def __init__(self, data_source_id: str, data_sets_dict: List[dict]) -> None:
        last_data_fetch_job = Job.get_last_data_fetch_job(data_source_id)
        last_data_set_dict = max(data_sets_dict, key=lambda ds: ds['created_at'], default=None) if len(data_sets_dict) \
            else None
        self.status = self.get_status_from_job(last_data_fetch_job)
        self.fetch_started_at = last_data_fetch_job.started_at.isoformat() if last_data_fetch_job else None
        self.validity_period = last_data_set_dict['validity_period'] if last_data_set_dict else None
        self.updated_at = last_data_set_dict['created_at'] if last_data_set_dict else None

    def get_status_from_job(self, job: Optional[Job]) -> str:
        if not job:
            status = DATA_SOURCE_STATUS_NEVER_FETCHED
        else:
            if job.state == JOB_STATUS_DONE:
                status = DATA_SOURCE_STATUS_UNCHANGED if job.step == 'compare' else DATA_SOURCE_STATUS_UPDATED
            elif job.state == JOB_STATUS_RUNNING:
                status = 'fetching'
            else:
                status = JOB_STATUS_FAILED
        return status
