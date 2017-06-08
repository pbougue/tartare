# Copyright (c) 2001-2015, Canal TP and/or its affiliates. All rights reserved.
#
# This file is part of Navitia,
#     the software to build cool stuff with public transport.
#
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
import docker
import logging
from abc import ABCMeta, abstractmethod


class AbstractDocker(metaclass=ABCMeta):
    def _get_docker_file(self):
        return None

    def _get_volumes_bindings(self):
        return []

    @abstractmethod
    def _fetch_image(self):
        pass

    @abstractmethod
    def _get_image_name(self):
        pass

    @abstractmethod
    def _get_container_name(self):
        pass

    def _get_volumes(self):
        return []

    def __enter__(self):
        return self

    def execute_manual_build(self):
        self.logger.info('building docker image')
        for build_output in self.docker.build(fileobj=self._get_docker_file(),
                                              tag=self._get_image_name(), rm=True):
            self.logger.debug(build_output)

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.docker = docker.from_env()
        self._fetch_image()

        volumes = self._get_volumes()
        host_config = self.docker.create_host_config(
            binds=self._get_volumes_bindings()
        ) if len(volumes) else None

        self.container_id = self.docker.create_container(self._get_image_name(), name=self._get_container_name(),
                                                         volumes=volumes, host_config=host_config).get('Id')
        self.logger.info("docker id is {}".format(self.container_id))
        self.logger.info("starting the temporary docker for image {}".format(self._get_image_name()))
        self.docker.start(self.container_id)
        self.ip_addr = self.docker.inspect_container(self.container_id).get('NetworkSettings', {}).get('IPAddress')
        if not self.ip_addr:
            self.logger.error("temporary docker {} not started".format(self.container_id))
            assert False
        self.logger.info("IP addr is {}".format(self.ip_addr))

    def __exit__(self, *args, **kwargs):
        logging.getLogger(__name__).info("stopping the temporary docker")
        self.docker.stop(container=self.container_id)

        logging.getLogger(__name__).info("removing the temporary docker")
        self.docker.remove_container(container=self.container_id, v=True)

        # test to be sure the docker is removed at the end
        for cont in self.docker.containers(all=True):
            if cont['Image'].split(':')[0] == self._get_image_name():
                if self.container_id in (name[1:] for name in cont['Names']):
                    self.logger.error("something is strange, the container is still there ...")
                    exit(1)


class DownloadServerDocker(AbstractDocker):
    def _fetch_image(self):
        self.docker.pull(self._get_image_name())

    def _get_volumes(self):
        return ['/var/www']

    def _get_container_name(self):
        return 'http_download_server'

    def _get_image_name(self):
        return 'visity/webdav'

    def _get_volumes_bindings(self):
        current_dir = os.path.dirname(os.path.realpath(__file__))
        gtfs_http_fixtures_dir = os.path.join(current_dir, 'fixtures', 'gtfs', 'http', '')
        return {
            gtfs_http_fixtures_dir: {
                'bind': '/var/www',
                'mode': 'rw',
            },
        }


class MongoDocker(AbstractDocker):
    @property
    def db_name(self):
        return 'tartare_test'

    def _fetch_image(self):
        self.execute_manual_build()

    def _get_docker_file(self):
        """
            Return a dumb DockerFile

            The best way to get the image would be to get it from dockerhub,
            but with this dumb wrapper the runtime time of the unit tests
            is reduced by 10s
        """
        from io import BytesIO
        return BytesIO("FROM {}".format(self._get_image_name()).encode())

    def _get_container_name(self):
        return 'tartare_test_mongo'

    def _get_image_name(self):
        return 'mongo'
