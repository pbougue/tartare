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
from tartare.exceptions import ProtocolException

logger = logging.getLogger(__name__)


class AbstractProtocol(metaclass=ABCMeta):
    def __init__(self, url, options):
        self.url = url
        self.options = options

    @abstractmethod
    def publish(self, file, filename):
        pass


class HttpProtocol(AbstractProtocol):
    def publish(self, file, filename):
        logger.info('publishing file {filename} on {url}...'.format(filename=filename, url=self.url))
        if self.options:
            response = requests.post(self.url, auth=(self.options['authent']['username'], self['authent']['password']),
                                     files={'file': file, 'filename': filename}, timeout=10)
        else:
            response = requests.post(self.url, files={'file': file, 'filename': filename},
                                     timeout=10)
        if response.status_code != 200:
            message = 'error during publishing on {url}, status code => {status_code}'.format(
                url=self.url, status_code=response.status_code)
            logger.error(message)
            raise ProtocolException(message)


class FtpProtocol(AbstractProtocol):
    def publish(self, file, filename):
        directory = None
        if 'directory' in self.options and self.options['directory']:
            directory = self.options['directory']
        logger.info(
            'publishing file {filename} on ftp://{url}/{directory}...'.format(filename=filename, url=self.url,
                                                                              directory=directory if directory else ''))
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
                raise ProtocolException(message)

        full_code = session.storbinary('STOR {filename}'.format(filename=filename), file)
        session.quit()
        code, message = tuple(full_code.split('-'))
        if code != '226':
            message = 'error during publishing on ftp://{url} => {full_code}'.format(url=self.url, full_code=full_code)
            logger.error(message)
            raise ProtocolException(message)


class AbstractPublisher(metaclass=ABCMeta):
    @abstractmethod
    def publish(self, protocol_uploader, file, coverage_id):
        pass


class NavitiaPublisher(AbstractPublisher):
    def publish(self, protocol_uploader, file, coverage_id):
        # do some things
        filename = "{coverage}.zip".format(coverage=coverage_id)
        protocol_uploader.publish(file, filename)


class ODSPublisher(AbstractPublisher):
    def publish(self, protocol_uploader, file, coverage_id):
        # do some things
        filename = "{coverage}.zip".format(coverage=coverage_id)
        protocol_uploader.publish(file, filename)


class StopAreaPublisher(AbstractPublisher):
    def publish(self, protocol_uploader, file, coverage_id):
        import tempfile
        import os
        from zipfile import ZipFile
        source_filename = 'stops.txt'
        dest_filename = "{coverage}_stops.txt".format(coverage=coverage_id)

        with tempfile.TemporaryDirectory() as tmp_dirname, ZipFile(file, 'r') as gtfs_zip:
            dest_file_path = os.path.join(tmp_dirname, source_filename)
            logger.info('Extracting {} to {}.'.format(source_filename, dest_file_path))
            gtfs_zip.extract(source_filename, tmp_dirname)
            with open(dest_file_path, 'rb') as fp:
                protocol_uploader.publish(fp, dest_filename)
