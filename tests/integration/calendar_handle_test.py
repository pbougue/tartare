# coding=utf-8

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

import os
from glob import glob
from io import BytesIO
from tartare.core import calendar_handler
from zipfile import ZipFile, ZIP_DEFLATED



def test_merge_calendar():
    pwd = os.path.dirname(os.path.dirname(__file__))

    calendar_path = os.path.join(pwd, 'fixtures/gridcalendar/export_calendars.zip')
    ntfs_path = os.path.join(pwd, 'fixtures/ntfs/*.txt')

    ntfs_zip = ZipFile(BytesIO(), 'a', ZIP_DEFLATED, False)

    for filename in glob(ntfs_path):
        with open(filename, 'r') as file:
            ntfs_zip.writestr(os.path.basename(filename), file.read())

    with ZipFile(calendar_path, 'r') as calendar_zip:
        calendar_handler._merge_calendar(calendar_zip, ntfs_zip)
