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
import logging

import pytest

import docker


@pytest.fixture(scope="function", autouse=True)
def empty_mongo():
    client = docker.from_env()
    mongo_server = client.containers(filters={"name": "tartare_test_mongo"})
    if not len(mongo_server) == 1:
        exit('expect one and only one mongo instance')
    mongo_server = mongo_server[0]
    """Empty mongo db before each tests"""
    client.exec_start(client.exec_create(container=mongo_server['Id'],
                       cmd='mongo tartare --eval "db.dropDatabase();"'))
