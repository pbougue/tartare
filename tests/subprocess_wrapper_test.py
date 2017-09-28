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

from tartare.core.subprocess_wrapper import SubProcessWrapper
from tartare.exceptions import CommandRuntimeException
import pytest


def test_subprocess_wrapper_invalid_command():
    subp = SubProcessWrapper('Test')
    with pytest.raises(CommandRuntimeException) as excinfo:
        subp.run_cmd("abcd")
    assert str(excinfo.value) == "Test: b'/bin/sh: 1: abcd: not found\\n'"


def test_subprocess_wrapper_valid_command():
    subp = SubProcessWrapper('Test')
    assert not subp.run_cmd("ls")
