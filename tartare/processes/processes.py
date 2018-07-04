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
from typing import List, Dict

from tartare.core.context import Context, ContributorExportContext
from tartare.core.models import Process
from tartare.http_exceptions import InvalidArguments
from tartare.processes import contributor
from tartare.processes import coverage
from tartare.processes.abstract_process import AbstractProcess


class ProcessManager(object):
    @classmethod
    def get_process_class(cls, process_name: str, instance: str) -> type:
        try:
            if instance == 'contributor':
                return getattr(contributor, process_name)
            elif instance == 'coverage':
                return getattr(coverage, process_name)
            else:
                raise InvalidArguments('unknown instance {instance}'.format(instance=instance))
        except AttributeError:
            msg = 'impossible to build process {} : modules within tartare.processes.{} have no class {}'.format(
                process_name, instance, process_name)
            logging.getLogger(__name__).error(msg)
            raise InvalidArguments(msg)

    @classmethod
    def get_process(cls, context: Context, process: Process) -> AbstractProcess:
        """
        :param context: current context
        :param process: process model object (api)
        :return: process instance to run (worker)
        """
        instance = 'contributor' if isinstance(context, ContributorExportContext) else 'coverage'
        attr = cls.get_process_class(process.type, instance)

        return attr(context, process)  # call to the constructor, with all the args


    @classmethod
    def check_processes_for_instance(cls, processes: List[Dict[str, str]], instance: str) -> None:
        for process in processes:
            # will raise InvalidArguments if not valid
            ProcessManager.get_process_class(process.get('type', ''), instance)

    @classmethod
    def check_process_data_source_integrity(cls, process_dict_list: List[Dict[str, str]],
                                               existing_data_source_ids: List[str], instance: str) -> None:
        for process in process_dict_list:
            if 'data_source_ids' in process and process['data_source_ids']:
                for data_source_id in process['data_source_ids']:
                    if data_source_id not in existing_data_source_ids:
                        msg = ("data_source referenced by id '{data_source_id}' in process '{process}' " +
                               "not found in {instance}").format(
                            data_source_id=data_source_id, process=process['type'], instance=instance)
                        logging.getLogger(__name__).error(msg)
                        raise InvalidArguments(msg)
