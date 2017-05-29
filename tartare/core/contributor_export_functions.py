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
from urllib.error import ContentTooShortError
from tartare.core.gridfs_handler import GridFsHandler
from tartare.core.models import save_file_in_gridfs
from tartare.core.models import ContributorExports


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
                tmp_file_name = os.path.join(tmp_dir_name,
                                             "gtfs-{data_source_id}.zip".format(data_source_id=data_source.id))
                try:
                    urllib.request.urlretrieve(url, tmp_file_name)
                    if not zipfile.is_zipfile(tmp_file_name):
                        raise Exception('downloaded file from url {} is not a zip file'.format(url))
                    with open(tmp_file_name, 'rb') as file:
                        grid_fs_id = GridFsHandler().save_file_in_gridfs(file)
                        context.add_data_source_grid(data_source_id=data_source.id, grid_fs_id=grid_fs_id)
                except ContentTooShortError as e:
                    logger.error('downloaded file size was shorter than exepected for url {}'.format(url))
                    raise e

    for d in data_sources:
        type = d.input.get('type')
        kls = map_fetcher.get(type)
        if kls is None:
            logger.info("Unknown type: %s", type)
            continue
        fetcher = kls(d, context)
        context = fetcher.fetch()

    return context

def save_export(contributor, context):
    export_file = '/home/azime/Navitia/tartare/tests/fixtures/ntfs/ntfs.zip'
    with open(export_file, 'rb') as file:
        context.export_gridfs_id = save_file_in_gridfs(file=file, filename='ntfs.zip')
        logger.info('Export generate : {}'.format(context.export_gridfs_id))
        export = ContributorExports(contributor_id=contributor.id, gridfs_id=context.export_gridfs_id)
        export.save()
    return context