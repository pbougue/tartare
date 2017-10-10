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

from tartare.core.context import Context
from tartare.core.models import ValidityPeriod
from tartare.exceptions import IntegrityException, ValidityPeriodException
from tartare.processes.abstract_preprocess import AbstractFusioProcess
from tartare.processes.fusio import Fusio
from tartare.validity_period_finder import ValidityPeriodFinder
from tartare.processes.utils import preprocess_registry


@preprocess_registry('coverage')
class FusioImport(AbstractFusioProcess):
    def get_validity_period(self) -> ValidityPeriod:
        validity_periods = [ceds.validity_period for ceds in self.context.contributor_contexts if
                                              ceds.validity_period]
        try:
            validity_period_union = ValidityPeriodFinder.get_validity_period_union(validity_periods)
        except ValidityPeriodException as exception:
            raise IntegrityException('bounds date for fusio import incorrect: {detail}'.format(detail=str(exception)))
        return validity_period_union

    def do(self) -> Context:
        validity_period = self.get_validity_period()
        resp = self.fusio.call(requests.post, api='api',
                          data={
                              'DateDebut': Fusio.format_date(validity_period.start_date),
                              'DateFin': Fusio.format_date(validity_period.end_date),
                              'action': 'regionalimport',
                          })
        self.fusio.wait_for_action_terminated(self.fusio.get_action_id(resp.content))
        return self.context
