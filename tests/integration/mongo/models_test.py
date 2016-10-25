
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
from tartare.core import models


def test_coverage_fetch(get_app_context):
    """
    basic use of mnogo, we create a Coverage and persist it, we should be able to get it back
    """
    assert len(models.Coverage.all()) == 0
    coverage = models.Coverage(id='id_of_the_coverage',
                               name='name of the coverage')
    coverage.save()

    persisted_coverages = list(models.Coverage.all())
    assert len(persisted_coverages) == 1

    assert persisted_coverages[0].id == 'id_of_the_coverage'
    assert persisted_coverages[0].name == 'name of the coverage'
