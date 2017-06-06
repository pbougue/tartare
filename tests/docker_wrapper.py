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

# python image
MONGO_IMAGE = 'mongo'
MONGO_CONTAINER_NAME = 'tartare_test_mongo'

HTTP_SERVER_IMAGE = 'visity/webdav'


def _get_docker_file():
    """
    Return a dumb DockerFile

    The best way to get the image would be to get it from dockerhub,
    but with this dumb wrapper the runtime time of the unit tests
    is reduced by 10s
    """
    from io import BytesIO
    return BytesIO("FROM {}".format(MONGO_IMAGE).encode())


class DownloadServerDocker(object):
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info('DownloadServerDocker')
        current_dir = os.path.dirname(os.path.realpath(__file__))
        gtfs_http_fixtures_dir = os.path.join(current_dir, 'fixtures', 'gtfs', 'http', '')
        self.logger.info(gtfs_http_fixtures_dir)
        self.docker = docker.Client(base_url='unix://var/run/docker.sock')
        volumes = ['/var/www']
        volume_bindings = {
            gtfs_http_fixtures_dir: {
                'bind': '/var/www',
                'mode': 'rw',
            },
        }
        host_config = self.docker.create_host_config(
            binds=volume_bindings
        )
        self.docker.pull(HTTP_SERVER_IMAGE)
        self.container_id = self.docker.create_container(HTTP_SERVER_IMAGE, name='http_download_server', volumes=volumes, host_config=host_config).get('Id')
        self.logger.info("docker id is {}".format(self.container_id))
        self.logger.info("starting the temporary docker")
        self.docker.start(self.container_id)
        self.ip_addr = self.docker.inspect_container(self.container_id).get('NetworkSettings', {}).get('IPAddress')
        self.logger.info("IP addr is {}".format(self.ip_addr))

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        self.logger.info("stoping the temporary docker")
        self.docker.stop(container=self.container_id)

        self.logger.info("removing the temporary docker")
        self.docker.remove_container(container=self.container_id, v=True)


class MongoDocker(object):
    DBNAME = 'tartare_test'
    """
    launch a temporary docker for integration tests
    """
    def __init__(self):
        log = logging.getLogger(__name__)
        self.docker = docker.Client(base_url='unix://var/run/docker.sock')

        log.info('building docker image')
        for build_output in self.docker.build(fileobj=_get_docker_file(),
                                              tag=MONGO_IMAGE, rm=True):
            log.debug(build_output)

        self.container_id = self.docker.create_container(MONGO_IMAGE,
                                                         name=MONGO_CONTAINER_NAME).get('Id')

        log.info("docker id is {}".format(self.container_id))

        log.info("starting the temporary docker")
        self.docker.start(self.container_id)
        self.ip_addr = self.docker.inspect_container(self.container_id).get('NetworkSettings', {}).get('IPAddress')

        if not self.ip_addr:
            log.error("temporary docker {} not started".format(self.container_id))
            assert False

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        logging.getLogger(__name__).info("stoping the temporary docker")
        self.docker.stop(container=self.container_id)

        logging.getLogger(__name__).info("removing the temporary docker")
        self.docker.remove_container(container=self.container_id, v=True)

        # test to be sure the docker is removed at the end
        for cont in self.docker.containers(all=True):
            if cont['Image'].split(':')[0] == MONGO_IMAGE:
                if self.container_id in (name[1:] for name in cont['Names']):
                    logging.getLogger(__name__).error("something is strange, the container is still there ...")
                    exit(1)
