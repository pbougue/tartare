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
from typing import Optional

import flask_restful
from flask import Response

from tartare.core import models
from tartare.http_exceptions import ObjectNotFound
from tartare.interfaces.common_argrs import Pagination
from tartare.interfaces.schema import JobSchema


class Job(flask_restful.Resource, Pagination):
    def get(self, contributor_id: Optional[str] = None, coverage_id: Optional[str] = None,
            job_id: Optional[str] = None) -> Response:
        if job_id:
            jobs = models.Job.get_one(job_id)
            if jobs:
                return {'jobs': [JobSchema(many=False, strict=True).dump(jobs).data]}, 200
            else:
                raise ObjectNotFound('job not found: {}'.format(job_id))
        else:
            matching_jobs, total = models.Job.get_some(contributor_id=contributor_id, coverage_id=coverage_id,
                                                       page=self.get_page(), per_page=self.get_per_page())
            return {
                       'jobs': JobSchema(many=True, strict=True).dump(matching_jobs).data,
                       'pagination': {
                           'page': self.get_page(),
                           'per_page': self.get_per_page(),
                           'total': total,
                       }
                   }, 200
