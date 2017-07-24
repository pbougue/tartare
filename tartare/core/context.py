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
from tartare.core.models import ContributorExport, DataSourceFetched, DataSource
import logging
from typing import List


class Context:
    def __init__(self, instance: str='contributor', data_sources_fetched: List[DataSourceFetched]=None,
                 contributor_exports: List[ContributorExport]=None) -> None:
        self.instance = instance
        self.gridfs_id = None
        self.data_sources_fetched = data_sources_fetched if data_sources_fetched else []
        self.contributor_exports = contributor_exports if contributor_exports else []

    def fill_contributor_exports(self, contributors: List[str]) -> None:
        logging.getLogger(__name__).info('initialize context')
        for contributor_id in contributors:
            export = ContributorExport.get_last(contributor_id)
            if not export:
                logging.getLogger(__name__).info("Contributor {} without export.".format(contributor_id))
                continue
            self.contributor_exports.append(export)

    def fill_data_sources_fetched(self, contributor_id: str, data_sources: List[DataSource]) -> None:
        logging.getLogger(__name__).info('initialize context')
        for data_source in data_sources:
            export = DataSourceFetched.get_last(contributor_id, data_source.id)
            if not export:
                logging.getLogger(__name__).info("Data source {} for contributor {} without data source fetched.".
                                                 format(data_source.id, contributor_id))
                continue
            self.data_sources_fetched.append(export)
