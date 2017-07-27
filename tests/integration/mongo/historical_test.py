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

import os
from tartare.core import models
from datetime import date
from tartare import app, mongo
from tartare.core.gridfs_handler import GridFsHandler

fixtures_path = os.path.realpath('tests/fixtures/gtfs/some_archive.zip')
start_date, end_date = (date(2017, 1, 1), date(2018, 12, 31))
validity_period = models.ValidityPeriod(start_date=start_date, end_date=end_date)


def test_data_source_fetched_historical():
    list_ids = []
    with app.app_context():
        for i in range(1, 6):
            data_source_fetched = models.DataSourceFetched(contributor_id='contrib_id',
                                                           data_source_id='data_source_id',
                                                           validity_period=validity_period)
            data_source_fetched.save_dataset(fixtures_path, 'gtfs.zip')
            data_source_fetched.save()
            list_ids.append(data_source_fetched.id)

        # test that there are only 3 data sources
        raw = mongo.db[models.DataSourceFetched.mongo_collection].find({
            'contributor_id': 'contrib_id',
            'data_source_id': 'data_source_id'
        })
        assert raw.count() == 3
        # Test the 3 last objects saved are not deleted
        assert (list_ids[2:].sort() == [row.get('_id') for row in raw].sort())

        # test that there are only 3 gridfs
        raw = mongo.db['fs.files'].find({})
        assert raw.count() == 3


def test_data_contrib_export_historical():
    list_ids = []
    with app.app_context():
        for i in range(1, 6):
            with open(fixtures_path, 'rb') as file:
                gridfs_id = GridFsHandler().save_file_in_gridfs(file, filename='gtfs.zip', contributor_id='contrib_id')

            contrib_export = models.ContributorExport(contributor_id='contrib_id',
                                                      gridfs_id=gridfs_id,
                                                      validity_period=validity_period,
                                                      data_sources=[])
            contrib_export.save()
            list_ids.append(contrib_export.id)

        # test that there are only 3 contributor exports
        raw = mongo.db[models.ContributorExport.mongo_collection].find({
            'contributor_id': 'contrib_id',
        })
        assert raw.count() == 3
        # Test the 3 last objects saved are not deleted
        assert (list_ids[2:].sort() == [row.get('_id') for row in raw].sort())

        # test that there are only 3 gridfs
        raw = mongo.db['fs.files'].find({})
        assert raw.count() == 3


def test_data_coverage_export_historical():
    list_ids = []
    with app.app_context():
        for i in range(1, 6):
            with open(fixtures_path, 'rb') as file:
                gridfs_id = GridFsHandler().save_file_in_gridfs(file, filename='gtfs.zip', contributor_id='contrib_id')

            coverage_export = models.CoverageExport(coverage_id='id_test', gridfs_id=gridfs_id,
                                                    validity_period=validity_period,
                                                    contributors=[])
            coverage_export.save()
            list_ids.append(coverage_export.id)

        # test that there are only 3 coverage exports
        raw = mongo.db[models.CoverageExport.mongo_collection].find({
            'coverage_id': 'id_test',
        })
        assert raw.count() == 3
        # Test the 3 last objects saved are not deleted
        assert (list_ids[2:].sort() == [row.get('_id') for row in raw].sort())

        # test that there are only 3 gridfs
        raw = mongo.db['fs.files'].find({})
        assert raw.count() == 3
