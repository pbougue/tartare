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

from werkzeug.exceptions import HTTPException


class TartareException(HTTPException):
    """
    All tartare exceptions must inherit from this one and define a code and a short message
    """
    def __init__(self, detailed_message: Optional[str]=None) -> None:
        super(TartareException, self).__init__()
        self.data = {
            'message': self.message,
        }
        if detailed_message:
            self.data['error'] = detailed_message


class InvalidArguments(TartareException):
    code = 400
    message = 'Invalid arguments'


class DuplicateEntry(TartareException):
    code = 409
    message = 'Duplicate entry'


class InternalServerError(TartareException):
    code = 500
    message = 'Internal Server Error'


class ObjectNotFound(TartareException):
    code = 404
    message = 'Object Not Found'


class UnsupportedMediaType(TartareException):
    code = 415
    message = 'Unsupported Media Type'
