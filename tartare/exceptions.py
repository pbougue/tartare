# Copyright (c) 2001-2015, Canal TP and/or its affiliates. All rights reserved.
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
from typing import Optional


class ColumnNotFound(Exception):
    def __init__(self, message: Optional[str] = '') -> None:
        self.message = message


class FileNotFound(Exception):
    def __init__(self, message: Optional[str] = '') -> None:
        self.message = message


class InvalidFile(Exception):
    def __init__(self, message: Optional[str] = '') -> None:
        self.message = message


class ProtocolException(Exception):
    pass


class PublisherException(Exception):
    pass


class ProtocolManagerException(Exception):
    pass


class PublisherManagerException(Exception):
    pass


class GuessFileNameFromUrlException(Exception):
    pass


class FetcherException(Exception):
    pass


class FusioException(Exception):
    pass


class ValidityPeriodException(Exception):
    pass


class IntegrityException(Exception):
    pass


class EntityNotFound(Exception):
    pass


class ParameterException(Exception):
    pass


class RuntimeException(Exception):
    pass


class CommandRuntimeException(Exception):
    def __init__(self, command: str, message: Optional[str] = '') -> None:
        message = '{}: {}'.format(command, message)
        super(CommandRuntimeException, self).__init__(message)
