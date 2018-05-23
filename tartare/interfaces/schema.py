# coding: utf-8

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
from typing import Optional, List

from marshmallow import Schema, fields, post_load, validates_schema, ValidationError, post_dump, validate

from tartare.core.constants import ACTION_TYPE_COVERAGE_EXPORT, ACTION_TYPE_AUTO_COVERAGE_EXPORT, \
    ACTION_TYPE_AUTO_CONTRIBUTOR_EXPORT
from tartare.core.models import Job, MongoValidityPeriodSchema, DataSourceStatus, MongoDataSetSchema
from tartare.core.models import MongoContributorSchema, MongoDataSourceSchema, MongoJobSchema, MongoPreProcessSchema, \
    MongoContributorExportSchema, MongoCoverageExportSchema
from tartare.core.models import MongoCoverageSchema, Coverage, MongoEnvironmentSchema, MongoEnvironmentListSchema, \
    MongoPlatformSchema

not_blank = validate.Length(min=1, error='field cannot be empty')


class NoUnknownFieldMixin(Schema):
    @validates_schema(pass_original=True)
    def check_unknown_fields(self, data: dict, original_data: dict) -> None:
        for key in original_data:
            if key not in self.fields:
                raise ValidationError('unknown field name {}'.format(key))


class PlatformSchema(MongoPlatformSchema):
    @post_dump()
    def remove_password(self, data: dict) -> dict:
        try:
            if data.get('options').get('authent').get('password'):
                data['options']['authent'].pop('password')
        except AttributeError:
            pass
        return data


class EnvironmentSchema(MongoEnvironmentSchema, NoUnknownFieldMixin):
    publication_platforms = fields.Nested(PlatformSchema, many=True)
    current_ntfs_id = fields.String(allow_none=True, dump_only=True)


class EnvironmentListSchema(MongoEnvironmentListSchema, NoUnknownFieldMixin):
    production = fields.Nested(EnvironmentSchema, allow_none=True)
    preproduction = fields.Nested(EnvironmentSchema, allow_none=True)
    integration = fields.Nested(EnvironmentSchema, allow_none=True)


class CoverageSchema(MongoCoverageSchema, NoUnknownFieldMixin):
    id = fields.String(required=True, validate=not_blank)
    # we have to override nested field to add validation on input
    environments = fields.Nested(EnvironmentListSchema)
    # read only
    grid_calendars_id = fields.String(dump_only=True)

    @post_load
    def make_coverage(self, data: dict) -> Coverage:
        return Coverage(**data)

    @post_dump
    def add_last_active_job(self, data: dict) -> dict:
        def job_get_last(is_coverage: bool, id: str, action_types: List[str]) -> Optional['Job']:
            filter = {
                'action_type': {'$in': action_types},
                'coverage_id' if is_coverage else 'contributor_id': id
            }

            return Job.get_last(filter)

        def get_last_active_job(data: dict) -> Optional['Job']:
            job_coverage = job_get_last(True, data['id'],
                                        [ACTION_TYPE_COVERAGE_EXPORT, ACTION_TYPE_AUTO_COVERAGE_EXPORT])

            # if a coverage export is launched, no contributor export is done so we return the last coverage's job
            # -------------------------------------- Coverage export ---------------------------------------------------
            # --------- no contributor export ------------ | -------- coverage export 20/11/2017 -----------------------
            if job_coverage and job_coverage.action_type == ACTION_TYPE_COVERAGE_EXPORT:
                return job_coverage

            for contributor_id in data['contributors_ids']:
                job_contributor = job_get_last(False, contributor_id, [ACTION_TYPE_AUTO_CONTRIBUTOR_EXPORT])
                if job_contributor:
                    if job_coverage:
                        # ----------------------------------- Automatic update -----------------------------------------
                        # ------- contributor export 23/11/2017 ---- | ------ existing coverage export 20/11/2017 ------
                        if job_contributor.has_failed() and job_contributor.started_at > job_coverage.started_at:
                            return job_contributor

                    # No coverage export has succeeded
                    # ------------------------------------ Automatic update --------------------------------------------
                    # --------- contributor export failed -----------| ---------------- no coverage export -------------
                    elif job_contributor.has_failed():
                        return job_contributor

            return job_coverage

        last_active_job = get_last_active_job(data)
        data['last_active_job'] = None if last_active_job is None else JobSchema(strict=True).dump(last_active_job).data

        return data


class DataSourceSchema(MongoDataSourceSchema):
    id = fields.String()

    @post_dump()
    def add_calculated_fields_for_data_source(self, data: dict) -> dict:
        data_source_status = DataSourceStatus(data['id'], data['data_sets'])
        data_source_status_dict = {
            'status': data_source_status.status,
            'fetch_started_at': data_source_status.fetch_started_at,
            'updated_at': data_source_status.updated_at,
            'validity_period': data_source_status.validity_period,
        }
        data.update(data_source_status_dict)

        return data


class ContributorSchema(MongoContributorSchema):
    id = fields.String(validate=not_blank)

    data_sources = fields.Nested(DataSourceSchema, many=True, required=False)


class JobSchema(MongoJobSchema, NoUnknownFieldMixin):
    id = fields.String()


class PreProcessSchema(MongoPreProcessSchema, NoUnknownFieldMixin):
    id = fields.String()


class ContributorExportSchema(MongoContributorExportSchema, NoUnknownFieldMixin):
    id = fields.String()


class CoverageExportSchema(MongoCoverageExportSchema, NoUnknownFieldMixin):
    id = fields.String()


class ValidityPeriodSchema(MongoValidityPeriodSchema, NoUnknownFieldMixin):
    pass


class DataSetSchema(MongoDataSetSchema, NoUnknownFieldMixin):
    id = fields.String()
