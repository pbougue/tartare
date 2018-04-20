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
import zipfile
from typing import Optional

from tartare.core import models
from tartare.core.constants import DATA_FORMAT_GENERATE_EXPORT, INPUT_TYPE_URL, \
    DATA_SOURCE_STATUS_FAILED, DATA_SOURCE_STATUS_UNCHANGED, DATA_FORMAT_GTFS, ACTION_TYPE_DATA_SOURCE_FETCH
from tartare.core.context import ContributorExportContext
from tartare.core.fetcher import FetcherManager
from tartare.core.models import ContributorExport, ContributorExportDataSource, Contributor, ValidityPeriod, Job
from tartare.core.validity_period_finder import ValidityPeriodFinder
from tartare.exceptions import ParameterException, FetcherException, GuessFileNameFromUrlException, InvalidFile

logger = logging.getLogger(__name__)


def merge(contributor: Contributor, context: ContributorExportContext) -> ContributorExportContext:
    logger.info("Merge for contributor_id : %s", contributor.id)
    return context


def postprocess(contributor: Contributor, context: ContributorExportContext) -> ContributorExportContext:
    logger.info("Post process for contributor_id : %s", contributor.id)
    return context


def save_export(contributor: Contributor, context: ContributorExportContext) -> Optional[ContributorExport]:
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
        contributor_export_validity_period = ValidityPeriod.union(validity_periods) if len(validity_periods) else None

        export = ContributorExport(contributor_id=contributor.id,
                                   validity_period=contributor_export_validity_period,
                                   data_sources=contrib_export_data_sources)
        export.save()
        return export
    return None


def fetch_datasets_and_return_updated_number(contributor: Contributor, parent_job_id: str) -> int:
    nb_updated_datasets = 0
    for data_source in contributor.data_sources:
        if data_source.input.url and data_source.has_type(INPUT_TYPE_URL):
            nb_updated_datasets += 1 if fetch_and_save_dataset(contributor.id, data_source, parent_job_id) else 0

    return nb_updated_datasets


def fetch_and_save_dataset(contributor_id: str, data_source: models.DataSource,
                           parent_job_id: Optional[str] = None) -> bool:
    url = data_source.input.url
    logger.info("fetching data from url {}".format(url))
    with tempfile.TemporaryDirectory() as tmp_dir_name:
        data_source_fetch_job = Job(ACTION_TYPE_DATA_SOURCE_FETCH, contributor_id, parent_id=parent_job_id,
                                    state='running', step='prepare', data_source_id=data_source.id)
        data_source_fetch_job.save()
        last_data_source_fetched = models.DataSourceFetched.get_last(data_source_id=data_source.id)
        new_data_source_fetched = models.DataSourceFetched(data_source_id=data_source.id, contributor_id=contributor_id)
        new_data_source_fetched.save()
        try:
            data_source_fetch_job.update(step='fetch')
            fetcher = FetcherManager.select_from_url(url)
            dest_full_file_name, expected_file_name = fetcher.fetch(url, tmp_dir_name,
                                                                    data_source.input.expected_file_name)
            if data_source.data_format == DATA_FORMAT_GTFS and not zipfile.is_zipfile(dest_full_file_name):
                raise InvalidFile('downloaded file from url {} is not a zip file'.format(url))
        except (FetcherException, GuessFileNameFromUrlException, ParameterException, InvalidFile) as e:
            data_source_fetch_job.update(state='failed', error_message=str(e))
            new_data_source_fetched.set_status(DATA_SOURCE_STATUS_FAILED).update()
            raise e

        if data_source.data_format in DATA_FORMAT_GENERATE_EXPORT:
            if last_data_source_fetched and last_data_source_fetched.is_identical_to(dest_full_file_name):
                logger.debug('fetched file {} for contributor {} has not changed since last fetch, skipping'
                             .format(expected_file_name, contributor_id))
                new_data_source_fetched.set_status(DATA_SOURCE_STATUS_UNCHANGED).update()
                return False
        logger.debug('Add DataSourceFetched object for contributor: {}, data_source: {}'.format(
            contributor_id, data_source.id
        ))
        data_source_fetch_job.update(step='compute_validity')
        validity_period = ValidityPeriodFinder.select_computer_and_find(dest_full_file_name, data_source.data_format)
        new_data_source_fetched.validity_period = validity_period
        data_source_fetch_job.update(step='save')
        new_data_source_fetched.update_dataset(dest_full_file_name, expected_file_name)
        data_source_fetch_job.update(state='done')
        return data_source.data_format in DATA_FORMAT_GENERATE_EXPORT
