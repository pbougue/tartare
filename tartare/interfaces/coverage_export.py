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
from flask import Response

from tartare.core.constants import ACTION_TYPE_COVERAGE_EXPORT
from tartare.core.context import Context
from tartare.interfaces.common_argrs import CommonArgs
from tartare.tasks import coverage_export, finish_job
from tartare.interfaces.schema import JobSchema
from tartare.core.models import Job, Coverage, CoverageExport
from tartare.http_exceptions import ObjectNotFound
from tartare.interfaces.schema import CoverageExportSchema
import logging
from celery import chain


class CoverageExportResource(flask_restful.Resource, CommonArgs):
    def _export(self, coverage: Coverage) -> Job:
        job = Job(coverage_id=coverage.id, action_type=ACTION_TYPE_COVERAGE_EXPORT)
        job.save()
        try:
            coverage_export.si(Context('coverage', job, coverage, current_date=self.get_current_date())).delay()
        except Exception as e:
            # Exception when celery tasks aren't deferred, they are executed locally by blocking
            logging.getLogger(__name__).error('Error : {}'.format(str(e)))
        return job

    def post(self, coverage_id: str) -> Response:
        coverage = Coverage.get(coverage_id)
        if not coverage:
            msg = 'coverage not found: {}'.format(coverage_id)
            logging.getLogger(__name__).error(msg)
            raise ObjectNotFound(msg)
        job = self._export(coverage)
        job_schema = JobSchema(strict=True)
        return {'job': job_schema.dump(job).data}, 201

    def get(self, coverage_id: str) -> Response:
        coverage = Coverage.get(coverage_id)
        if not coverage:
            msg = 'coverage not found: {}'.format(coverage_id)
            logging.getLogger(__name__).error(msg)
            raise ObjectNotFound(msg)

        exports = CoverageExport.get(coverage_id=coverage.id)
        return {'exports': CoverageExportSchema(many=True, strict=True).dump(exports).data}, 200
