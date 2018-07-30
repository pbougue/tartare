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

import pytest

from tartare.core.constants import PLATFORM_PROTOCOL_HTTP
from tartare.core.models import Platform
from tartare.core.publisher import ProtocolManager, AbstractProtocol
from tartare.exceptions import ProtocolManagerException


class TestUploader:
    def test_select_from_platform_ok(self):
        uploader = ProtocolManager.select_from_platform(
            Platform(PLATFORM_PROTOCOL_HTTP, 'ftp://whatever'))
        assert isinstance(uploader, AbstractProtocol)

    def test_select_from_platform_ko(self):
        with pytest.raises(ProtocolManagerException) as excinfo:
            ProtocolManager.select_from_platform(Platform('wrong_protocol', 'ftp://whatever'))
        assert excinfo.typename == 'ProtocolManagerException'
        assert str(excinfo.value) == 'unknown platform protocol "wrong_protocol"'
