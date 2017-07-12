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
from tartare.processes.processes import AbstractProcess
from tartare.processes.fusio import Fusio
from tartare.core.gridfs_handler import GridFsHandler
import requests
from datetime import date


class FusioDataUpdate(AbstractProcess):

    @staticmethod
    def _get_files(gridfs_id: str):
        return {
            "filename": GridFsHandler().get_file_from_gridfs(gridfs_id)
        }

    @staticmethod
    def _format_date(_date: date, fromat: str='%d/%m/%Y') -> str:
        return _date.strftime(fromat)

    def _get_data(self, contributor_export):
        validity_period = contributor_export.validity_period
        return {
            "action": 'dataupdate',
            'contributorexternalcode': contributor_export.contributor_id,
            'isadapted': 0,
            'dutype': 'update',
            'serviceexternalcode': contributor_export.data_sources[0],
            'libelle': 'unlibelle',
            'DateDebut': self._format_date(validity_period.start_date),
            'DateFin': self._format_date(validity_period.start_date),
            'content-type': 'multipart/form-data',
        }

    def do(self):
        for contributor_export in self.context.contributor_exports:
            if not contributor_export.gridfs_id:
                continue
            fusio = Fusio(self.params.get("url"))
            resp = fusio.call(requests.post, api='api',
                              data=self._get_data(contributor_export),
                              files=self._get_files(contributor_export.gridfs_id))
            fusio.wait_for_action_terminated(fusio.get_action_id(resp.content))
        return self.context


class FusioImport(AbstractProcess):

    def do(self):
        return self.context


class FusioPreProd(AbstractProcess):

    def do(self):
        return self.context


class FusioExport(AbstractProcess):

    def do(self):
        return self.context

