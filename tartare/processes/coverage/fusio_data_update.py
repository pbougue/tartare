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

import requests

from tartare.core.context import Context
from tartare.core.models import Contributor, DataSource, DataSet
from tartare.core.validity_period_finder import ValidityPeriodFinder
from tartare.exceptions import ParameterException, ValidityPeriodException
from tartare.processes.abstract_preprocess import AbstractFusioProcess
from tartare.processes.fusio import Fusio
from tartare.processes.utils import preprocess_registry


@preprocess_registry('coverage')
class FusioDataUpdate(AbstractFusioProcess):
    def __get_data(self, contributor: Contributor, data_source: DataSource, data_set: DataSet) -> dict:
        validity_period = data_set.validity_period.to_valid(self.context.current_date)

        if data_source.service_id is None:
            raise ParameterException('service_id of data source {} of contributor {} should not be null'.format(
                data_source.id, contributor.id))

        return {
            'action': 'dataupdate',
            'contributorexternalcode': contributor.data_prefix,
            'isadapted': 0,
            'dutype': 'update',
            'serviceid': data_source.service_id,
            'libelle': 'unlibelle',
            'DateDebut': Fusio.format_date(validity_period.start_date),
            'DateFin': Fusio.format_date(validity_period.end_date),
            'content-type': 'multipart/form-data',
        }

    def do(self) -> Context:
        self.context.coverage.input_data_source_ids.sort()
        for data_source_id in self.context.coverage.input_data_source_ids:
            contributor = DataSource.get_contributor_of_data_source(data_source_id)
            data_source = contributor.get_data_source(data_source_id)
            if not data_source.is_of_one_of_data_format(ValidityPeriodFinder.get_data_format_with_validity()):
                continue
            try:
                data_set = data_source.get_last_data_set()
                resp = self.fusio.call(requests.post, api='api',
                                       data=self.__get_data(contributor, data_source, data_set),
                                       files=self.get_files_from_gridfs(data_set.gridfs_id))
                self.fusio.wait_for_action_terminated(self.fusio.get_action_id(resp.content))
            except ValidityPeriodException as exception:
                # validity period in past may happen so we just skip data update instead of crash
                logging.getLogger(__name__).warning('skipping data update for data source {}, error: {}'.format(
                    data_source_id, str(exception)
                ))
        return self.context
