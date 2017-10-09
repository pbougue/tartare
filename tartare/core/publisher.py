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

from tartare import app
from tartare.core.calendar_handler import dic_to_memory_csv
from tartare.exceptions import ProtocolException
from zipfile import ZipFile, ZIP_DEFLATED
import tempfile
import os
from typing import List, BinaryIO, Optional
from tartare.core.models import Coverage, CoverageExport

logger = logging.getLogger(__name__)


class AbstractProtocol(metaclass=ABCMeta):
    def __init__(self, url: str, options: dict) -> None:
        self.url = url
        self.options = options

    def publish(self, file: BinaryIO, filename: str) -> None:
        pass


class HttpProtocol(AbstractProtocol):
    def publish(self, file: BinaryIO, filename: str) -> None:
        timeout = app.config.get('TYR_UPLOAD_TIMEOUT')
        logger.info('publishing file {filename} on {url}...'.format(filename=filename, url=self.url))
        if self.options:
            response = requests.post(self.url,
                                     auth=(self.options['authent']['username'], self.options['authent']['password']),
                                     files={'file': file, 'filename': filename}, timeout=timeout)
        else:
            response = requests.post(self.url, files={'file': file, 'filename': filename},
                                     timeout=timeout)
        if response.status_code != 200:
            message = 'error during publishing on {url}, status code => {status_code}'.format(
                url=self.url, status_code=response.status_code)
            logger.error(message)
            raise ProtocolException(message)


class FtpProtocol(AbstractProtocol):
    def __init__(self, url: str, options: dict) -> None:
        super().__init__(url, options)
        self.url = self.url.replace('ftp://', '') if self.url.startswith('ftp://') else self.url

    def publish(self, file: BinaryIO, filename: str) -> None:
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
                logger.error(str(message))
                session.quit()
                raise ProtocolException(message)

        full_code = session.storbinary('STOR {filename}'.format(filename=filename), file)
        session.quit()
        if not full_code.startswith('226'):
            error_message = 'error during publishing on ftp://{url} => {full_code}'.format(url=self.url,
                                                                                           full_code=full_code)
            logger.error(error_message)
            raise ProtocolException(error_message)


class AbstractPublisher(metaclass=ABCMeta):
    @abstractmethod
    def publish(self, protocol_uploader: AbstractProtocol, file: BinaryIO, coverage: Coverage,
                coverage_export: Optional[CoverageExport]) -> None:
        pass


class NavitiaPublisher(AbstractPublisher):
    def publish(self, protocol_uploader: AbstractProtocol, file: BinaryIO, coverage: Coverage,
                coverage_export: CoverageExport) -> None:
        filename = "{coverage}.zip".format(coverage=coverage.id)
        protocol_uploader.publish(file, filename)


class ODSPublisher(AbstractPublisher):
    @property
    def metadata_ordered_columns(self) -> List[str]:
        return ['ID', 'Description', 'Format', 'Type file', 'Download', 'Validity start date', 'Validity end date',
                'Script of Transformation', 'Licence', 'Source link', 'Publication update date']

    def publish(self, protocol_uploader: AbstractProtocol, file: BinaryIO, coverage: Coverage,
                coverage_export: CoverageExport) -> None:
        import datetime
        meta_data_dict = [
            {
                'ID': coverage.id + '-GTFS',
                'Description': 'Global transport in {coverage}'.format(coverage=coverage.id),
                'Format': 'GTFS',
                'Type file': 'Global',
                'Download': 'gtfs.zip',
                'Validity start date': coverage_export.validity_period.start_date.strftime('%Y%m%d'),
                'Validity end date': coverage_export.validity_period.end_date.strftime('%Y%m%d'),
                'Licence': coverage.license.name,
                'Source link': coverage.license.url,
                'Publication update date': datetime.datetime.now().strftime('%d/%m/%Y')
            }
        ]
        memory_csv = dic_to_memory_csv(meta_data_dict, self.metadata_ordered_columns)
        with tempfile.TemporaryDirectory() as tmp_dirname:
            zip_file_name = '{coverage}.zip'.format(coverage=coverage.id)
            zip_full_name = os.path.join(tmp_dirname, zip_file_name)
            with ZipFile(zip_full_name, 'a', ZIP_DEFLATED, False) as zip_out:
                zip_out.writestr('{coverage}.txt'.format(coverage=coverage.id), memory_csv.getvalue())
                zip_out.writestr('GTFS.zip', file.read())
            with open(zip_full_name, 'rb') as fp:
                protocol_uploader.publish(fp, zip_file_name)


class StopAreaPublisher(AbstractPublisher):
    def publish(self, protocol_uploader: AbstractProtocol, file: BinaryIO, coverage: Coverage,
                coverage_export: CoverageExport) -> None:
        source_filename = 'stops.txt'
        dest_filename = "{coverage}_stops.txt".format(coverage=coverage.id)

        with tempfile.TemporaryDirectory() as tmp_dirname, ZipFile(file, 'r') as gtfs_zip:
            dest_file_path = os.path.join(tmp_dirname, source_filename)
            logger.info('Extracting {} to {}.'.format(source_filename, dest_file_path))
            gtfs_zip.extract(source_filename, tmp_dirname)
            with open(dest_file_path, 'rb') as fp:
                protocol_uploader.publish(fp, dest_filename)
