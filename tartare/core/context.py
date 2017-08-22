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
from tartare import app
from tartare.core.models import ContributorExport, ValidityPeriod, Contributor, Coverage, DataSource
import logging
from typing import List, Optional
from tartare.core.gridfs_handler import GridFsHandler


class DataSourceContext():
    def __init__(self, data_source_id: str, gridfs_id: str, validity_period: Optional[ValidityPeriod]=None) -> None:
        self.data_source_id = data_source_id
        self.gridfs_id = gridfs_id
        self.validity_period = validity_period


class ContributorContext():
    def __init__(self, contributor: Contributor,
                 data_source_contexts: Optional[List[DataSourceContext]]=None,
                 validity_period: ValidityPeriod=None) -> None:
        self.contributor = contributor
        self.data_source_contexts = data_source_contexts if data_source_contexts else []
        self.validity_period = validity_period


class Context():
    def __init__(self, instance: str='contributor', coverage: Coverage=None,
                 validity_period: ValidityPeriod=None, contributor_contexts: List[ContributorContext]=None) -> None:
        self.instance = instance
        self.coverage = coverage
        self.contributor_contexts = contributor_contexts if contributor_contexts else []
        self.validity_period = validity_period
        self.global_gridfs_id = ''

    def contributor_has_datasources(self, contributor_id: str) -> bool:
        return len(self.get_contributor_data_source_contexts(contributor_id=contributor_id)) > 0

    def add_contributor_context(self, contributor: Contributor) -> None:
        self.contributor_contexts.append(ContributorContext(contributor))

    def get_contributor_data_sources(self, contributor_id: str) -> Optional[List[DataSource]]:
        return next((contributor_context.contributor.data_sources for contributor_context in self.contributor_contexts
                     if contributor_context.contributor.id == contributor_id), None)

    def get_contributor_data_source_contexts(self, contributor_id: str) -> Optional[List[DataSourceContext]]:
        return next((contributor_context.data_source_contexts
                     for contributor_context in self.contributor_contexts
                     if contributor_context.contributor.id == contributor_id), None)

    def get_contributor_data_source_context(self, contributor_id: str, data_source_id: str) -> Optional[DataSourceContext]:
        data_source_contexts = self.get_contributor_data_source_contexts(contributor_id)
        if not data_source_contexts:
            return None
        return next((data_source_context
                     for data_source_context in data_source_contexts
                     if data_source_context.data_source_id == data_source_id), None)

    def add_contributor_data_source_context(self, contributor_id: str, data_source_id: str,
                                            validity_period: Optional[ValidityPeriod], gridfs_id: Optional[str]) -> None:
        contributor_context = next((contributor_context for contributor_context in self.contributor_contexts
                                    if contributor_context.contributor.id == contributor_id), None)
        if contributor_context:
            contributor_context.data_source_contexts.append(DataSourceContext(data_source_id=data_source_id,
                                                                              gridfs_id=gridfs_id,
                                                                              validity_period=validity_period))

    def fill_contributor_contexts(self, coverage: Coverage) -> None:
        for contributor_id in coverage.contributors:
            contributor_export = ContributorExport.get_last(contributor_id)
            if contributor_export:
                data_source_contexts = []
                for data_source in contributor_export.data_sources:
                    data_source_contexts.append(
                        DataSourceContext(data_source_id=data_source.data_source_id,
                                          gridfs_id=GridFsHandler().copy_file(data_source.gridfs_id),
                                          validity_period=data_source.validity_period)
                    )
                if data_source_contexts:
                    self.contributor_contexts.append(
                        ContributorContext(contributor=Contributor.get(contributor_id=contributor_id),
                                           validity_period=contributor_export.validity_period,
                                           data_source_contexts=data_source_contexts))
        self.coverage = coverage

    def cleanup(self) -> None:
        logging.getLogger(__name__).debug('Delete files context')
        for contributor_context in self.contributor_contexts:
            for data_source_context in contributor_context.data_source_contexts:
                GridFsHandler().delete_file_from_gridfs(data_source_context.gridfs_id)
        if self.global_gridfs_id:
            GridFsHandler().delete_file_from_gridfs(self.global_gridfs_id)
