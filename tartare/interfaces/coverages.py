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
from flask_restful import reqparse
import flask_restful
from pymongo.errors import PyMongoError
from tartare import mongo
import logging


class Coverage(flask_restful.Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('id', required=True, help='id is required',
                            case_sensitive=False, location=('json', 'values'))
        parser.add_argument('name', required=True,
                            case_sensitive=False, help='name is required', location=('json', 'values'))

        args = parser.parse_args()

        coverage = {
            'name': args['name'],
            '_id': args['id']
        }
        try:
            inserted_id = mongo.db.coverages.insert_one(coverage).inserted_id
        except PyMongoError as e:
            logging.getLogger(__name__).exception('impossible to add coverage {}'.format(coverage))
            return {'error': str(e)}, 400

        logging.getLogger(__name__).info("inserted id = {}".format(inserted_id))

        return {'inserted_id': str(inserted_id)}, 200

    def get(self, coverage_id=None):
        if coverage_id:
            return mongo.db.coverages.find_one_or_404({'_id': coverage_id})

        return list(mongo.db.coverages.find()), 200
