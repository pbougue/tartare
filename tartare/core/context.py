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

from datetime import date
from typing import Dict
from typing import List, Optional

from tartare.core.gridfs_handler import GridFsHandler
from tartare.core.models import ValidityPeriod, Contributor, Coverage, DataSource, \
    ValidityPeriodContainer, Job, DataSet
from tartare.exceptions import IntegrityException, ParameterException, EntityNotFound


class DataSourceContext:
    def __init__(self, data_source_id: str, gridfs_id: Optional[str],
                 validity_period: Optional[ValidityPeriod] = None) -> None:
        self.data_source_id = data_source_id
        self.gridfs_id = gridfs_id
        self.validity_period = validity_period

    def __repr__(self) -> str:
        return str(vars(self))


class ContributorContext(ValidityPeriodContainer):
    def __init__(self, contributor: Contributor, data_source_contexts: Optional[List[DataSourceContext]] = None,
                 validity_period: ValidityPeriod = None) -> None:
        super().__init__(validity_period)
        self.contributor = contributor
        self.data_source_contexts = data_source_contexts if data_source_contexts else []

    def __repr__(self) -> str:
        return str(vars(self))


class Context:
    def __init__(self, job: Job) -> None:
        self.job = job

    def __repr__(self) -> str:
        return str(vars(self))


class DataSourceExport:
    def __init__(self, gridfs_id: str, data_source_id: str, data_format: str, service_id: str=None) -> None:
        self.gridfs_id = gridfs_id
        self.data_source_id = data_source_id
        self.data_format = data_format
        self.service_id = service_id

    def update_data_set_state(self, gridfs_id: str, export_type: Optional[str] = None) -> None:
        self.gridfs_id = gridfs_id
        if export_type:
            self.data_format = export_type


class ContributorExportContext(Context):
    def __init__(self, job: Job) -> None:
        super().__init__(job)
        self.data_source_exports = {}  # type: Dict[str, List[DataSourceExport]]
        self.contributor_contexts = []  # type: Optional[List[ContributorContext]]

    def append_data_source_export(self, data_source: DataSource, data_set: DataSet) -> None:
        if data_source.export_data_source_id not in self.data_source_exports:
            self.data_source_exports[data_source.export_data_source_id] = []
        self.data_source_exports[data_source.export_data_source_id].append(DataSourceExport(
            data_set.gridfs_id,
            data_source.id,
            data_source.data_format,
            data_source.service_id,
        ))

    def get_data_source_export_from_data_source(self, data_source_id: str) -> DataSourceExport:
        for _, data_source_export_list in self.data_source_exports.items():
            data_source_export_found = next((data_source_export for data_source_export in data_source_export_list if
                                             data_source_export.data_source_id == data_source_id), None)
            if data_source_export_found:
                return data_source_export_found
        raise IntegrityException('cannot find data source export for data source {} in context'.format(data_source_id))

    def get_data_source_context_in_links(self, links: List[dict],
                                         data_format: Optional[str] = None) -> Optional[DataSourceContext]:
        for link in links:
            contributor_id = link.get('contributor_id')
            data_source_id = link.get('data_source_id')
            data_source_context = self.get_contributor_data_source_context(contributor_id, data_source_id,
                                                                           [data_format])
            if data_source_context:
                return data_source_context
        return None

    def get_contributor_data_source_contexts(self, contributor_id: str,
                                             data_format_list: Optional[List[str]] = None) -> List[DataSourceContext]:
        contributor_data_source_context_list = []  # type: List[DataSourceContext]
        for contributor_context in self.contributor_contexts:
            if contributor_context.contributor.id == contributor_id:
                if not data_format_list:
                    return contributor_context.data_source_contexts
                for data_source_context in contributor_context.data_source_contexts:
                    data_source = DataSource.get_one(contributor_id, data_source_context.data_source_id)
                    if data_source.data_format in data_format_list:
                        contributor_data_source_context_list.append(data_source_context)
        return contributor_data_source_context_list

    def get_contributor_data_source_context(self, contributor_id: str, data_source_id: str,
                                            data_format_list: Optional[List[str]] = None) -> Optional[
        DataSourceContext]:
        data_source_contexts = self.get_contributor_data_source_contexts(contributor_id, data_format_list)
        if not data_source_contexts:
            return None
        return next((data_source_context
                     for data_source_context in data_source_contexts
                     if data_source_context.data_source_id == data_source_id), None)

    def add_contributor_context(self, contributor: Contributor) -> None:
        contributor_context = next((contributor_context
                                    for contributor_context in self.contributor_contexts
                                    if contributor_context.contributor.id == contributor.id), None)
        if not contributor_context:
            self.contributor_contexts.append(ContributorContext(contributor))

    def add_contributor_data_source_context(self, contributor_id: str, data_source_id: str,
                                            validity_period: Optional[ValidityPeriod],
                                            gridfs_id: Optional[str]) -> None:
        contributor_context = next((contributor_context for contributor_context in self.contributor_contexts
                                    if contributor_context.contributor.id == contributor_id), None)
        if contributor_context:
            contributor_context.data_source_contexts.append(
                DataSourceContext(data_source_id=data_source_id,
                                  gridfs_id=gridfs_id, validity_period=validity_period))

    def fill_context(self, contributor: Contributor) -> None:
        self.add_contributor_context(contributor)
        for data_source in contributor.data_sources:
            if not data_source.is_computed():
                data_set = data_source.get_last_data_set()
                if not data_set:
                    raise ParameterException(
                        'data source {data_source_id} has no data set'.format(data_source_id=data_source.id))
                if data_source.export_data_source_id:
                    self.append_data_source_export(data_source, data_set)
                self.add_contributor_data_source_context(contributor.id, data_source.id, data_set.validity_period,
                                                         data_set.gridfs_id)
            else:
                self.add_contributor_data_source_context(contributor.id, data_source.id, None, None)

        # links data added
        for preprocess in contributor.preprocesses:
            for link in preprocess.params.get('links', []):
                contributor_id = link.get('contributor_id')
                data_source_id = link.get('data_source_id')
                if contributor_id and data_source_id and contributor_id != contributor.id:
                    # @TODO: should exit instead of continue and fail in preprocess
                    try:
                        tmp_contributor = Contributor.get(contributor_id)
                    except EntityNotFound:
                        continue
                    data_set = DataSource.get_one(contributor_id, data_source_id).get_last_data_set()
                    if not data_set:
                        continue
                    self.add_contributor_context(tmp_contributor)
                    self.add_contributor_data_source_context(contributor_id, data_source_id, None,
                                                             data_set.gridfs_id)

    def __repr__(self) -> str:
        return str(vars(self))


class CoverageExportContext(Context, ValidityPeriodContainer):
    def __init__(self, job: Job, coverage: Coverage = None, current_date: date = date.today()) -> None:
        super().__init__(job=job)
        ValidityPeriodContainer.__init__(self)
        self.coverage = coverage
        self.global_gridfs_id = ''
        self.current_date = current_date

    def fill_contributor_contexts(self, coverage: Coverage) -> None:
        if not coverage.input_data_source_ids:
            raise IntegrityException(
                'no data sources are attached to coverage {}'.format(
                    coverage.id))

    def __repr__(self) -> str:
        return str(vars(self))
