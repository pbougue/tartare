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
import logging

from datetime import datetime, timedelta

from tartare.exceptions import IntegrityException
from tartare.processes.processes import AbstractProcess
from tartare.processes.fusio import Fusio
from tartare.core.gridfs_handler import GridFsHandler
import requests
from datetime import date
from tartare.core.models import ContributorExport
from tartare.core.context import Context


class FusioDataUpdate(AbstractProcess):
    @staticmethod
    def _get_files(gridfs_id: str) -> dict:
        return {
            "filename": GridFsHandler().get_file_from_gridfs(gridfs_id)
        }

    def _get_data(self, contributor_export: ContributorExport) -> dict:
        validity_period = contributor_export.validity_period
        return {
            'action': 'dataupdate',
            'contributorexternalcode': contributor_export.contributor_id,
            'isadapted': 0,
            'dutype': 'update',
            'serviceexternalcode': contributor_export.data_sources[0].data_source_id,
            'libelle': 'unlibelle',
            'DateDebut': Fusio.format_date(validity_period.start_date),
            'DateFin': Fusio.format_date(validity_period.end_date),
            'content-type': 'multipart/form-data',
        }

    def do(self) -> Context:
        fusio = Fusio(self.params.get("url"))
        for contributor_export in self.context.contributor_exports:
            if not contributor_export.gridfs_id:
                continue
            resp = fusio.call(requests.post, api='api',
                              data=self._get_data(contributor_export),
                              files=self._get_files(contributor_export.gridfs_id))
            fusio.wait_for_action_terminated(fusio.get_action_id(resp.content))
        return self.context


class FusioImport(AbstractProcess):
    def _get_period_bounds(self) -> tuple:
        min_contributor = min(self.context.contributor_exports,
                              key=lambda contrib: contrib.validity_period.start_date)

        max_contributor = max(self.context.contributor_exports,
                              key=lambda contrib: contrib.validity_period.end_date)
        begin_date = min_contributor.validity_period.start_date
        end_date = max_contributor.validity_period.end_date
        now_date = datetime.now().date()
        if end_date < now_date:
            raise IntegrityException('bounds date from fusio import incorrect (end_date: {end} < now: {now})'.format(
                end=Fusio.format_date(end_date), now=Fusio.format_date(now_date)))
        if abs(begin_date - end_date).days > 365:
            logging.getLogger(__name__).warning(
                'period bounds for union of contributors validity periods exceed one year')
            begin_date = max(begin_date, now_date)
            end_date = min(begin_date + timedelta(days=364), end_date)
        return begin_date, end_date

    def do(self):
        fusio = Fusio(self.params.get("url"))
        begin_date, end_date = self._get_period_bounds()
        resp = fusio.call(requests.post, api='api',
                          data={
                              'DateDebut': Fusio.format_date(begin_date),
                              'DateFin': Fusio.format_date(end_date),
                              'action': 'regionalimport',
                          })
        fusio.wait_for_action_terminated(fusio.get_action_id(resp.content))
        return self.context


class FusioPreProd(AbstractProcess):
    def do(self):
        fusio = Fusio(self.params.get("url"))
        resp = fusio.call(requests.post, api='api', data={'action': 'settopreproduction'})
        fusio.wait_for_action_terminated(fusio.get_action_id(resp.content))
        return self.context


class FusioExport(AbstractProcess):
    def do(self):
        return self.context
