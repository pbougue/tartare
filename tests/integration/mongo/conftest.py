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

from tests.docker_wrapper import MongoDocker


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
    app.config['MONGO_TEST_DBNAME'] = docker.DBNAME
    app.config['MONGO_TEST_HOST'] = docker.ip_addr
    mongo.init_app(app, 'MONGO_TEST')


@pytest.fixture(scope="function", autouse=True)
def empty_mongo(docker):
    """Empty mongo db before each tests"""
    with app.app_context():
        mongo.db.client.drop_database(docker.DBNAME)
    #TODO try to remove the code below
    # problem is the empty_mongo function is called after each tests, which errase the indexes  previously created (cf. tartare.__init__.py)
    with app.app_context():
        db = mongo.db.client[docker.DBNAME]
        db['contributors'].ensure_index("data_prefix", unique=True)


@pytest.yield_fixture(scope="function")
def get_app_context():
    with app.app_context():
        yield
