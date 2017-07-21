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
from typing import Union

from tartare.core.models import DataSource, PreProcess
from tartare.interfaces import schema


def upgrade_dict(source: Union[DataSource, PreProcess], request_data: dict, key: str) -> None:
    map_model = {
        "data_sources": schema.DataSourceSchema,
        "preprocesses": schema.PreProcessSchema
    }
    existing_id = [d.id for d in source]
    logging.getLogger(__name__).debug("PATCH : list of existing {} ids {}".format(key, str(existing_id)))
    # constructing PATCH data
    patched_data = None
    if key in request_data:
        patched_data = map_model.get(key)(many=True).dump(source).data
        for item in request_data[key]:
            if item['id'] in existing_id:
                item2update = next((p for p in patched_data if p['id'] == item['id']), None)
                if item2update:
                    item2update.update(item)
            else:
                patched_data.append(item)
    if patched_data:
        request_data[key] = patched_data
