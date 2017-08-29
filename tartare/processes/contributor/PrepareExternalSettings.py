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

from tartare.core.context import Context
from tartare.core.models import PreProcess
from tartare.processes.abstract_preprocess import AbstractContributorProcess


class PrepareExternalSettings(AbstractContributorProcess):
    contrib_trigram = "OIF"

    def __init__(self, context: Context, preprocess: PreProcess):
        super().__init__(context, preprocess)

    def get_navitia_code_from_gtfs_stop_point(self, gtfs_stop_code):
        return "{}:SP:{}".format(self.contrib_trigram, gtfs_stop_code[10:])

    def do(self) -> Context:
        for data_source_id_to_process in self.data_source_ids:
            data_source_to_process_context = self.context.get_contributor_data_source_context(
                contributor_id=self.contributor_id,
                data_source_id=data_source_id_to_process)
        return self.context
