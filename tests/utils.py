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
import os
import tempfile
from zipfile import ZipFile

from mock import MagicMock
from requests import Response

from tartare.helper import get_md5_content_file


def to_dict(response):
    return json.loads(response.data.decode('utf-8'))


def to_json(dict):
    return json.dumps(dict)


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


def mock_requests_post(url, files, timeout):
    return get_response()


def get_response(status_code: int = 200, content: str = None) -> Response:
    response = MagicMock()
    response.status_code = status_code
    if content:
        response.content = content
    return response


def _get_file_fixture_full_path(rel_path):
    return '{}/{}'.format('{}/{}'.format(os.path.dirname(os.path.dirname(__file__)), 'tests/fixtures'), rel_path)


def assert_zip_contains_only_files_with_extensions(zip_file, extensions):
    for zip_info in zip_file.filelist:
        assert zip_info.filename[-3:] in extensions, print(
            'file {filename} should not be in zip archive (only {extensions} files allowed)'.format(
                filename=zip_info.filename, extensions=','.join(extensions)))


def assert_zip_contains_only_txt_files(zip_file):
    assert_zip_contains_only_files_with_extensions(zip_file, ['txt'])


def display_files_content(result_file_name, expected_file_name):
    with open(result_file_name, 'r') as result, open(expected_file_name, 'r') as expected:
        result_content = result.read()
        expected_content = expected.read()
        print("{res_content}\n(len={res_len})<========>\n{exp_content}\n(len={exp_len})".format(
            res_content=result_content, res_len=len(result_content), exp_content=expected_content,
            exp_len=len(expected_content)))


def assert_text_files_equals(result_file_name, expected_file_name):
    assert get_md5_content_file(result_file_name) == get_md5_content_file(expected_file_name), \
        display_files_content(result_file_name, expected_file_name)


def assert_zip_file_equals_ref_zip_file(zip_file, tmp_dir, ref_zip_file, ref_tmp_dir):
    with ZipFile(zip_file, 'r') as zip_file_handle, ZipFile(_get_file_fixture_full_path(ref_zip_file),
                                                            'r') as ref_zip_file_handle:
        except_files_list = ref_zip_file_handle.namelist()
        response_files_list = zip_file_handle.namelist()

        assert len(except_files_list) == len(response_files_list)
        zip_file_handle.extractall(tmp_dir)
        ref_zip_file_handle.extractall(ref_tmp_dir)

        for f in except_files_list:
            assert_text_files_equals('{}/{}'.format(ref_tmp_dir, f), '{}/{}'.format(tmp_dir, f))


def assert_content_equals_ref_file(content, ref_zip_file):
    with tempfile.TemporaryDirectory() as extract_result_tmp, tempfile.TemporaryDirectory() as ref_tmp:
        dest_zip_res = '{}/gtfs.zip'.format(extract_result_tmp)
        with open(dest_zip_res, 'wb') as f:
            f.write(content)
        assert_zip_file_equals_ref_zip_file(dest_zip_res, extract_result_tmp, ref_zip_file, ref_tmp)
