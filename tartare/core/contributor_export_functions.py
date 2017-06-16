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
import urllib.request
import zipfile
from urllib.error import ContentTooShortError, HTTPError, URLError
from tartare.core.gridfs_handler import GridFsHandler
from tartare.core.models import ContributorExport, ContributorExportDataSource
from tartare.helper import get_filename
from tartare.validity_period_finder import ValidityPeriodFinder

logger = logging.getLogger(__name__)


def merge(contributor, context):
    logger.info("contributor_id : %s", contributor.id)
    return context


def postprocess(contributor, context):
    logger.info("contributor_id : %s", contributor.id)
    return context


def fetch_datasets(contributor, context):
    for data_source in contributor.data_sources:
        data_input = data_source.input
        if data_input:
            url = data_input.get('url')
            logger.info("fetching data from url {}".format(url))
            with tempfile.TemporaryDirectory() as tmp_dir_name:
                filename = get_filename(url, data_source.id)
                tmp_file_name = os.path.join(tmp_dir_name, filename)
                try:
                    urllib.request.urlretrieve(url, tmp_file_name)
                except HTTPError as e:
                    logger.error('error during download of file: {}'.format(str(e)))
                    raise
                except ContentTooShortError:
                    logger.error('downloaded file size was shorter than exepected for url {}'.format(url))
                    raise
                except URLError as e:
                    logger.error('error during download of file: {}'.format(str(e)))
                    raise
                if not zipfile.is_zipfile(tmp_file_name):
                    raise Exception('downloaded file from url {} is not a zip file'.format(url))

                start_date, end_date = ValidityPeriodFinder().get_validity_period(file=tmp_file_name)
                logger.info('Production date {} to {}'.format(start_date, end_date))
                with open(tmp_file_name, 'rb') as file:
                    grid_fs_id = GridFsHandler().save_file_in_gridfs(file, filename=filename)
                    context.add_data_source_grid(data_source_id=data_source.id,
                                                 grid_fs_id=grid_fs_id,
                                                 start_date=start_date,
                                                 end_date=end_date)
    return context


def save_export(contributor, context):
    for dict_gridfs_id in context.data_sources_grid:
        grid_fs_id = dict_gridfs_id.get("grid_fs_id")
        data_source_id = dict_gridfs_id.get("data_source_id")
        if not grid_fs_id:
            logger.info("data source {} without gridfs id.".format(data_source_id))
            continue
        new_grid_fs_id = GridFsHandler().copy_file(grid_fs_id)
        validity_period = dict_gridfs_id.get('validity_period')
        data_source = ContributorExportDataSource(data_source_id, validity_period)
        export = ContributorExport(contributor_id=contributor.id,
                                   gridfs_id=new_grid_fs_id,
                                   validity_period=validity_period,
                                   data_sources=[data_source])
        export.save()
        dict_gridfs_id.update({'grid_fs_id': new_grid_fs_id})
    return context
