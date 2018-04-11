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
import tempfile

import requests

from tartare.core.context import Context
from tartare.core.fetcher import HttpFetcher
from tartare.core.models import Platform
from tartare.core.publisher import ProtocolManager, AbstractProtocol
from tartare.processes.abstract_preprocess import AbstractFusioProcess
from tartare.processes.fusio import Fusio
from tartare.processes.utils import preprocess_registry


@preprocess_registry('coverage')
class FusioExportContributor(AbstractFusioProcess):
    gtfs_export_type = 36
    is_adapted_value_no_strike = 0
    data_exported_type_preprod = 4

    def publish(self, protocol_uploader: AbstractProtocol, url: str) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir_name:
            dest_full_file_name, expected_file_name = HttpFetcher().fetch(
                url, tmp_dir_name, self.params.get('expected_file_name')
            )
            with open(dest_full_file_name, 'rb') as file:
                protocol_uploader.publish(file, expected_file_name)

    def do(self) -> Context:
        trigram = self.params.get('trigram')
        data = {
            'action': 'Export',
            'ExportType': self.gtfs_export_type,
            'Source': self.data_exported_type_preprod,
            'ContributorList': trigram,
            'Libelle': 'Export auto Tartare {}'.format(trigram),
            'isadapted': self.is_adapted_value_no_strike
        }
        logging.getLogger(__name__).info('fusio export contributor called with {}'.format(data))
        resp = self.fusio.call(requests.post, api='api', data=data)
        action_id = self.fusio.get_action_id(resp.content)
        self.fusio.wait_for_action_terminated(action_id)

        export_url = self.fusio.get_export_url(action_id)

        # fusio hostname is replaced by the one configured in the preprocess
        # avoid to access to a private ip from outside
        export_url = Fusio.replace_url_hostname_from_url(export_url, self.fusio.url)

        logging.getLogger(__name__).info('fusio export contributor has generated url {}'.format(export_url))

        publication_platform_dict = self.params.get('publication_platform')
        publication_platform_object = Platform(publication_platform_dict.get('protocol'), '',
                                               publication_platform_dict.get('url'),
                                               publication_platform_dict.get('options'))
        protocol_uploader = ProtocolManager.select_from_platform(publication_platform_object)
        self.publish(protocol_uploader, export_url)
        return self.context
