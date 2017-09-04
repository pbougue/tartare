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

import logging

from tartare.processes.abstract_preprocess import AbstractProcess
from tartare.processes import contributor
from tartare.processes import coverage
from typing import Optional, List, Dict

from tartare.core.context import Context
from tartare.core.models import PreProcess
from tartare.http_exceptions import InvalidArguments


class PreProcessManager(object):
    @classmethod
    def get_preprocess_class(cls, preprocess_name: str, instance: str) -> type:
        try:
            if instance == 'contributor':
                return getattr(contributor, preprocess_name)
            elif instance == 'coverage':
                return getattr(coverage, preprocess_name)
            else:
                raise InvalidArguments('unknown instance {instance}'.format(instance=instance))
        except AttributeError:
            msg = 'impossible to build preprocess {} : modules within tartare.processes.{} have no class {}'.format(
                preprocess_name, instance, preprocess_name)
            logging.getLogger(__name__).error(msg)
            raise InvalidArguments(msg)

    @classmethod
    def get_preprocess(cls, context: Context, preprocess: PreProcess) -> AbstractProcess:
        """
        :param preprocess_name: Ruspell, FusioImport, ....
        :return: Ruspell, FusioImport, ... or FusioDataUpdate  Object
        """
        attr = cls.get_preprocess_class(preprocess.type, context.instance)
        try:
            return attr(context, preprocess)  # call to the contructor, with all the args
        except TypeError as e:
            msg = 'impossible to build preprocess {}, wrong arguments: {}'.format(preprocess.type, str(e))
            logging.getLogger(__name__).error(msg)
            raise InvalidArguments(msg)

    @classmethod
    def check_preprocesses_for_instance(cls, preprocesses: List[Dict[str, str]], instance: str) -> None:
        for preprocess in preprocesses:
            # will raise InvalidArguments if not valid
            PreProcessManager.get_preprocess_class(preprocess.get('type', ''), instance)

    @classmethod
    def check_preprocess_data_source_integrity(cls, preprocess_dict_list: List[Dict[str, str]],
                                               existing_data_source_ids: List[str], instance: str) -> None:
        for preprocess in preprocess_dict_list:
            if 'data_source_ids' in preprocess and preprocess['data_source_ids']:
                for data_source_id in preprocess['data_source_ids']:
                    if data_source_id not in existing_data_source_ids:
                        msg = "data_source referenced by id '{data_source_id}' in preprocess '{preprocess}' not found in {instance}".format(
                            data_source_id=data_source_id, preprocess=preprocess['type'], instance=instance)
                        logging.getLogger(__name__).error(msg)
                        raise InvalidArguments(msg)
