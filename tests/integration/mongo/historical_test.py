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
from tartare.core.context import Context
from tartare.core import contributor_export_functions, coverage_export_functions
import pytest

fixtures_path = os.path.realpath('tests/fixtures/gtfs/some_archive.zip')
start_date, end_date = (date(2017, 1, 1), date(2018, 12, 31))
validity_period = models.ValidityPeriod(start_date=start_date, end_date=end_date)


class TestHistorical():
    @classmethod
    @pytest.yield_fixture(scope='function', autouse=True)
    def my_method_setup(cls):
        with app.app_context():
            contributor = models.Contributor(id='contrib_id', name='AAA', data_prefix='AAA')
            contributor.save()

            data_source = models.DataSource(id='data_source_gtfs', name='EEEEE', data_format='gtfs')
            data_source.save(contributor_id=contributor.id)

            data_source = models.DataSource(id='data_source_direction_config',
                                            name='direction_config', data_format='direction_config')

            data_source.save(contributor_id=contributor.id)
            coverage = models.Coverage('c1', 'c1', contributors=[contributor.id])
            coverage.save()
            yield

    def test_data_source_fetched_gtfs_historical(self):
        list_ids = []

        for i in range(1, 6):
            data_source_fetched = models.DataSourceFetched(contributor_id='contrib_id',
                                                           data_source_id='data_source_gtfs',
                                                           validity_period=validity_period)
            data_source_fetched.save_dataset(fixtures_path, 'gtfs.zip')
            data_source_fetched.save()
            list_ids.append(data_source_fetched.id)

        # test that there are only 3 data sources
        raw = mongo.db[models.DataSourceFetched.mongo_collection].find({
            'contributor_id': 'contrib_id',
            'data_source_id': 'data_source_gtfs'
        })
        assert raw.count() == app.config.get('KEEP_HISTORICAL').get('gtfs')
        # Test the 3 last objects saved are not deleted
        assert (list_ids[2:].sort() == [row.get('_id') for row in raw].sort())

        # test that there are only 3 gridfs
        raw = mongo.db['fs.files'].find({})
        assert raw.count() == 3

    def test_data_source_fetched_gtfs_config_file_historical(self):
        data_source_gtfs_list_ids = []
        direction_config_list_ids = []

        # GTFS
        for i in range(1, 6):
            data_source_fetched = models.DataSourceFetched(contributor_id='contrib_id',
                                                           data_source_id='data_source_gtfs',
                                                           validity_period=validity_period)
            data_source_fetched.save_dataset(fixtures_path, 'gtfs.zip')
            data_source_fetched.save()
            data_source_gtfs_list_ids.append(data_source_fetched.id)
        #Config File
        for i in range(1, 6):
            data_source_fetched = models.DataSourceFetched(contributor_id='contrib_id',
                                                           data_source_id='data_source_direction_config')
            data_source_fetched.save_dataset(fixtures_path, 'gtfs.zip')
            data_source_fetched.save()
            direction_config_list_ids.append(data_source_fetched.id)
        # test that there are only 3 data sources
        raw = mongo.db[models.DataSourceFetched.mongo_collection].find({
            'contributor_id': 'contrib_id',
            'data_source_id': 'data_source_gtfs'
        })
        assert raw.count() == 3
        # Test the 3 last objects saved are not deleted
        assert (data_source_gtfs_list_ids[2:].sort() == [row.get('_id') for row in raw].sort())

        raw = mongo.db[models.DataSourceFetched.mongo_collection].find({
            'contributor_id': 'contrib_id',
            'data_source_id': 'data_source_direction_config'
        })
        assert raw.count() == 2
        # Test the 3 last objects saved are not deleted
        assert (direction_config_list_ids[2:].sort() == [row.get('_id') for row in raw].sort())

        # test that there are only 5 gridfs
        # 3 gtfs data format
        # 2 direction config
        raw = mongo.db['fs.files'].find({})
        assert raw.count() == 5

    def test_data_contrib_export_historical(self):
        list_ids = []
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

    def test_data_coverage_export_historical(self):
        list_ids = []
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

    def populate_data_fetched(self, context, contributor):
        context.add_contributor_context(contributor)
        contributor_export_functions.save_data_fetched_and_get_context(context=context,
                                                                       file=fixtures_path,
                                                                       filename='gtfs.zip',
                                                                       contributor_id='contrib_id',
                                                                       data_source_id='data_source_gtfs',
                                                                       validity_period=validity_period)
        return context

    def populate_data_fetched_and_save_export(self, contributor):
        context = Context()
        context = self.populate_data_fetched(context, contributor)
        contributor_export_functions.save_export(contributor, context)

    def test_data_source_fetched_historical_use_context(self):
        list_ids = []
        contributor = models.Contributor.get('contrib_id')
        data_sources = models.DataSource.get(data_source_id='data_source_gtfs')
        for i in range(1, 6):
            self.populate_data_fetched(Context(), contributor)
        # test that there are only 3 data sources
        raw = mongo.db[models.DataSourceFetched.mongo_collection].find({
            'contributor_id': contributor.id,
            'data_source_id': data_sources[0].id
        })

        assert raw.count() == 3
        # Test the 3 last objects saved are not deleted
        assert (list_ids[2:].sort() == [row.get('_id') for row in raw].sort())

        # test that there are only 3 gridfs
        raw = mongo.db['fs.files'].find({})
        assert raw.count() == 3

    def couverage_save_export(self, coverage):
        context = Context('coverage', coverage)
        context.fill_contributor_contexts(coverage)
        coverage_export_functions.postprocess(coverage,context)
        coverage_export_functions.save_export(coverage, context)

    def test_data_source_fetched_historical_and_save_export_use_context(self):
        list_ids = []
        contributor = models.Contributor.get('contrib_id')
        data_sources = models.DataSource.get(data_source_id='data_source_gtfs')
        for i in range(1, 6):
            self.populate_data_fetched_and_save_export(contributor)
        # test that there are only 3 data sources
        raw = mongo.db[models.DataSourceFetched.mongo_collection].find({
            'contributor_id': contributor.id,
            'data_source_id': data_sources[0].id
        })
        assert raw.count() == 3
        # Test the 3 last objects saved are not deleted
        assert (list_ids[2:].sort() == [row.get('_id') for row in raw].sort())

        raw = mongo.db[models.ContributorExport.mongo_collection].find({
            'contributor_id': contributor.id
        })
        assert raw.count() == 3
        # Test the 3 last objects saved are not deleted
        assert (list_ids[2:].sort() == [row.get('_id') for row in raw].sort())

        # test that there are only 6 gridfs :
        # 3 in DataSourceFetched
        # 3 in ContributorExport
        raw = mongo.db['fs.files'].find({})
        assert raw.count() == 6

    def test_data_source_fetched_historical_and_save_export_save_coverage_export_use_context(self):
        list_ids = []
        contributor = models.Contributor.get('contrib_id')
        data_sources = models.DataSource.get(data_source_id='data_source_gtfs')
        coverage = models.Coverage.get('c1')
        for i in range(1, 6):
            self.populate_data_fetched_and_save_export(contributor)
            self.couverage_save_export(coverage)
        # test that there are only 3 data sources
        raw = mongo.db[models.DataSourceFetched.mongo_collection].find({
            'contributor_id': contributor.id,
            'data_source_id': data_sources[0].id
        })
        assert raw.count() == 3
        # Test the 3 last objects saved are not deleted
        assert (list_ids[2:].sort() == [row.get('_id') for row in raw].sort())

        raw = mongo.db[models.ContributorExport.mongo_collection].find({
            'contributor_id': contributor.id
        })
        assert raw.count() == 3
        # Test the 3 last objects saved are not deleted
        assert (list_ids[2:].sort() == [row.get('_id') for row in raw].sort())


        raw = mongo.db[models.CoverageExport.mongo_collection].find({
            'coverage_id': 'c1'
        })
        assert raw.count() == 3
        # Test the 3 last objects saved are not deleted
        assert (list_ids[2:].sort() == [row.get('_id') for row in raw].sort())

        # test that there are only 6 gridfs :
        # 3 in DataSourceFetched
        # 3 in ContributorExport
        # 6 in CoverageExport
        raw = mongo.db['fs.files'].find({})
        assert raw.count() == 12
