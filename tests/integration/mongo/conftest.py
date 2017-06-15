# Copyright (c) 2001-2015, Canal TP and/or its affiliates. All rights reserved.
#
# This file is part of Navitia,
#     the software to build cool stuff with public transport.
#
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

from tartare import app, mongo
import pytest
from tartare.core import models
from tests.docker_wrapper import MongoDocker, DownloadHttpServerDocker, DownloadFtpServerDocker, UploadFtpServerDocker
from tests.utils import to_json
from datetime import date


@pytest.yield_fixture(scope="session", autouse=True)
def docker():
    """
    a docker providing a mongo database is started once for all tests
    """
    with MongoDocker() as docker:
        yield docker


@pytest.fixture(scope="session", autouse=True)
def init_mongo_db(docker):
    """
    when the docker is started, we init flask once for the new database
    """
    app.config['MONGO_TEST_DBNAME'] = docker.db_name
    app.config['MONGO_TEST_HOST'] = docker.ip_addr
    mongo.init_app(app, 'MONGO_TEST')


@pytest.fixture(scope="function", autouse=True)
def empty_mongo(docker):
    """Empty mongo db before each tests"""
    with app.app_context():
        mongo.db.client.drop_database(docker.db_name)
        models.init_mongo()


@pytest.yield_fixture(scope="session", autouse=True)
def init_http_download_server():
    with DownloadHttpServerDocker() as download_server:
        yield download_server

@pytest.yield_fixture(scope="session", autouse=True)
def init_ftp_upload_server():
    with UploadFtpServerDocker() as upload_server:
        yield upload_server

@pytest.yield_fixture(scope="session", autouse=True)
def init_ftp_download_server():
    with DownloadFtpServerDocker() as download_server:
        yield download_server


@pytest.yield_fixture(scope="function")
def get_app_context():
    with app.app_context():
        yield


@pytest.fixture(scope="function")
def coverage_with_data_source_tram_lyon(app):
    coverage = app.post('/coverages',
                headers={'Content-Type': 'application/json'},
               data='{"id": "jdr", "name": "name of the coverage jdr", "data_sources": ["tram_lyon"]}')
    return to_json(coverage)['coverages'][0]

@pytest.fixture(scope="function")
def coverage(app):
    coverage = app.post('/coverages',
                headers={'Content-Type': 'application/json'},
               data='{"id": "jdr", "name": "name of the coverage jdr"}')
    return to_json(coverage)['coverages'][0]


@pytest.fixture(scope="function")
def contributor(app):
    contributor = app.post('/contributors',
                           headers={'Content-Type': 'application/json'},
                           data='{"id": "id_test", "name": "name_test", "data_prefix": "AAA"}')
    return to_json(contributor)['contributors'][0]

@pytest.fixture(scope="function")
def data_source(app, contributor):
    data_source = app.post('/contributors/{}/data_sources'.format(contributor.get('id')),
                           headers={'Content-Type': 'application/json'},
                           data='{"name": "bobette", "data_format": "gtfs",'
                                '"input": {"type": "url", "url": "http://stif.com/od.zip"}}')
    return to_json(data_source)['data_sources'][0]

@pytest.fixture(scope="function")
def coverage_obj(tmpdir, get_app_context):
    coverage = models.Coverage(id='test', name='test')
    coverage.environments['production'] = models.Environment(name='prod')
    publication_platform = models.Platform(type="navitia", protocol="http", url="http://tyr.prod/v0/instances/test")
    coverage.environments['production'].publication_platforms.append(publication_platform)
    coverage.save()
    return coverage


@pytest.fixture(scope="function")
def coverage_export_obj(tmpdir, get_app_context):
    p = models.ValidityPeriod(date(2017, 1, 1), date(2017, 1, 30))
    c = models.ContributorExportDataSource(data_source_id='1234', validity_period=p)
    contributors = models.CoverageExportContributor(contributor_id='fr-idf',
                                                    validity_period=p, data_sources=[c])
    coverage_export = models.CoverageExport(coverage_id='coverage1',
                                            gridfs_id='1234',
                                            validity_period=p,
                                            contributors=[contributors])
    coverage_export.save()
    return coverage_export
