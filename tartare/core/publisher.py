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


class AbstractProtocolPublisher(metaclass=ABCMeta):
    def __init__(self, url, options, coverage_id):
        self.url = url
        self.options = options
        self.filename = "{coverage}.zip".format(coverage=coverage_id)

    @abstractmethod
    def publish(self, file):
        pass


class HttpPublisher(AbstractProtocolPublisher):
    def publish(self, file):
        logger.info('publishing file {filename} on {url}...'.format(filename=self.filename, url=self.url))
        if self.options:
            response = requests.post(self.url, auth=(self.options['authent']['username'], self['authent']['password']),
                                     files={'file': file, 'filename': self.filename}, timeout=10)
        else:
            response = requests.post(self.url, files={'file': file, 'filename': self.filename},
                                     timeout=10)
        if response.status_code != 200:
            message = 'error during publishing on {url}, status code => {status_code}'.format(
                url=self.url, status_code=response.status_code)
            logger.error(message)
            raise PublishException(message)


class FtpPublisher(AbstractProtocolPublisher):
    def publish(self, file):
        directory = None
        if 'directory' in self.options and self.options['directory']:
            directory = self.options['directory']
        logger.info(
            'publishing file {filename} on ftp://{url}/{directory}...'.format(filename=self.filename, url=self.url,
                                                                              directory=directory))
        if 'authent' in self.options:
            session = ftplib.FTP(self.url, self.options['authent']['username'], self.options['authent']['password'])
        else:
            session = ftplib.FTP(self.url)
        if directory:
            try:
                session.cwd(directory)
            except ftplib.error_perm as message:
                logger.error(message)
                session.quit()
                raise PublishException(message)

        full_code = session.storbinary('STOR {filename}'.format(filename=self.filename), file)
        session.quit()
        code, message = tuple(full_code.split('-'))
        if code != '226':
            message = 'error during publishing on ftp://{url} => {full_code}'.format(url=self.url, full_code=full_code)
            logger.error(message)
            raise PublishException(message)


class AbstractPublisher(metaclass=ABCMeta):
    @abstractmethod
    def publish(self, protocol_publisher, file):
        pass


class NavitiaPublisher(AbstractPublisher):
    def publish(self, protocol_publisher, file):
        # do some things
        protocol_publisher.publish(file)


class ODSPublisher(AbstractPublisher):
    def publish(self, protocol_publisher, file):
        # do some things
        protocol_publisher.publish(file)


class StopAreaPublisher(AbstractPublisher):
    def publish(self, protocol_publisher, file):
        # do some things
        protocol_publisher.publish(file)
