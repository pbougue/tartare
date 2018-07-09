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

from typing import List

from tartare.core.constants import DATA_FORMAT_GENERATE_EXPORT, \
    DATA_FORMAT_GTFS
from tartare.core.context import ContributorExportContext
from tartare.core.fetcher import FetcherManager
from tartare.core.gridfs_handler import GridFsHandler
from tartare.core.models import Contributor, DataSet
from tartare.core.validity_period_finder import ValidityPeriodFinder
from tartare.exceptions import ParameterException, FetcherException, GuessFileNameFromUrlException, InvalidFile, \
    RuntimeException

logger = logging.getLogger(__name__)


def merge(contributor: Contributor, context: ContributorExportContext) -> ContributorExportContext:
    logger.info("Merge for contributor_id : %s", contributor.id)
    return context


def postprocess(contributor: Contributor, context: ContributorExportContext) -> ContributorExportContext:
    logger.info("Post process for contributor_id : %s", contributor.id)
    return context


def save_export(contributor: Contributor, context: ContributorExportContext) -> List[str]:
    exports_ids = []
    for export_id, data_source_export_list in context.data_source_exports.items():
        gridfs_ids = [export.gridfs_id for export in data_source_export_list]
        data_formats = [export.data_format for export in data_source_export_list]
        service_ids = [export.service_id for export in data_source_export_list]
        if len(gridfs_ids) > 1 or len(data_formats) > 1 or len(service_ids) > 1:
            raise RuntimeException(
                ('export {} cannot be determined from its input data_sources' +
                 'found {} gridfs_id ({}), {} data_format ({}) and {} service_id ({})').format(
                    export_id, len(gridfs_ids), ','.join(gridfs_ids), len(data_formats), ','.join(data_formats),
                    len(service_ids), ','.join(service_ids)
                )

            )
        data_set = DataSet(gridfs_id=gridfs_ids[0])
        data_source = contributor.get_data_source(export_id)
        data_source.data_format = data_formats[0]
        data_source.service_id = service_ids[0]
        data_set.validity_period = ValidityPeriodFinder.select_computer_and_find(
            GridFsHandler().get_file_from_gridfs(gridfs_ids[0]), data_source.data_format)
        data_source.add_data_set_and_update_model(data_set, contributor)
        exports_ids.append(data_source.id)
    return exports_ids


def fetch_datasets_and_return_updated_number(contributor: Contributor, data_source_to_fetch_id: str = None) -> int:
    nb_updated_datasets = 0
    for data_source in contributor.data_sources:
        if (not data_source_to_fetch_id or data_source_to_fetch_id == data_source.id) and \
                data_source.is_auto() and data_source.input.url:
            nb_updated_datasets += 1 if fetch_and_save_dataset(contributor, data_source.id) else 0
    return nb_updated_datasets


def fetch_and_save_dataset(contributor: Contributor, data_source_id: str) -> bool:
    data_source = contributor.get_data_source(data_source_id)
    url = data_source.input.url
    logger.info("fetching data from url {}".format(url))
    data_source.starts_fetch(contributor)
    with tempfile.TemporaryDirectory() as tmp_dir_name:
        last_data_set = data_source.get_last_data_set_if_exists()
        try:
            fetcher = FetcherManager.select_from_url(url)
            dest_full_file_name, expected_file_name = fetcher.fetch(url, tmp_dir_name, options=data_source.input.options,
                                                                    expected_filename=data_source.input.expected_file_name)
            if data_source.data_format == DATA_FORMAT_GTFS and not zipfile.is_zipfile(dest_full_file_name):
                raise InvalidFile('downloaded file from url {} is not a zip file'.format(url))
        except (FetcherException, GuessFileNameFromUrlException, ParameterException, InvalidFile) as e:
            data_source.fetch_fails(contributor)
            raise e

        if data_source.data_format in DATA_FORMAT_GENERATE_EXPORT:
            if last_data_set and last_data_set.is_identical_to(dest_full_file_name):
                logger.debug('fetched file {} for contributor {} has not changed since last fetch, skipping'
                             .format(expected_file_name, contributor.id))
                data_source.fetch_unchanged(contributor)
                return False
        logger.debug('Add DataSet object for contributor: {}, data_source: {}'.format(
            contributor.id, data_source.id
        ))
        validity_period = ValidityPeriodFinder.select_computer_and_find(dest_full_file_name, data_source.data_format)
        data_set = DataSet(validity_period=validity_period)
        data_set.add_file_from_path(dest_full_file_name, expected_file_name)
        data_source.add_data_set_and_update_model(data_set, contributor)
        return data_source.data_format in DATA_FORMAT_GENERATE_EXPORT
