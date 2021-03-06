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

import requests

from tartare.core.constants import DATA_FORMAT_PT_EXTERNAL_SETTINGS
from tartare.core.context import Context
from tartare.core.models import DataSource
from tartare.processes.abstract_process import AbstractFusioProcess
from tartare.processes.utils import process_registry


@process_registry('coverage')
class FusioSendPtExternalSettings(AbstractFusioProcess):
    def do(self) -> Context:
        for data_source_id in self.params.get('input_data_source_ids', []):
            data_source = DataSource.get_one(data_source_id)
            data_set = data_source.get_last_data_set()
            if data_source.is_of_data_format(DATA_FORMAT_PT_EXTERNAL_SETTINGS):
                resp = self.fusio.call(requests.post, api='api',
                                       data={'action': 'externalstgupdate'},
                                       files=self.get_files_from_gridfs(data_set.gridfs_id))
                self.fusio.wait_for_action_terminated(self.fusio.get_action_id(resp.content))
        return self.context
