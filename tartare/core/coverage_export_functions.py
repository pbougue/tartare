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
from tartare.core.context import Context
from tartare.core.models import CoverageExport, CoverageExportContributor, Coverage, ContributorExportDataSource
from tartare.core.gridfs_handler import GridFsHandler

logger = logging.getLogger(__name__)


def merge(coverage: Coverage, context: Context) -> Context:
    logger.info("coverage_id : %s", coverage.id)
    return context


def postprocess(coverage: Coverage, context: Context) -> Context:
    logger.info("coverage_id : %s", coverage.id)
    for contributor_context in context.contributors_context:
        if not context.validity_period:
            context.validity_period = contributor_context.validity_period
        if not context.global_gridfs_id:
            context.global_gridfs_id = contributor_context.data_sources_context[0].gridfs_id
        break
    return context


def save_export(coverage: Coverage, context: Context) -> Context:
    contributor_exports = []
    for contributor_context in context.contributors_context:
        data_sources = []
        for data_source_context in contributor_context.data_sources_context:
            data_sources.append(
                ContributorExportDataSource(data_source_id=data_source_context.data_source_id,
                                            gridfs_id=GridFsHandler().copy_file(data_source_context.gridfs_id),
                                            validity_period=data_source_context.validity_period)
            )

        if data_sources:
            contributor_exports.append(
                CoverageExportContributor(contributor_id=contributor_context.contributor.id,
                                          validity_period=contributor_context.validity_period,
                                          data_sources=data_sources))

    if contributor_exports:
        export = CoverageExport(coverage_id=coverage.id,
                                gridfs_id=GridFsHandler().copy_file(context.global_gridfs_id),
                                validity_period=context.validity_period,
                                contributors=contributor_exports)
        export.save()

    return context
