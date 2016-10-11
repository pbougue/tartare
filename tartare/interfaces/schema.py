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
from functools import wraps
from flask_restful import unpack
from marshmallow import Schema, fields, post_load, validates_schema, ValidationError
from tartare.core.models import MongoCoverageSchema, Coverage, MongoCoverageTechnicalConfSchema
from tartare.core.models import MongoContributorSchema
import os
from tartare import app


class serialize_with(object):
    def __init__(self, serializer):
        self.serializer = serializer

    def __call__(self, f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            resp = f(*args, **kwargs)
            if isinstance(resp, tuple):
                data, code, headers = unpack(resp)
                return self.serializer.dump(data), code, headers
            return self.serializer.dump(resp)
        return wrapper


class NoUnknownFieldMixin(Schema):
    @validates_schema(pass_original=True)
    def check_unknown_fields(self, data, original_data):
        for key in original_data:
            if key not in self.fields:
                raise ValidationError('Unknown field name {}'.format(key))


class CoverageTechnicalConfSchema(MongoCoverageTechnicalConfSchema, NoUnknownFieldMixin):
    #we just need NoUnknownFieldMixin for validation purpose
    pass

class CoverageSchema(MongoCoverageSchema, NoUnknownFieldMixin):
    id = fields.String(required=True)
    #we have to override nested field to add validation on input
    technical_conf = fields.Nested(CoverageTechnicalConfSchema)


    @post_load
    def make_coverage(self, data):
        """
        we override the make coverage from the schema model, this way we can add some specific logic
        This method need to have the same name as the one in the modelSchema else they will both be called
        """
        def _default_dir(var, coverage_id):
            return os.path.join(app.config.get(var), coverage_id) if coverage_id else None

        if 'technical_conf' not in data:
            data['technical_conf'] = Coverage.TechnicalConfiguration()
        for arg, env_var in (('input_dir', 'INPUT_DIR'),
                             ('output_dir', 'OUTPUT_DIR'),
                             ('current_data_dir', 'CURRENT_DATA_DIR')):
            setattr(data['technical_conf'], arg, getattr(data.get('technical_conf', {}), arg) \
                                                 or _default_dir(env_var, data['id']))
        return Coverage(**data)

class ContributorSchema(MongoContributorSchema, NoUnknownFieldMixin):
    id = fields.String()

