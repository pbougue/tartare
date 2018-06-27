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
from typing import Optional

from tartare.core.constants import DATA_FORMAT_GTFS
from tartare.core.context import CoverageExportContext
from tartare.core.gridfs_handler import GridFsHandler
from tartare.core.models import CoverageExport, Coverage, DataSource
from tartare.core.validity_period_finder import ValidityPeriodFinder
from tartare.exceptions import IntegrityException

logger = logging.getLogger(__name__)


def merge(coverage: Coverage, context: CoverageExportContext) -> CoverageExportContext:
    logger.info("merge for coverage_id = %s", coverage.id)
    # following condition is matched when Fusio export preprocess is not attached to coverage
    # it simulates its behavior for now for tests purposes
    # merge necessary for multi-contributors is not handled here and should be done by Fusio
    if not context.global_gridfs_id:
        for data_source_id in coverage.input_data_source_ids:
            data_source = DataSource.get_one(data_source_id=data_source_id)
            if data_source.is_of_one_of_data_format(ValidityPeriodFinder.get_data_format_with_validity()):
                data_set = data_source.get_last_data_set()
                context.global_gridfs_id = GridFsHandler().copy_file(data_set.gridfs_id)
                context.validity_period = data_set.validity_period
                return context
        raise IntegrityException(
            ('coverage {} does not contains any Fusio export preprocess ' +
             'and fallback computation cannot find any {} data source').format(coverage.id, DATA_FORMAT_GTFS))
    return context


def postprocess(coverage: Coverage, context: CoverageExportContext) -> CoverageExportContext:
    logger.info("postprocess for coverage_id = %s", coverage.id)
    # @TODO launch post process with tartare.tasks.launch function
    return context


def save_export(coverage: Coverage, context: CoverageExportContext) -> None:
    export = CoverageExport(coverage_id=coverage.id,
                            gridfs_id=context.global_gridfs_id,
                            validity_period=context.validity_period
                            )
    export.save()
