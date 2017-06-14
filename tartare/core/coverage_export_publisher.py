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
from abc import ABCMeta, abstractmethod
import logging

import requests

from tartare.exceptions import PublishException

logger = logging.getLogger(__name__)


class AbstractPublisher(metaclass=ABCMeta):
    def __init__(self, url, authent, timeout=120):
        self.url = url
        self.authent = authent
        self.timeout = timeout

    @abstractmethod
    def publish(self, file):
        pass


class HttpPublisher(AbstractPublisher):
    def publish(self, file):
        logger.info('publishing file {filename} on {url}...'.format(filename=file.filename, url=self.url))
        if self.authent:
            response = requests.post(self.url, auth=(self.authent.username, self.authent.password),
                                     files={'file': file, 'filename': file.filename}, timeout=self.timeout)
        else:
            response = requests.post(self.url, files={'file': file, 'filename': file.filename}, timeout=self.timeout)
        if response.status_code != 200:
            message = 'error during publishing on {url}, status code => {status_code}'.format(
                url=self.url, status_code=response.status_code)
            logger.error(message)
            raise PublishException(message)


class FtpPublisher(AbstractPublisher):
    def publish(self, file):
        logger.info('publishing file {filename} on ftp://{url}...'.format(filename=file.filename, url=self.url))
        if self.authent:
            session = ftplib.FTP(self.url, self.authent.username, self.authent.password)
        else:
            session = ftplib.FTP(self.url)
        full_code = session.storbinary('STOR {filename}'.format(filename=file.filename), file)
        code, message = tuple(full_code.split('-'))
        if code != '226':
            message = 'error during publishing on ftp://{url} => {full_code}'.format(url=self.url, full_code=full_code)
            logger.error(message)
            raise PublishException(message)
        file.close()
        session.quit()
