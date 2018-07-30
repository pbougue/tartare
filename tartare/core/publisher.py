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
import ftplib
import logging
from abc import ABCMeta
from typing import List, BinaryIO, Optional

import requests

from tartare import app
from tartare.core.constants import PLATFORM_PROTOCOL_FTP, PLATFORM_PROTOCOL_HTTP
from tartare.core.gridfs_handler import GridFsHandler
from tartare.core.models import DataSource, Platform, PlatformOptions
from tartare.exceptions import ProtocolException, ProtocolManagerException

logger = logging.getLogger(__name__)


class AbstractProtocol(metaclass=ABCMeta):
    def __init__(self, url: str, options: Optional[PlatformOptions]) -> None:
        self.url = url
        self.options = options

    def publish(self, file: BinaryIO, filename: str) -> None:
        pass


class HttpProtocol(AbstractProtocol):
    def publish(self, file: BinaryIO, filename: str) -> None:
        timeout = app.config.get('TYR_UPLOAD_TIMEOUT')
        logger.info('publishing file {filename} on {url}...'.format(filename=filename, url=self.url))
        if self.options and self.options.authent:
            response = requests.post(self.url,
                                     auth=(self.options.authent.username, self.options.authent.password),
                                     files={'file': (filename, file)}, timeout=timeout)
        else:
            response = requests.post(self.url, files={'file': (filename, file)}, timeout=timeout)
        if response.status_code != 200:
            message = 'error during publishing on {url}, status code => {status_code}'.format(
                url=self.url, status_code=response.status_code)
            logger.error(message)
            raise ProtocolException(message)


class FtpProtocol(AbstractProtocol):
    def __init__(self, url: str, options: Optional[PlatformOptions]) -> None:
        super().__init__(url, options)
        self.url = self.url.replace('ftp://', '') if self.url.startswith('ftp://') else self.url

    def publish(self, file: BinaryIO, filename: str) -> None:
        directory = self.options.directory if self.options and self.options.directory else ''
        logger.info(
            'publishing file {filename} on ftp://{url}/{directory}...'.format(filename=filename, url=self.url,
                                                                              directory=directory))
        try:
            if self.options and self.options.authent:
                session = ftplib.FTP(self.url, self.options.authent.username, self.options.authent.password)
            else:
                session = ftplib.FTP(self.url)

            if directory:
                session.cwd(directory)
        except ftplib.error_perm as message:
            logger.error(str(message))
            raise ProtocolException(message)

        full_code = session.storbinary('STOR {filename}'.format(filename=filename), file)
        session.quit()
        if not full_code.startswith('226'):
            error_message = 'error during publishing on ftp://{url} => {full_code}'.format(url=self.url,
                                                                                           full_code=full_code)
            logger.error(error_message)
            raise ProtocolException(error_message)


class ProtocolManager:
    publishers_by_protocol = {
        PLATFORM_PROTOCOL_HTTP: HttpProtocol,
        PLATFORM_PROTOCOL_FTP: FtpProtocol
    }

    @classmethod
    def select_from_platform(cls, platform: Platform) -> AbstractProtocol:
        if platform.protocol not in cls.publishers_by_protocol:
            error_message = 'unknown platform protocol "{protocol}"'.format(protocol=platform.protocol)
            raise ProtocolManagerException(error_message)
        publisher_class = cls.publishers_by_protocol[platform.protocol]
        return publisher_class(platform.url, platform.options)


class Publisher(metaclass=ABCMeta):
    def __init__(self, protocol_uploader: AbstractProtocol) -> None:
        self.protocol_uploader = protocol_uploader

    def publish(self, input_data_source_ids: List[str]) -> None:
        for input_data_source_id in input_data_source_ids:
            data_source = DataSource.get_one(input_data_source_id)
            data_set = data_source.get_last_data_set()
            data_set_file = GridFsHandler().get_file_from_gridfs(data_set.gridfs_id)
            data_set_file_name = data_set_file.filename

            self.protocol_uploader.publish(data_set_file, data_set_file_name)
