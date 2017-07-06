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

from importlib import import_module
from abc import ABCMeta, abstractmethod
import logging
from tartare.http_exceptions import InvalidArguments


class AbstractProcess(metaclass=ABCMeta):
    def __init__(self, context):
        self.context = context

    @abstractmethod
    def do(self):
        pass


class PreProcess(object):
    @classmethod
    def is_valid(cls, preprocess_name, instance):
        try:
            module = import_module('tartare.processes.{}'.format(instance))
            return getattr(module, preprocess_name)
        except AttributeError as e:
            msg = 'impossible to build preprocess {} : {}'.format(preprocess_name, e)
            logging.getLogger(__name__).error(msg)
            raise InvalidArguments(msg)
        except ImportError:
            msg = 'impossible to build preprocess {}, cannot find class'.format(preprocess_name)
            logging.getLogger(__name__).error(msg)
            raise InvalidArguments(msg)

    @classmethod
    def get_preprocess(cls, context, preprocess_name):
        """
        :param context:
        :param preprocess_name: Ruspell, FusioImport, ....
        :param instance: coverage or contributor
        :return: Ruspell, FusioImport, ... or FusioDataUpdate  Object
        """
        attr = cls.is_valid(preprocess_name, context.instance)
        try:
            return attr(context)  # call to the contructor, with all the args
        except TypeError as e:
            msg = 'impossible to build preprocess {}, wrong arguments: {}'.format(preprocess_name, e.message)
            logging.getLogger(__name__).error(msg)
            raise InvalidArguments(msg)
