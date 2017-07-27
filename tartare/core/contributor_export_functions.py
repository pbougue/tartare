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
import os
import tempfile
from tartare.core.context import Context
from tartare.core.gridfs_handler import GridFsHandler
from tartare.core.models import ContributorExport, ContributorExportDataSource, Contributor
from tartare.validity_period_finder import ValidityPeriodFinder
from tartare.helper import get_filename, get_md5_content_file, download_zip_file
from tartare.core import models


logger = logging.getLogger(__name__)


def merge(contributor: Contributor, context: Context) -> Context:
    logger.info("contributor_id : %s", contributor.id)
    return context


def postprocess(contributor: Contributor, context: Context) -> Context:
    logger.info("contributor_id : %s", contributor.id)
    return context


def save_export(contributor: Contributor, context: Context) -> Context:
    data_sources = []
    new_grid_fs_id = None
    for data_source_grid in context.data_sources_fetched:
        if not data_source_grid.gridfs_id:
            logger.info("data source {} without gridfs id.".format(data_source_grid.data_source_id))
            continue
        new_grid_fs_id = GridFsHandler().copy_file(data_source_grid.gridfs_id)
        data_sources.append(
            ContributorExportDataSource(data_source_grid.data_source_id, data_source_grid.validity_period)
        )
    if data_sources:
        export = ContributorExport(contributor_id=contributor.id,
                                   gridfs_id=new_grid_fs_id,
                                   validity_period=data_source_grid.validity_period,
                                   data_sources=data_sources)
        export.save()
        context.contributor_exports.append(export)
    return context


def fetch_datasets(contributor: Contributor, context: Context) -> Context:
    for data_source in contributor.data_sources:
        if data_source.input:
            url = data_source.input.get('url')
            logger.info("fetching data from url {}".format(url))
            with tempfile.TemporaryDirectory() as tmp_dir_name:
                filename = get_filename(url, data_source.id)
                tmp_file_name = os.path.join(tmp_dir_name, filename)
                download_zip_file(url, tmp_file_name)

                data_source_fetched = models.DataSourceFetched.get_last(contributor_id=contributor.id,
                                                                        data_source_id=data_source.id)
                if data_source_fetched and data_source_fetched.get_md5() == get_md5_content_file(tmp_file_name):
                        logger.debug('already existing file {} for contributor {}'.format(filename, contributor.id))
                        continue
                logger.debug('Add DataSourceFetched object for contributor: {}, data_source: {}'.format(
                    contributor.id, data_source.id
                ))
                start_date, end_date = ValidityPeriodFinder().get_validity_period(file=tmp_file_name)
                validity_period = models.ValidityPeriod(start_date=start_date, end_date=end_date)
                data_source_fetched = models.DataSourceFetched(contributor_id=contributor.id,
                                                               data_source_id=data_source.id,
                                                               validity_period=validity_period)
                data_source_fetched.save_dataset(tmp_file_name, filename)
                data_source_fetched.save()
                context.data_sources_fetched.append(data_source_fetched)
    return context
