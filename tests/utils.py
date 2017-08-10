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
import json
from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED
from glob import glob
from contextlib import contextmanager
import os
from mock import MagicMock
from requests import Response


def to_json(response):
    return json.loads(response.data.decode('utf-8'))


def delete(app, url):
    """
        post on API with params as json
        """
    return app.delete(url)


def post(app, url, params, headers={'Content-Type': 'application/json'}):
    """
    post on API with params as json
    """
    return app.post(url,
                    headers=headers,
                    data=params)


def patch(app, url, params, headers={'Content-Type': 'application/json'}):
    """
    patch on API with params as json
    """
    return app.patch(url,
                     headers=headers,
                     data=params)


@contextmanager
def get_valid_ntfs_memory_archive():
    ntfs_file_name = 'ntfs.zip'
    ntfs_path = os.path.join(os.path.dirname(__file__), 'fixtures/ntfs/*.txt')
    with BytesIO() as ntfs_zip_memory:
        ntfs_zip = ZipFile(ntfs_zip_memory, 'a', ZIP_DEFLATED, False)
        for filename in glob(ntfs_path):
            ntfs_zip.write(filename, os.path.basename(filename))
        ntfs_zip.close()
        ntfs_zip_memory.seek(0)
        yield (ntfs_file_name, ntfs_zip_memory)


def mock_urlretrieve(url, target):
    with get_valid_ntfs_memory_archive() as (filename, ntfs_file):
        with open(target, 'wb') as out:
            out.write(ntfs_file.read())


def mock_zip_file(url, target):
    pass


def mock_requests_post(url, files, timeout):
    return get_response()


def get_response(status_code: int=200, content: str=None) -> Response:
    response = MagicMock()
    response.status_code = status_code
    if content:
        response.content = content
    return response


def _get_file_fixture_full_path(rel_path):
    return '{}/{}'.format('{}/{}'.format(os.path.dirname(os.path.dirname(__file__)), 'tests/fixtures'), rel_path)


def assert_files_equals(result_file_name, expected_file_name):
    with open(result_file_name, 'r') as result, open(expected_file_name, 'r') as expected:
        result_content = result.read()
        expected_content = expected.read()
        assert result_content == expected_content, print(
            "{res_content}\n(len={res_len})<========>\n{exp_content}\n(len={exp_len})".format(
                res_content=result_content, res_len=len(result_content), exp_content=expected_content,
                exp_len=len(expected_content)))
