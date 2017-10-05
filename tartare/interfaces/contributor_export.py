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

from flask_restful import Resource, reqparse
from flask import Response

from tartare.core.context import Context
from tartare.tasks import contributor_export, finish_job
from tartare.interfaces.schema import JobSchema, ContributorExportSchema
from tartare.core.models import Contributor, Job, ContributorExport
from tartare.http_exceptions import ObjectNotFound
import logging
from celery import chain
from datetime import date


class ContributorExportResource(Resource):
    def __init__(self):
        self.parsers = dict
        self.parsers["get"] = reqparse.RequestParser()
        parser_get = self.parsers["get"]
        parser_get.add_argument("start_page", type=date, default=date.today())

    @staticmethod
    def _export(contributor: Contributor) -> Job:
        job = Job(contributor_id=contributor.id, action_type="contributor_export")
        job.save()
        try:
            chain(contributor_export.si(Context(), contributor, job, False), finish_job.si(job.id)).delay()
        except Exception as e:
            # Exception when celery tasks aren't deferred, they are executed locally by blocking
            logging.getLogger(__name__).error('Error : {}'.format(str(e)))
        return job

    def post(self, contributor_id: str) -> Response:
        contributor = Contributor.get(contributor_id)
        if not contributor:
            msg = 'Contributor not found: {}'.format(contributor_id)
            logging.getLogger(__name__).error(msg)
            raise ObjectNotFound(msg)

        job = self._export(contributor)
        job_schema = JobSchema(strict=True)
        return {'job': job_schema.dump(job).data}, 201

    def get(self, contributor_id: str) -> Response:
        contributor = Contributor.get(contributor_id)
        if not contributor:
            msg = 'Contributor not found: {}'.format(contributor_id)
            logging.getLogger(__name__).error(msg)
            raise ObjectNotFound(msg)
        exports = ContributorExport.get(contributor_id=contributor.id)
        return {'exports': ContributorExportSchema(many=True, strict=True).dump(exports).data}, 200
