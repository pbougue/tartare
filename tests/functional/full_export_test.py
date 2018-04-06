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
import json
import os
from time import sleep

import pytest

from tests.functional.abstract_request_client import AbstractRequestClient


@pytest.mark.functional
class TestFullExport(AbstractRequestClient):
    def test_contrib_export_with_compute_directions(self):
        self.init_contributor('contributor.json')
        with open(self.get_fixtures_relative_path('compute_directions/config.json'), 'rb') as file:
            raw = self.post(
                '/contributors/contributor_with_preprocess_id/data_sources/compute_direction_config_id/data_sets',
                files={'file': file})
            self.assert_sucessful_create(raw)

        job_id = self.contributor_export('contributor_with_preprocess_id')
        self.wait_for_job_to_be_done(job_id, 'save_contributor_export')

        self.assert_export_file_equals_ref_file(contributor_id='contributor_with_preprocess_id',
                                                data_source_id='data_source_to_process_id',
                                                ref_file='compute_directions/ref_functional.zip')

    def test_contrib_export_with_ruspell(self):
        # create contributor with data_type : geographic
        self.init_contributor('contributor_geographic.json')

        job_id = self.contributor_export('geo')
        self.wait_for_job_to_be_done(job_id, 'save_contributor_export', nb_retries_max=20)

        # contributor with: config ruspell, bano data, gtfs and preprocess ruspell
        self.init_contributor('contributor_ruspell.json')

        # launch ruspell preprocess
        job_id = self.contributor_export('AMI')
        self.wait_for_job_to_be_done(job_id, 'save_contributor_export', nb_retries_max=20)

        self.assert_export_file_equals_ref_file(contributor_id='AMI', ref_file='ruspell/ref_gtfs.zip',
                                                data_source_id="Google-1", expected_filename='gtfs-processed.zip')

    def test_exports_combined(self):
        self.init_contributor('contributor_light.json')
        self.init_coverage('coverage.json')
        self.full_export('contributor_id', 'coverage_id', current_date='2017-12-14')

        self.assert_export_file_equals_ref_file(contributor_id='contributor_id',
                                                ref_file='compute_directions/functional.zip',
                                                data_source_id="data_source_to_process_id")

    def test_exports_combined_two_coverages(self):
        self.init_contributor('contributor_light.json')
        self.init_coverage('coverage.json')
        self.init_coverage('other_coverage.json')

        self.full_export('contributor_id', 'coverage_id', current_date='2017-12-14')
        self.full_export('contributor_id', 'coverage_id_2', current_date='2017-12-14')

    def test_contrib_export_preprocess_ko_before_ok(self):
        self.init_contributor('contributor_preprocess_ko.json')

        # launch export with a preprocess generating error => should end up being failed
        job_id = self.contributor_export('contributor_preprocess_ko')
        self.wait_for_job_to_be_done(job_id, 'preprocess', break_if='failed')

        self.init_contributor('contributor_headsign_short_name.json')

        # launch export generating success => should end up being done
        job_id = self.contributor_export('AMI')
        self.wait_for_job_to_be_done(job_id, 'save_contributor_export')

    def test_coverage_exports_callback_waits_for_contributor_full_export(self):
        self.init_contributor('contributor_sleeping.json')
        self.init_contributor('contributor_light.json')
        self.init_coverage('coverage_triggered.json')

        self.post('/actions/automatic_update?current_date=2017-08-15')
        self.wait_for_jobs_to_exist('automatic_update_coverage_export', 1)
        self.patch(
            '/contributors/{}/data_sources/{}'.format('contributor_id_sleeping', 'data_source_to_process_id_sleeping'),
            json.dumps({'input': {'url': "http://{HTTP_SERVER_IP}/gtfs/minimal_gtfs_modified.zip".format(
                HTTP_SERVER_IP=os.getenv('HTTP_SERVER_IP'))}}))
        self.post('/actions/automatic_update?current_date=2017-08-15')
        # here there should be 2 coverage exports:
        # - one for the first automatic update because all data set were new
        # - one other triggered by contributor_sleeping data set updated
        self.wait_for_jobs_to_exist('automatic_update_coverage_export', 2)
        exports = self.get_dict_from_response(self.get('coverages/coverage_id_triggered/exports'))['exports']
        assert len(exports) == 2

    def test_contrib_export_with_gtfs2ntfs(self):
        # contributor with: config ruspell, bano data, gtfs and preprocess ruspell
        self.init_contributor('contributor_gtfs2ntfs.json')

        # launch gtfs2ntfs preprocess
        job_id = self.contributor_export('AMI')
        self.wait_for_job_to_be_done(job_id, 'save_contributor_export', nb_retries_max=20)

    def test_auto_update_one_contributor(self):
        self.init_contributor('contributor_light.json')
        self.init_coverage('coverage.json')
        self.post('/actions/automatic_update?current_date=2017-08-15')
        job = self.wait_for_jobs_to_exist('automatic_update_coverage_export', 1)
        self.wait_for_job_to_be_done(job['id'], 'save_coverage_export')
        exports = self.get_dict_from_response(self.get('coverages/coverage_id/exports'))['exports']
        assert len(exports) == 1
