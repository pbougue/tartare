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

import tartare
import pytest
import os


@pytest.fixture(scope="module")
def app():
    """ Return a handler over flask API """
    return tartare.app.test_client()


@pytest.fixture(scope="function")
def fixture_dir():
    pwd = os.path.dirname(os.path.dirname(__file__))
    return os.path.join(pwd, 'fixtures/')


@pytest.fixture(scope="session", autouse=True)
def local_celery():
    """
    celery tasks aren't deferred, they are executed locally by blocking
    """
    tartare.app.config['CELERY_ALWAYS_EAGER'] = True
    tartare.app.config['CELERY_TASK_EAGER_PROPAGATES'] = True
    tartare.app.config['ENABLE_SEND_ERROR_EMAILS'] = False
    tartare.celery.conf.update(tartare.app.config)

