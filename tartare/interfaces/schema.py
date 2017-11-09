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

from marshmallow import Schema, fields, post_load, validates_schema, ValidationError, post_dump
from tartare.core.models import MongoCoverageSchema, Coverage, MongoEnvironmentSchema, MongoEnvironmentListSchema, \
    DataSource
from tartare.core.models import MongoContributorSchema, MongoDataSourceSchema, MongoJobSchema, MongoPreProcessSchema, \
    MongoContributorExportSchema, MongoCoverageExportSchema, MongoDataSourceFetchedSchema


class NoUnknownFieldMixin(Schema):
    @validates_schema(pass_original=True)
    def check_unknown_fields(self, data: dict, original_data: dict) -> None:
        for key in original_data:
            if key not in self.fields:
                raise ValidationError('Unknown field name {}'.format(key))


class EnvironmentSchema(MongoEnvironmentSchema, NoUnknownFieldMixin):
    current_ntfs_id = fields.String(allow_none=True, dump_only=True)


class EnvironmentListSchema(MongoEnvironmentListSchema, NoUnknownFieldMixin):
    production = fields.Nested(EnvironmentSchema, allow_none=True)
    preproduction = fields.Nested(EnvironmentSchema, allow_none=True)
    integration = fields.Nested(EnvironmentSchema, allow_none=True)


class CoverageSchema(MongoCoverageSchema, NoUnknownFieldMixin):
    id = fields.String(required=True)
    # we have to override nested field to add validation on input
    environments = fields.Nested(EnvironmentListSchema)
    # read only
    grid_calendars_id = fields.String(dump_only=True)

    @post_load
    def make_coverage(self, data: dict) -> Coverage:
        return Coverage(**data)


class DataSourceSchema(MongoDataSourceSchema):
    id = fields.String()

    @post_dump()
    def add_calculated_fields_for_data_source(self, data: dict) -> dict:
        data['status'], data['fetch_started_at'], data['updated_at'] = DataSource.format_calculated_attributes(
            DataSource.get_calculated_attributes(data['id'])
        )

        return data


class ContributorSchema(MongoContributorSchema):
    id = fields.String()

    data_sources = fields.Nested(DataSourceSchema, many=True, required=False)


class JobSchema(MongoJobSchema, NoUnknownFieldMixin):
    id = fields.String()


class PreProcessSchema(MongoPreProcessSchema, NoUnknownFieldMixin):
    id = fields.String()


class ContributorExportSchema(MongoContributorExportSchema, NoUnknownFieldMixin):
    id = fields.String()


class CoverageExportSchema(MongoCoverageExportSchema, NoUnknownFieldMixin):
    id = fields.String()


class DataSourceFetchedSchema(MongoDataSourceFetchedSchema, NoUnknownFieldMixin):
    id = fields.String()
