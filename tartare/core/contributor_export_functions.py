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
from tartare.url_dataset_fetcher import UrlDataSetFetcher
from tartare.core.context import Context

logger = logging.getLogger(__name__)

def merge(contributor, context):
    logger.info("contributor_id : %s", contributor.id)

def postprocess(contributor, context):
    logger.info("contributor_id : %s", contributor.id)


def fetch_dataset(data_sources):
    map_fetcher = {
        "url": UrlDataSetFetcher,
        "ftp": UrlDataSetFetcher
    }
    context = Context()

    for d in data_sources:
        type = d.input.get('type')
        kls = map_fetcher.get(type)
        if kls is None:
            logger.info("Unknown type: %s", type)
            continue
        fetcher = kls(d, context)
        context = fetcher.fetch()

    return context
