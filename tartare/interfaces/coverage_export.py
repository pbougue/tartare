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

import flask_restful
from tartare.tasks import coverage_export
from tartare.interfaces.schema import JobSchema
from tartare.core.models import Job, Coverage, CoverageExport
import uuid
from tartare.exceptions import ObjectNotFound
from tartare.interfaces.schema import CoverageExportSchema


class CoverageExportResource(flask_restful.Resource):
    @staticmethod
    def _export(coverage):
        job = Job(id=str(uuid.uuid4()), coverage_id=coverage.id, action_type="coverage_export")
        job.save()
        coverage_export.delay(coverage, job)
        return job

    def post(self, coverage_id):
        coverage = Coverage.get(coverage_id)
        if not coverage:
            raise ObjectNotFound('Coverage not found: {}'.format(coverage_id))
        job = self._export(coverage)
        job_schema = JobSchema(strict=True)
        return {'job': job_schema.dump(job).data}, 201

    def get(self, coverage_id):
        coverage = Coverage.get(coverage_id)
        if not coverage:
            raise ObjectNotFound('Coverage not found: {}'.format(coverage_id))
        exports = CoverageExport.get(coverage_id=coverage.id)
        return {'exports': CoverageExportSchema(many=True, strict=True).dump(exports).data}, 200
