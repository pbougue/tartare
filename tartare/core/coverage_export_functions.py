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
from tartare.core.models import ContributorExport, CoverageExport

logger = logging.getLogger(__name__)


def merge(coverage, context):
    logger.info("coverage_id : %s", coverage.id)
    return context


def postprocess(coverage, context):
    logger.info("coverage_id : %s", coverage.id)
    return context


def initialize_context(coverage, context):
    logger.info('fetch contributors')
    for contributor_id in coverage.contributors:
        export = ContributorExport.get_last(contributor_id)
        if not export:
            logger.info("Contributor {} without export.".format(contributor_id), coverage.id)
            continue
        context.contributor_exports.append(export[0])

    return context


def save_export(coverage, context):
    for ce in context.contributor_exports:
        if not ce.get("gridfs_id"):
            logger.info("contributor export {} without gridfs id.".format(ce.get("contributor_id")))
            continue
        export = CoverageExport(coverage_id=coverage.id, gridfs_id=ce.get("gridfs_id"),
                                contributors=[ce.get("contributor_id")])
        export.save()
    return context
