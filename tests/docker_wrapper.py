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
import logging
import os
import subprocess
from abc import ABCMeta, abstractmethod

import docker
import pytest
from docker.errors import APIError


class AbstractDocker(metaclass=ABCMeta):
    @property
    def fixtures_directory(self):
        current_dir = os.path.dirname(os.path.realpath(__file__))
        return os.path.join(current_dir, 'fixtures')

    def _get_docker_file(self):
        """
            Return a dumb DockerFile

            The best way to get the image would be to get it from dockerhub,
            but with this dumb wrapper the runtime time of the unit tests
            is reduced by 10s
        """
        from io import BytesIO
        return BytesIO("FROM {}".format(self.image_name).encode())

    @property
    def volumes_bindings(self):
        return None

    def wait_until_available(self):
        return

    def _remove_temporary_files(self):
        pass

    def _fetch_image(self):
        self.execute_manual_build()

    @abstractmethod
    def image_name(self):
        pass

    @abstractmethod
    def container_name(self):
        pass

    @property
    def ports(self):
        return None

    @property
    def port_bindings(self):
        return None

    @property
    def env_vars(self):
        return None

    @property
    def volumes(self):
        return []

    def __enter__(self):
        return self

    def execute_manual_build(self):
        self.logger.info('building docker image')
        for build_output in self.docker.build(fileobj=self._get_docker_file(),
                                              tag=self.image_name, rm=True):
            self.logger.debug(build_output)

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.docker = docker.from_env()
        if len(self.docker.images(name=self.image_name)) == 0:
            self._fetch_image()

        host_config = self.docker.create_host_config(
            binds=self.volumes_bindings,
            port_bindings=self.port_bindings
        )

        try:
            self.container_id = self.docker.create_container(self.image_name, name=self.container_name,
                                                             ports=self.ports,
                                                             environment=self.env_vars,
                                                             volumes=self.volumes, host_config=host_config).get('Id')
            self.logger.info("docker id is {}".format(self.container_id))
            self.logger.info("starting the temporary docker for image {}".format(self.image_name))
            self.docker.start(self.container_id)
            self.ip_addr = self.docker.inspect_container(self.container_id).get('NetworkSettings', {}).get('IPAddress')
            if not self.ip_addr:
                self.logger.error("temporary docker {} not started".format(self.container_id))
                assert False
            self.logger.info("IP addr is {}".format(self.ip_addr))
            self.wait_until_available()
        except APIError as e:
            pytest.exit(
                "error during setup of docker container {}, aborting. Details:\n{}".format(self.container_name, str(e)))

    def __exit__(self, *args, **kwargs):
        if self.volumes:
            self._remove_temporary_files()
        self.docker.stop(container=self.container_id)

        self.docker.remove_container(container=self.container_id, v=True)

        # test to be sure the docker is removed at the end
        for cont in self.docker.containers(all=True):
            if cont['Image'].split(':')[0] == self.image_name:
                if self.container_id in (name[1:] for name in cont['Names']):
                    self.logger.error("something is strange, the container is still there ...")
                    exit(2)


class AbstractHttpServerDocker(AbstractDocker):
    def container_name(self):
        pass

    def image_name(self):
        pass

    def wait_until_available(self):
        self.logger.info("Waiting for container to be available")
        command = 'wget http://{} --retry-connrefused --tries=5 --wait=1 --spider'.format(self.ip_addr + ':80')
        process = subprocess.Popen(command.split(), stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error = process.communicate()
        if process.returncode != 0:
            raise str(error)


class DownloadHttpServerDocker(AbstractHttpServerDocker):
    @property
    def working_dir(self):
        return '/var/www'

    @property
    def volumes(self):
        return [self.working_dir]

    @property
    def container_name(self):
        return 'http_download_server'

    @property
    def image_name(self):
        return 'visity/webdav'

    @property
    def volumes_bindings(self):
        return {
            self.fixtures_directory: {
                'bind': self.working_dir,
                'mode': 'rw',
            },
        }

    def _remove_temporary_files(self):
        exec_id = self.docker.exec_create(container=self.container_id,
                                          cmd='rm -rf {working_dir}/.temp'.format(working_dir=self.working_dir))
        self.docker.exec_start(exec_id=exec_id)


class DownloadHttpServerAuthentDocker(AbstractHttpServerDocker):
    @property
    def working_dir(self):
        return '/var/webdav'

    @property
    def volumes(self):
        return [self.working_dir]

    @property
    def container_name(self):
        return 'http_download_authent_server'

    @property
    def image_name(self):
        return 'morrisjobke/webdav'

    @property
    def volumes_bindings(self):
        return {
            self.fixtures_directory: {
                'bind': self.working_dir,
                'mode': 'ro',
            },
        }
    @property
    def env_vars(self):
        return {'USERNAME': 'user@domain.com', 'PASSWORD': 'myPassword*'}

    @property
    def properties(self):
        props = self.env_vars
        props['ROOT'] = 'webdav/'
        return props


class DownloadFtpServerDocker(AbstractDocker):
    @property
    def working_dir(self):
        return '/var/lib/ftp'

    @property
    def volumes(self):
        return [self.working_dir]

    @property
    def container_name(self):
        return 'ftp_download_server'

    @property
    def image_name(self):
        return 'gimoh/pureftpd'

    @property
    def volumes_bindings(self):
        return {
            self.fixtures_directory: {
                'bind': self.working_dir,
                'mode': 'rw',
            },
        }


class UploadFtpServerDocker(AbstractDocker):
    # see credentials copied here : tests/fixtures/authent/ftp_upload_users/pureftpd.passwd
    @property
    def user(self):
        return 'tartare_user'

    @property
    def password(self):
        return 'tartare_password'

    @property
    def conf_dir(self):
        return '/etc/pure-ftpd/passwd'

    @property
    def volumes(self):
        return [self.conf_dir]

    @property
    def container_name(self):
        return 'ftp_upload_server'

    @property
    def image_name(self):
        return 'stilliard/pure-ftpd:hardened'

    @property
    def port_bindings(self):
        """
        See https://github.com/stilliard/docker-pure-ftpd/blob/master/Dockerfile
        """
        return {nb: nb for nb in range(30000, 30010)}

    @property
    def ports(self):
        return [nb for nb in range(30000, 30010)]

    @property
    def env_vars(self):
        return {'PUBLICHOST': 'localhost'}

    @property
    def volumes_bindings(self):
        return {
            os.path.join(self.fixtures_directory, 'authent', 'ftp_upload_users'): {
                'bind': self.conf_dir,
                'mode': 'ro',
            },
        }


class MongoDocker(AbstractDocker):
    @property
    def db_name(self):
        return 'tartare_test'

    @property
    def container_name(self):
        return 'tartare_test_mongo'

    @property
    def image_name(self):
        return 'mongo'
