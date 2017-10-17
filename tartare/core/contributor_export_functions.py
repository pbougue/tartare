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
import tempfile

from tartare.core import models
from tartare.core.constants import DATA_FORMAT_GENERATE_EXPORT, INPUT_TYPE_URL, DATA_FORMAT_WITH_VALIDITY
from tartare.core.context import Context
from tartare.core.fetcher import FetcherManager
from tartare.core.gridfs_handler import GridFsHandler
from tartare.core.models import ContributorExport, ContributorExportDataSource, Contributor, DataSourceFetched
from tartare.exceptions import ParameterException
from tartare.helper import get_md5_content_file
from tartare.validity_period_finder import ValidityPeriodFinder
from datetime import date

logger = logging.getLogger(__name__)


def merge(contributor: Contributor, context: Context) -> Context:
    logger.info("Merge for contributor_id : %s", contributor.id)
    return context


def postprocess(contributor: Contributor, context: Context) -> Context:
    logger.info("Post process for contributor_id : %s", contributor.id)
    return context


def save_export(contributor: Contributor, context: Context, current_date: date) -> Context:
    contrib_export_data_sources = []
    validity_periods = []
    for data_source_context in context.get_contributor_data_source_contexts(contributor.id):
        if not data_source_context.gridfs_id:
            logger.info("data source {} without gridfs id.".format(data_source_context.data_source_id))
            continue
        contrib_export_data_sources.append(
            ContributorExportDataSource(data_source_id=data_source_context.data_source_id,
                                        gridfs_id=data_source_context.gridfs_id,
                                        validity_period=data_source_context.validity_period)
        )
        if data_source_context.validity_period:
            validity_periods.append(data_source_context.validity_period)

    if contrib_export_data_sources:
        # grid fs id is taken from the first data source having a validity period
        # contributor with multiple data sources is not handled yet
        grid_fs_id = next((data_source.gridfs_id
                           for data_source in contrib_export_data_sources
                           if data_source.validity_period), None)
        contributor_export_validity_period = ValidityPeriodFinder.get_validity_period_union(validity_periods,
                                                                                            current_date)
        export = ContributorExport(contributor_id=contributor.id,
                                   gridfs_id=GridFsHandler().copy_file(grid_fs_id),
                                   validity_period=contributor_export_validity_period,
                                   data_sources=contrib_export_data_sources)
        export.save()
    return context


def save_data_fetched_and_get_context(context: Context, file: str, filename: str,
                                      contributor_id: str, data_source_id: str,
                                      validity_period: models.ValidityPeriod) -> Context:
    data_source_fetched = models.DataSourceFetched(contributor_id=contributor_id,
                                                   data_source_id=data_source_id,
                                                   validity_period=validity_period)
    data_source_fetched.save_dataset(file, filename)
    data_source_fetched.save()
    context.add_contributor_data_source_context(contributor_id=contributor_id,
                                                data_source_id=data_source_id,
                                                validity_period=validity_period,
                                                gridfs_id=GridFsHandler().copy_file(data_source_fetched.gridfs_id))
    return context


def fetch_datasets_and_return_updated_number(contributor: Contributor) -> int:
    nb_updated_datasets = 0
    for data_source in contributor.data_sources:
        if data_source.input.type == INPUT_TYPE_URL and data_source.input.url:
            url = data_source.input.url
            logger.info("fetching data from url {}".format(url))
            fetcher = FetcherManager.select_from_url(url)
            with tempfile.TemporaryDirectory() as tmp_dir_name:
                dest_full_file_name, expected_file_name = fetcher.fetch(url, tmp_dir_name, data_source.data_format,
                                                                        data_source.input.expected_file_name)
                data_source_fetched = models.DataSourceFetched.get_last(contributor_id=contributor.id,
                                                                        data_source_id=data_source.id)
                if data_source.data_format in DATA_FORMAT_GENERATE_EXPORT:
                    if data_source_fetched and data_source_fetched.get_md5() == get_md5_content_file(
                            dest_full_file_name):
                        logger.debug('fetched file {} for contributor {} has not changed since last fetch, skipping'
                                     .format(expected_file_name, contributor.id))
                        continue
                    else:
                        nb_updated_datasets += 1
                logger.debug('Add DataSourceFetched object for contributor: {}, data_source: {}'.format(
                    contributor.id, data_source.id
                ))
                if data_source.data_format in DATA_FORMAT_WITH_VALIDITY:
                    start_date, end_date = ValidityPeriodFinder().get_validity_period(file=dest_full_file_name)
                    validity_period = models.ValidityPeriod(start_date=start_date, end_date=end_date)
                else:
                    validity_period = None

                data_source_fetched = models.DataSourceFetched(contributor_id=contributor.id,
                                                               data_source_id=data_source.id,
                                                               validity_period=validity_period)
                data_source_fetched.save_dataset(dest_full_file_name, expected_file_name)
                data_source_fetched.save()
    return nb_updated_datasets


def build_context(contributor: Contributor, context: Context) -> Context:
    context.add_contributor_context(contributor)
    for data_source in contributor.data_sources:
        if data_source.input.type != 'computed':
            data_set = DataSourceFetched.get_last(contributor.id, data_source.id)
            if not data_set:
                raise ParameterException(
                    'data source {data_source_id} has no data set'.format(data_source_id=data_source.id))
            context.add_contributor_data_source_context(contributor.id, data_source.id, data_set.validity_period,
                                                        GridFsHandler().copy_file(data_set.gridfs_id))
        else:
            context.add_contributor_data_source_context(contributor.id, data_source.id, None, None)
    return context
