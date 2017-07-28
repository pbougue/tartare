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

from tartare.exceptions import IntegrityException, FusioException
from tartare.processes.processes import AbstractProcess
from tartare.processes.fusio import Fusio
from tartare.core.gridfs_handler import GridFsHandler
import requests
from tartare.core.models import Contributor
from tartare.core.context import Context, DataSourceContext
from tartare.helper import download_zip_file, get_filename
import tempfile


class FusioDataUpdate(AbstractProcess):

    @staticmethod
    def _get_files(gridfs_id: str) -> dict:
        return {
            "filename": GridFsHandler().get_file_from_gridfs(gridfs_id)
        }

    def _get_data(self, contributor: Contributor, data_source_context: DataSourceContext) -> dict:
        validity_period = data_source_context.validity_period
        return {
            'action': 'dataupdate',
            'contributorexternalcode': contributor.data_prefix,
            'isadapted': 0,
            'dutype': 'update',
            'serviceexternalcode': data_source_context.data_source_id,
            'libelle': 'unlibelle',
            'DateDebut': Fusio.format_date(validity_period.start_date),
            'DateFin': Fusio.format_date(validity_period.end_date),
            'content-type': 'multipart/form-data',
        }

    def do(self) -> Context:
        fusio = Fusio(self.params.get("url"))
        for contributor_context in self.context.contributors_context:
            for data_source_context in contributor_context.data_source_contexts:
                if not data_source_context.gridfs_id:
                    continue
                resp = fusio.call(requests.post, api='api',
                                  data=self._get_data(contributor_context.contributor, data_source_context),
                                  files=self._get_files(data_source_context.gridfs_id))
                fusio.wait_for_action_terminated(fusio.get_action_id(resp.content))
        return self.context


class FusioImport(AbstractProcess):
    def _get_period_bounds(self) -> tuple:
        min_contributor = min(self.context.contributors_context,
                              key=lambda contrib: contrib.validity_period.start_date)

        max_contributor = max(self.context.contributors_context,
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

    def do(self) -> Context:
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

    def do(self) -> Context:
        fusio = Fusio(self.params.get("url"))
        resp = fusio.call(requests.post, api='api', data={'action': 'settopreproduction'})
        fusio.wait_for_action_terminated(fusio.get_action_id(resp.content))
        return self.context


class FusioExport(AbstractProcess):

    def get_export_type(self) -> int:
        export_type = self.params.get('export_type', "ntfs")
        map_export_type = {
            "ntfs": 32,
            "gtfsv2": 36,
            "googletransit": 37
        }
        lower_export_type = export_type.lower()
        if lower_export_type not in map_export_type:
            msg = 'export_type {} not found'.format(lower_export_type)
            logging.getLogger(__name__).exception(msg)
            raise FusioException(msg)
        return map_export_type.get(lower_export_type)

    def save_export(self, url: str) -> Context:
        with tempfile.TemporaryDirectory() as tmp_dir_name:
            file_name = '{}/{}'.format(tmp_dir_name, get_filename(url, 'fusio'))
            download_zip_file(url, file_name)
            with open(file_name, 'rb') as file:
                self.context.global_gridfs_id = GridFsHandler().save_file_in_gridfs(file, filename=file_name)
        return self.context

    def do(self) -> Context:
        fusio = Fusio(self.params.get("url"))
        data = {
            'action': 'Export',
            'ExportType': self.get_export_type(),
            'Source': 4}
        resp = fusio.call(requests.post, api='api', data=data)
        action_id = fusio.get_action_id(resp.content)
        fusio.wait_for_action_terminated(action_id)
        return self.save_export(fusio.get_export_url(action_id))
