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
import calendar
import copy
import logging
import uuid
from abc import ABCMeta
from datetime import date, timedelta
from datetime import datetime
from io import IOBase
from typing import Optional, List, Union, Dict, Any, TypeVar, BinaryIO, Tuple, Type, Set

import pymongo
import pytz
from marshmallow import Schema, post_load, utils, fields, validates, validates_schema, ValidationError
from marshmallow_oneofschema import OneOfSchema

from tartare import app
from tartare import mongo
from tartare.core.constants import *
from tartare.core.gridfs_handler import GridFsHandler
from tartare.exceptions import ValidityPeriodException, EntityNotFound, ParameterException, IntegrityException, \
    RuntimeException
from tartare.helper import get_values_by_key, get_md5_content_file


@app.before_first_request
def init_mongo() -> None:
    mongo.db['contributors'].create_index("data_prefix", unique=True)
    mongo.db['contributors'].create_index([("data_sources.id", pymongo.DESCENDING)], unique=True, sparse=True)
    mongo.db['coverages'].create_index([("data_sources.id", pymongo.DESCENDING)], unique=True, sparse=True)


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


class DataSourceAndProcessContainer(metaclass=ABCMeta):
    mongo_collection = ''
    label = ''

    def __init__(self, processes: List['Process'] = None, data_sources: List['DataSource'] = None) -> None:
        self.processes = [] if processes is None else processes  # type: List['Process']
        self.data_sources = data_sources if data_sources else []  # type: List['DataSource']

    def add_computed_data_sources(self) -> None:
        for data_source in self.data_sources:
            if data_source.export_data_source_id:
                if not any(data_source for data_source in self.data_sources if
                           data_source.id == data_source.export_data_source_id):
                    data_source_computed = DataSource(
                        id=data_source.export_data_source_id,
                        name=data_source.export_data_source_id,
                        data_format=data_source.data_format,
                        input=InputComputed(),
                    )
                    self.data_sources.append(data_source_computed)
        for process in self.processes:
            if isinstance(process, OldProcess):
                if "target_data_source_id" in process.params and "export_type" in process.params:
                    if not any(data_source for data_source in self.data_sources if
                               data_source.id == process.params.get("target_data_source_id")):
                        data_source_computed = DataSource(
                            id=process.params.get("target_data_source_id"),
                            name=process.params.get("target_data_source_id"),
                            data_format=process.params.get("export_type"),
                            input=InputComputed(),
                        )
                        # empty target_data_source_id generates a new id (uuid.uuid4() of DataSource.__init__())
                        if not process.params.get("target_data_source_id"):
                            process.params['target_data_source_id'] = data_source_computed.id
                        self.data_sources.append(data_source_computed)
            elif isinstance(process, NewProcess) and process.target_data_format and process.target_data_source_id:
                data_source_computed = DataSource(
                    id=process.target_data_source_id,
                    name=process.target_data_source_id,
                    data_format=process.target_data_format,
                    input=InputComputed(),
                )
                self.data_sources.append(data_source_computed)

    def fill_data_source_passwords_from_existing_object(self,
                                                        existing_object: 'DataSourceAndProcessContainer') -> None:
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
    def __init__(self, protocol: str, url: str, options: PlatformOptions = None, sequence: int = 0,
                 input_data_source_ids: List[str] = None) -> None:
        SequenceContainer.__init__(self, sequence)
        Platform.__init__(self, protocol, url, options)
        self.input_data_source_ids = input_data_source_ids if input_data_source_ids else []


class Environment(SequenceContainer):
    def __init__(self, name: str = None, current_ntfs_id: str = None,
                 publication_platforms: List[PublicationPlatform] = None,
                 sequence: int = 0) -> None:
        super().__init__(sequence)
        self.name = name
        self.current_ntfs_id = current_ntfs_id
        self.publication_platforms = publication_platforms if publication_platforms else []

    def get_publication_platform_for_type_with_user(self, username: str) -> Optional[PublicationPlatform]:
        return next((existing_platform for existing_platform in self.publication_platforms
                     if existing_platform.options and
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
            previous_tick = now if now.hour >= self.hour_of_day else now - timedelta(days=1)
            previous_tick = previous_tick.replace(hour=self.hour_of_day)
            previous_tick = previous_tick.replace(minute=0)
            previous_tick = previous_tick.replace(second=0)
            return last_fetched_at < previous_tick


class FrequencyWeekly(Enabled):
    def __init__(self, day_of_week: str, hour_of_day: int, enabled: bool = True) -> None:
        super().__init__(enabled)
        self.day_of_week = day_of_week
        self.hour_of_day = hour_of_day

    def should_fetch(self, last_fetched_at: datetime, now: datetime) -> bool:
        frequency_day_of_week = list(calendar.day_name).index(self.day_of_week) + 1
        if not last_fetched_at:
            return now.hour == self.hour_of_day and now.isoweekday() == frequency_day_of_week
        else:
            previous_tick = now
            # if we are on scheduled day but before the mark, we need to go back in time to find previous tick
            # next loop is forced
            if previous_tick.hour < self.hour_of_day and previous_tick.isoweekday() == frequency_day_of_week:
                previous_tick = previous_tick - timedelta(days=1)
            while previous_tick.isoweekday() != frequency_day_of_week:
                previous_tick = previous_tick - timedelta(days=1)
            previous_tick = previous_tick.replace(hour=self.hour_of_day)
            previous_tick = previous_tick.replace(minute=0)
            previous_tick = previous_tick.replace(second=0)
            return last_fetched_at < previous_tick


class FrequencyMonthly(Enabled):
    def __init__(self, day_of_month: int, hour_of_day: int, enabled: bool = True) -> None:
        super().__init__(enabled)
        self.day_of_month = day_of_month
        self.hour_of_day = hour_of_day

    def should_fetch(self, last_fetched_at: datetime, now: datetime) -> bool:
        if not last_fetched_at:
            return now.day == self.day_of_month and now.hour == self.hour_of_day
        else:
            previous_tick = now
            # if we are on scheduled day but before the mark, we need to go back in time to find previous tick
            # next loop is forced
            if previous_tick.hour < self.hour_of_day and previous_tick.day == self.day_of_month:
                previous_tick = previous_tick - timedelta(days=1)
            while previous_tick.day != self.day_of_month:
                previous_tick = previous_tick - timedelta(days=1)
            previous_tick = previous_tick.replace(hour=self.hour_of_day)
            previous_tick = previous_tick.replace(minute=0)
            previous_tick = previous_tick.replace(second=0)
            return last_fetched_at < previous_tick


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
    def exists(cls, data_source_id: str) -> bool:
        return mongo.db[Contributor.mongo_collection].find_one({'data_sources.id': data_source_id}) is not None

    @classmethod
    def get_data_format(cls, data_source_id: str) -> str:
        raw = mongo.db[Contributor.mongo_collection].find_one({'data_sources.id': data_source_id})
        data_source = next(data_source for data_source in raw['data_sources'] if data_source['id'] == data_source_id)
        return data_source['data_format']

    @classmethod
    def get_one(cls, data_source_id: str) -> 'DataSource':
        try:
            return cls.get_contributor_of_data_source(data_source_id).get_data_source(data_source_id)
        except EntityNotFound:
            try:
                return cls.get_coverage_of_data_source(data_source_id).get_data_source(data_source_id)
            except EntityNotFound:
                raise EntityNotFound("data source '{}' not found in contributors or coverages".format(data_source_id))

    @classmethod
    def get_owner_of_data_source(cls, data_source_id: str, model: Union[Type['Contributor'], Type['Coverage']]) \
            -> Union['Contributor', 'Coverage']:
        raw = mongo.db[model.mongo_collection].find_one({'data_sources.id': data_source_id})

        if not raw:
            raise EntityNotFound(
                "{} of data source '{}' not found".format(model.label.lower(), data_source_id))
        return raw

    @classmethod
    def get_coverage_of_data_source(cls, data_source_id: str) -> 'Coverage':
        return MongoCoverageSchema(strict=True).load(cls.get_owner_of_data_source(data_source_id, Coverage)).data

    @classmethod
    def get_contributor_of_data_source(cls, data_source_id: str) -> 'Contributor':
        return MongoContributorSchema(strict=True).load(cls.get_owner_of_data_source(data_source_id, Contributor)).data

    def add_data_set_and_update_owner(self, data_set: DataSet, owner: Union['Contributor', 'Coverage']) -> None:
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
        owner.update()

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
        return self.is_auto() and \
               not Job.data_source_has_exports_running(self.get_contributor_of_data_source(self.id).id, self.id) and \
               self.input.frequency.should_fetch(self.fetch_started_at, datetime.now(pytz.utc))


class Process(SequenceContainer):
    def __init__(self, id: Optional[str] = None, sequence: int = 0, enabled: bool = True) -> None:
        super().__init__(sequence)
        self.id = str(uuid.uuid4()) if not id else id
        self.enabled = enabled
        self.type = self.__class__.__name__.replace('Process', '')

    def __repr__(self) -> str:
        return str(vars(self))


class OldProcess(Process):
    def __init__(self, id: Optional[str] = None, params: Optional[dict] = None,
                 sequence: int = 0, data_source_ids: Optional[List[str]] = None,
                 enabled: bool = True) -> None:
        super().__init__(id, sequence, enabled)
        self.data_source_ids = data_source_ids if data_source_ids else []
        self.params = params if params else {}

    def __repr__(self) -> str:
        return str(vars(self))


class ConfigurationDataSource(object):
    def __init__(self, name: str, ids: List[str]) -> None:
        self.ids = ids
        self.id = ids[0] if len(ids) == 1 else None
        self.name = name


class NewProcess(Process):
    def __init__(self, id: Optional[str] = None,
                 configuration_data_sources: Optional[List[ConfigurationDataSource]] = None,
                 sequence: int = 0, input_data_source_ids: Optional[List[str]] = None,
                 target_data_source_id: Optional[str] = None,
                 enabled: bool = True) -> None:
        super().__init__(id, sequence, enabled)
        self.configuration_data_sources = configuration_data_sources if configuration_data_sources else []
        self.input_data_source_ids = input_data_source_ids if input_data_source_ids else []
        self.target_data_source_id = target_data_source_id
        self.target_data_format = DATA_FORMAT_DEFAULT

    def __repr__(self) -> str:
        return str(vars(self))


class ComputeDirectionsProcess(NewProcess):
    pass


class GtfsAgencyFileProcessParameters:
    def __init__(self, agency_id: str = None, agency_name: str = None, agency_url: str = None,
                 agency_timezone: str = None, agency_lang: str = None, agency_phone: str = None,
                 agency_email: str = None, agency_fare_url: str = None) -> None:
        self.agency_id = agency_id
        self.agency_name = agency_name
        self.agency_url = agency_url
        self.agency_timezone = agency_timezone
        self.agency_lang = agency_lang
        self.agency_phone = agency_phone
        self.agency_email = agency_email
        self.agency_fare_url = agency_fare_url

    def apply_to_file_dict(self, file_dict: Dict[str, str]) -> Dict[str, str]:
        default = {
            'agency_url': "https://www.navitia.io/",
            'agency_timezone': "Europe/Paris",
        }
        return dict((key, value) if value else (key, file_dict.get(key, default.get(key))) for key, value in
                    self.__dict__.items())


class GtfsAgencyFileProcess(NewProcess):
    def __init__(self, id: Optional[str] = None,
                 configuration_data_sources: Optional[List[ConfigurationDataSource]] = None,
                 sequence: int = 0, input_data_source_ids: Optional[List[str]] = None,
                 target_data_source_id: Optional[str] = None,
                 enabled: bool = True, parameters: GtfsAgencyFileProcessParameters = None) -> None:
        super().__init__(id, configuration_data_sources, sequence, input_data_source_ids, target_data_source_id,
                         enabled)
        self.parameters = parameters


class ComputeODSProcess(NewProcess):
    def __init__(self, id: Optional[str] = None,
                 configuration_data_sources: Optional[List[ConfigurationDataSource]] = None,
                 sequence: int = 0, input_data_source_ids: Optional[List[str]] = None,
                 target_data_source_id: Optional[str] = None,
                 enabled: bool = True) -> None:
        super().__init__(id, configuration_data_sources, sequence, input_data_source_ids, target_data_source_id, enabled)
        self.target_data_format = DATA_FORMAT_ODS


class ComputeExternalSettingsProcess(NewProcess):
    def __init__(self, id: Optional[str] = None,
                 configuration_data_sources: Optional[List[ConfigurationDataSource]] = None,
                 sequence: int = 0, input_data_source_ids: Optional[List[str]] = None,
                 target_data_source_id: Optional[str] = None,
                 enabled: bool = True) -> None:
        super().__init__(id, configuration_data_sources, sequence, input_data_source_ids, target_data_source_id,
                         enabled)
        self.target_data_format = DATA_FORMAT_PT_EXTERNAL_SETTINGS


class Gtfs2NtfsProcess(OldProcess):
    pass


class HeadsignShortNameProcess(NewProcess):
    pass


class RuspellProcess(NewProcess):
    pass


class SleepingProcess(OldProcess):
    pass


class FusioDataUpdateProcess(OldProcess):
    pass


class FusioExportProcess(OldProcess):
    pass


class FusioExportContributorProcess(OldProcess):
    pass


class FusioImportProcess(OldProcess):
    pass


class FusioPreProdProcess(OldProcess):
    pass


class FusioSendPtExternalSettingsProcess(OldProcess):
    pass


class Contributor(DataSourceAndProcessContainer):
    mongo_collection = 'contributors'
    label = 'Contributor'

    def __init__(self, id: str, name: str, data_prefix: str, data_sources: List[DataSource] = None,
                 processes: List[Process] = None, data_type: str = DATA_TYPE_DEFAULT) -> None:
        super(Contributor, self).__init__(processes, data_sources)
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
        def handle_contributor_query_result(contributors_using_result: List[Contributor]) -> None:
            if contributors_using_result:
                contributors_ids = [contributor.id for contributor in contributors_using_result if
                                    contributor.id != self.id]
                if contributors_ids:
                    raise IntegrityException(
                        'unable to delete contributor {} because the following contributors are using one of its data sources: {}'.format(
                            self.id, ', '.join(contributors_ids)
                        ))

        contributors_using = self.find({
            'processes.params.links.contributor_id': self.id
        })
        handle_contributor_query_result(contributors_using)

        new_contributors_using = self.find({
            '$or': [
                {'processes.input_data_source_ids': {'$in': [data_source.id for data_source in self.data_sources]}},
                {'processes.configuration_data_sources.ids': {
                    '$in': [data_source.id for data_source in self.data_sources]}},
            ]
        })
        handle_contributor_query_result(new_contributors_using)

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
        return MongoContributorSchema(many=True, strict=True).load(list(raw)).data

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
        try:
            return next(data_source for data_source in self.data_sources if data_source.id == data_source_id)
        except StopIteration:
            msg = "data source '{}' not found for contributor '{}'".format(data_source_id, self.id)
            logging.getLogger(__name__).error(msg)
            raise EntityNotFound(msg)

    def is_geographic(self) -> bool:
        return self.data_type == DATA_TYPE_GEOGRAPHIC


class Coverage(DataSourceAndProcessContainer):
    mongo_collection = 'coverages'
    label = 'Coverage'

    def __init__(self, id: str, name: str, environments: Dict[str, Environment] = None,
                 input_data_source_ids: List[str] = None, license: License = None,
                 processes: List[Process] = None, data_sources: List[DataSource] = None,
                 type: str = 'other', short_description: str = '', comment: str = '') -> None:
        super(Coverage, self).__init__(processes)
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
                            .get_publication_platform_for_type_with_user(platform.options.authent.username)
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
    day_of_week = fields.String(required=True)

    @post_load
    def make(self, data: dict) -> FrequencyWeekly:
        return FrequencyWeekly(**data)

    @validates('day_of_week')
    def validates_day_of_week(self, day_of_week: str) -> None:
        if day_of_week not in calendar.day_name:
            raise ValidationError("day_of_week should be one of {}".format(', '.join(calendar.day_name)))


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


class MongoGenericProcessSchema(EnabledSchema):
    id = fields.String(required=True)
    sequence = fields.Integer(required=True)


class MongoConfigurationDataSource(Schema):
    name = fields.String(required=True)
    ids = fields.List(fields.String(), required=True)

    @post_load
    def build_configuration(self, data: dict) -> ConfigurationDataSource:
        return ConfigurationDataSource(**data)


class MongoNewProcessSchema(MongoGenericProcessSchema):
    input_data_source_ids = fields.List(fields.String(), required=True)
    target_data_source_id = fields.String(required=False, allow_none=True)
    configuration_data_sources = fields.List(fields.Nested(MongoConfigurationDataSource), required=False,
                                             allow_none=True)

    @staticmethod
    def check_configuration_data_source_contains_only(configuration_data_sources: List[ConfigurationDataSource],
                                                      configuration_data_source_names_mandatory_expected: List[str],
                                                      configuration_data_source_names_optional_expected: List[
                                                          str] = None) -> None:
        configuration_data_source_names_optional_expected = configuration_data_source_names_optional_expected if \
            configuration_data_source_names_optional_expected else []
        configuration_names = [config.name for config in configuration_data_sources]
        if not configuration_data_source_names_optional_expected:
            if configuration_names != configuration_data_source_names_mandatory_expected:
                raise ValidationError(
                    'configuration_data_sources should contain a "{}" data source and only that'.format(
                        '" and a "'.join(configuration_data_source_names_mandatory_expected)))
        else:
            if set(configuration_data_source_names_mandatory_expected).issubset(configuration_names):
                optional_found = set(configuration_names) - set(configuration_data_source_names_mandatory_expected)
                if optional_found.issubset(configuration_data_source_names_optional_expected):
                    return
            raise ValidationError(
                'configuration_data_sources should contain a "{}" data source and possibly some of "{}" data source'.format(
                    '" and a "'.join(configuration_data_source_names_mandatory_expected),
                    ', '.join(configuration_data_source_names_optional_expected)))

    @validates('input_data_source_ids')
    def validate_input_data_source_ids(self, input_data_source_ids: List[str]) -> None:
        if len(input_data_source_ids) != 1:
            raise ValidationError('input_data_source_ids should contains one and only one data source id')


class MongoOldProcessSchema(MongoGenericProcessSchema):
    params = fields.Dict(required=False)
    data_source_ids = fields.List(fields.String(), required=False)

    @post_load
    def build_process(self, data: dict) -> OldProcess:
        return OldProcess(**data)


class MongoGtfsAgencyFileProcessParametersSchema(Schema):
    agency_id = fields.String(required=False, allow_none=True)
    agency_name = fields.String(required=False, allow_none=True)
    agency_url = fields.Url(required=False, allow_none=True)
    agency_timezone = fields.String(required=False, allow_none=True)
    agency_lang = fields.String(required=False, allow_none=True)
    agency_phone = fields.String(required=False, allow_none=True)
    agency_fare_url = fields.Url(required=False, allow_none=True)
    agency_email = fields.Email(required=False, allow_none=True)

    @post_load
    def build_parameters(self, data: dict) -> GtfsAgencyFileProcessParameters:
        return GtfsAgencyFileProcessParameters(**data)


class MongoGtfsAgencyFileProcessSchema(MongoNewProcessSchema):
    parameters = fields.Nested(MongoGtfsAgencyFileProcessParametersSchema, required=False, allow_none=True)

    @post_load
    def build_process(self, data: dict) -> GtfsAgencyFileProcess:
        return GtfsAgencyFileProcess(**data)


class MongoGtfs2NtfsProcessSchema(MongoOldProcessSchema):
    @post_load
    def build_process(self, data: dict) -> Gtfs2NtfsProcess:
        return Gtfs2NtfsProcess(**data)


class MongoHeadsignShortNameProcessSchema(MongoNewProcessSchema):
    @post_load
    def build_process(self, data: dict) -> HeadsignShortNameProcess:
        return HeadsignShortNameProcess(**data)


class MongoRuspellProcessSchema(MongoNewProcessSchema):
    configuration_data_sources = fields.List(fields.Nested(MongoConfigurationDataSource), required=True)

    @validates('configuration_data_sources')
    def validate_configuration_data_sources(self, configuration_data_sources: List[ConfigurationDataSource]) -> None:
        self.check_configuration_data_source_contains_only(configuration_data_sources, ['ruspell_config'],
                                                           ['geographic_data'])

    @post_load
    def build_process(self, data: dict) -> RuspellProcess:
        return RuspellProcess(**data)


class MongoSleepingProcessSchema(MongoOldProcessSchema):
    @post_load
    def build_process(self, data: dict) -> SleepingProcess:
        return SleepingProcess(**data)


class MongoComputeExternalSettingsProcessSchema(MongoNewProcessSchema):
    target_data_source_id = fields.String(required=True)
    configuration_data_sources = fields.List(fields.Nested(MongoConfigurationDataSource), required=True)

    @post_load
    def build_process(self, data: dict) -> ComputeExternalSettingsProcess:
        return ComputeExternalSettingsProcess(**data)

    @validates('configuration_data_sources')
    def validate_configuration_data_sources(self, configuration_data_sources: List[ConfigurationDataSource]) -> None:
        self.check_configuration_data_source_contains_only(configuration_data_sources,
                                                           ['perimeter', 'lines_referential'])


class MongoFusioDataUpdateProcessSchema(MongoOldProcessSchema):
    @post_load
    def build_process(self, data: dict) -> FusioDataUpdateProcess:
        return FusioDataUpdateProcess(**data)


class MongoFusioExportProcessSchema(MongoOldProcessSchema):
    @post_load
    def build_process(self, data: dict) -> FusioExportProcess:
        return FusioExportProcess(**data)


class MongoFusioExportContributorProcessSchema(MongoOldProcessSchema):
    @post_load
    def build_process(self, data: dict) -> FusioExportContributorProcess:
        return FusioExportContributorProcess(**data)


class MongoFusioImportProcessSchema(MongoOldProcessSchema):
    @post_load
    def build_process(self, data: dict) -> FusioImportProcess:
        return FusioImportProcess(**data)


class MongoFusioPreProdProcessSchema(MongoOldProcessSchema):
    @post_load
    def build_process(self, data: dict) -> FusioPreProdProcess:
        return FusioPreProdProcess(**data)


class MongoFusioSendPtExternalSettingsProcessSchema(MongoOldProcessSchema):
    @post_load
    def build_process(self, data: dict) -> FusioSendPtExternalSettingsProcess:
        return FusioSendPtExternalSettingsProcess(**data)


class MongoComputeDirectionsProcessSchema(MongoNewProcessSchema):
    configuration_data_sources = fields.List(fields.Nested(MongoConfigurationDataSource), required=True)

    @post_load
    def build(self, data: dict) -> ComputeDirectionsProcess:
        return ComputeDirectionsProcess(**data)

    @validates('configuration_data_sources')
    def validate_configuration_data_sources(self, configuration_data_sources: List[ConfigurationDataSource]) -> None:
        self.check_configuration_data_source_contains_only(configuration_data_sources, ['directions'])


class MongoComputeODSProcessSchema(MongoNewProcessSchema):
    target_data_source_id = fields.String(required=True)

    @post_load
    def build(self, data: dict) -> ComputeODSProcess:
        return ComputeODSProcess(**data)

    @validates('input_data_source_ids')
    def validate_input_data_source_ids(self, input_data_source_ids: List[str]) -> None:
        if not input_data_source_ids:
            raise ValidationError('input_data_source_ids should contains more than one data source id')


class MongoProcessSchema(OneOfSchema):
    type_schemas = {
        'ComputeDirections': MongoComputeDirectionsProcessSchema,
        'GtfsAgencyFile': MongoGtfsAgencyFileProcessSchema,
        'ComputeExternalSettings': MongoComputeExternalSettingsProcessSchema,
        'Gtfs2Ntfs': MongoGtfs2NtfsProcessSchema,
        'HeadsignShortName': MongoHeadsignShortNameProcessSchema,
        'Ruspell': MongoRuspellProcessSchema,
        'Sleeping': MongoSleepingProcessSchema,
        'FusioDataUpdate': MongoFusioDataUpdateProcessSchema,
        'FusioExport': MongoFusioExportProcessSchema,
        'FusioExportContributor': MongoFusioExportContributorProcessSchema,
        'FusioImport': MongoFusioImportProcessSchema,
        'FusioPreProd': MongoFusioPreProdProcessSchema,
        'FusioSendPtExternalSettings': MongoFusioSendPtExternalSettingsProcessSchema,
        'ComputeODS': MongoComputeODSProcessSchema,
    }

    def get_obj_type(self, obj: Process) -> str:
        if isinstance(obj, ComputeDirectionsProcess):
            return 'ComputeDirections'
        elif isinstance(obj, GtfsAgencyFileProcess):
            return 'GtfsAgencyFile'
        elif isinstance(obj, ComputeExternalSettingsProcess):
            return 'ComputeExternalSettings'
        elif isinstance(obj, Gtfs2NtfsProcess):
            return 'Gtfs2Ntfs'
        elif isinstance(obj, HeadsignShortNameProcess):
            return 'HeadsignShortName'
        elif isinstance(obj, RuspellProcess):
            return 'Ruspell'
        elif isinstance(obj, SleepingProcess):
            return 'Sleeping'
        elif isinstance(obj, FusioDataUpdateProcess):
            return 'FusioDataUpdate'
        elif isinstance(obj, FusioExportProcess):
            return 'FusioExport'
        elif isinstance(obj, FusioExportContributorProcess):
            return 'FusioExportContributor'
        elif isinstance(obj, FusioImportProcess):
            return 'FusioImport'
        elif isinstance(obj, FusioPreProdProcess):
            return 'FusioPreProd'
        elif isinstance(obj, FusioSendPtExternalSettingsProcess):
            return 'FusioSendPtExternalSettings'
        elif isinstance(obj, ComputeODSProcess):
            return 'ComputeODS'


class MongoCoverageSchema(Schema):
    id = fields.String(required=True, load_from='_id', dump_to='_id')
    name = fields.String(required=True)
    environments = fields.Nested(MongoEnvironmentListSchema)
    input_data_source_ids = fields.List(fields.String())
    license = fields.Nested(MongoDataSourceLicenseSchema, allow_none=True)
    processes = fields.Nested(MongoProcessSchema, many=True, required=False, allow_none=False)
    data_sources = fields.Nested(MongoDataSourceSchema, many=True, required=False, allow_none=True)
    type = CoverageType()
    short_description = fields.String()
    comment = fields.String()

    @post_load
    def make_coverage(self, data: dict) -> Coverage:
        return Coverage(**data)


class MongoContributorSchema(Schema):
    id = fields.String(required=True, load_from='_id', dump_to='_id')
    name = fields.String(required=True)
    data_prefix = fields.String(required=True)
    data_sources = fields.Nested(MongoDataSourceSchema, many=True, required=False)
    processes = fields.Nested(MongoProcessSchema, many=True, required=False)
    data_type = DataType()

    @validates_schema(pass_original=True, skip_on_field_errors=True, pass_many=True)
    def validate_contributor_process_input_data_source_ids(self, unmarshalled: Union[dict, Contributor],
                                                           contributors: Union[dict, List[dict]], many: bool) -> None:
        if not many:
            contributors = [contributors]  # type: ignore
        for contributor in contributors:
            for process in contributor.get('processes', []):
                if isinstance(process, dict):
                    if 'input_data_source_ids' in process and len(process['input_data_source_ids']) == 1:
                        data_source_id = process['input_data_source_ids'][0]
                        data_source = next((data_source for data_source in contributor.get('data_sources', []) if
                                            data_source_id == data_source['id']), None)
                        if not data_source:
                            if not DataSource.exists(data_source_id):
                                raise ValidationError(
                                    'data source referenced by "{}" in process "{}" not found'.format(
                                        data_source_id, process['type']), ['input_data_source_ids'])
                            else:
                                data_format = DataSource.get_data_format(data_source_id)
                        else:
                            data_format = data_source.get('data_format', DATA_FORMAT_DEFAULT)
                        self.validate_input_data_source_id_has_data_format(data_format, process['type'])

    @classmethod
    def validate_input_data_source_id_has_data_format(cls, data_format_found: str, process_type: str) -> None:
        if data_format_found != DATA_FORMAT_GTFS:
            raise ValidationError(
                'input data source in process "{}" should be of data format "{}", found "{}"'.format(
                    process_type, DATA_FORMAT_GTFS, data_format_found), ['input_data_source_ids'])

    @classmethod
    def validate_configuration_has_data_format(cls, configuration_key: str, data_format_found: str,
                                               process_type: str) -> None:
        config_mapping_format = {
            'directions': DATA_FORMAT_DIRECTION_CONFIG,
            'perimeter': DATA_FORMAT_TR_PERIMETER,
            'lines_referential': DATA_FORMAT_LINES_REFERENTIAL,
            'ruspell_config': DATA_FORMAT_RUSPELL_CONFIG,
            'geographic_data': [DATA_FORMAT_BANO_FILE, DATA_FORMAT_OSM_FILE],
        }
        config_mapping_format_choices = config_mapping_format[configuration_key]
        config_mapping_format_choices = config_mapping_format_choices if \
            isinstance(config_mapping_format_choices, list) else [config_mapping_format_choices]
        if configuration_key in config_mapping_format and data_format_found not in config_mapping_format_choices:
            raise ValidationError(
                'data source referenced by "{}" in process "{}" should be of data format "{}", found "{}"'.format(
                    configuration_key, process_type, ' or '.join(config_mapping_format_choices),
                    data_format_found), ['configuration_data_sources'])

    @validates_schema(pass_original=True, skip_on_field_errors=True, pass_many=True)
    def validate_contributor_process_configuration(self, unmarshalled: Union[dict, Contributor],
                                                   contributors: Union[dict, List[dict]], many: bool) -> None:
        if not many:
            contributors = [contributors]  # type: ignore
        for contributor in contributors:
            for process in contributor.get('processes', []):
                if isinstance(process, dict):
                    for configuration_data_source in process.get('configuration_data_sources', []):
                        for data_source_id in configuration_data_source.get('ids', []):
                            contributor_data_sources = contributor.get('data_sources', [])
                            if not any(data_source_id == data_source['id'] for data_source in contributor_data_sources):
                                if not DataSource.exists(data_source_id):
                                    raise ValidationError(
                                        'data source referenced by "{}" in process "{}" was not found'.format(
                                            data_source_id,
                                            process['type']),
                                        ['configuration_data_sources'])
                                else:
                                    data_format = DataSource.get_data_format(data_source_id)
                            else:
                                data_format = next(
                                    data_source['data_format'] for data_source in contributor_data_sources if
                                    data_source['id'] == data_source_id)

                            self.validate_configuration_has_data_format(configuration_data_source['name'], data_format,
                                                                        process['type'])

    @post_load
    def make_contributor(self, data: dict) -> Contributor:
        return Contributor(**data)


class Job(object):
    mongo_collection = 'jobs'

    def __init__(self, action_type: str = ACTION_TYPE_CONTRIBUTOR_EXPORT, contributor_id: str = None,
                 coverage_id: str = None, parent_id: str = None, state: str = JOB_STATUS_PENDING, step: str = None,
                 id: str = None, started_at: datetime = None, updated_at: Optional[datetime] = None,
                 error_message: str = "", data_source_id: str = None) -> None:
        self.id = id if id else str(uuid.uuid4())
        self.parent_id = parent_id
        self.action_type = action_type
        self.contributor_id = contributor_id
        self.data_source_id = data_source_id
        self.coverage_id = coverage_id
        self.step = step
        self.state = state
        self.error_message = error_message
        self.started_at = started_at if started_at else datetime.now(pytz.utc)
        self.updated_at = updated_at if updated_at else self.started_at

    def save(self) -> None:
        raw = MongoJobSchema().dump(self).data
        mongo.db[self.mongo_collection].insert_one(raw)

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
    def get_some(cls, contributor_id: str = None, coverage_id: str = None,
                 page: int = 1, per_page: int = 20) -> Tuple[List['Job'], int]:
        find_filter = {}
        if contributor_id:
            find_filter.update({'contributor_id': contributor_id})
        if coverage_id:
            find_filter.update({'coverage_id': coverage_id})
        raw = mongo.db[cls.mongo_collection].find(find_filter)
        total_number = raw.count()
        paginated = raw.sort('updated_at', -1).skip((page - 1) * per_page).limit(per_page)
        return MongoJobSchema(many=True).load(paginated).data, total_number

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
    def data_source_has_exports_running(cls, contributor_id: str, data_source_id: str) -> bool:
        filter_statuses = [{'state': status} for status in [JOB_STATUS_PENDING, JOB_STATUS_RUNNING]]
        filter = {
            'action_type': ACTION_TYPE_AUTO_CONTRIBUTOR_EXPORT,
            'contributor_id': contributor_id,
            'data_source_id': data_source_id,
            '$or': filter_statuses,
        }
        raw = mongo.db[cls.mongo_collection].find(filter)
        return raw.count() > 0

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
        self.created_at = created_at if created_at else datetime.now(pytz.utc)
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
