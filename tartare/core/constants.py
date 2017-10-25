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

INPUT_TYPE_URL = 'url'
INPUT_TYPE_MANUAL = 'manual'
INPUT_TYPE_COMPUTED = 'computed'
INPUT_TYPE_DEFAULT = INPUT_TYPE_MANUAL
INPUT_TYPE_VALUES = [
    INPUT_TYPE_URL,
    INPUT_TYPE_MANUAL,
    INPUT_TYPE_COMPUTED,
]

DATA_FORMAT_GTFS = 'gtfs'
DATA_FORMAT_BANO_FILE = 'bano_file'
DATA_FORMAT_OSM_FILE = 'osm_file'
DATA_FORMAT_DIRECTION_CONFIG = 'direction_config'
DATA_FORMAT_RUSPELL_CONFIG = 'ruspell_config'
DATA_FORMAT_LINES_REFERENTIAL = 'lines_referential'
DATA_FORMAT_TR_PERIMETER = 'tr_perimeter'
DATA_FORMAT_PT_EXTERNAL_SETTINGS = 'pt_external_settings'
DATA_FORMAT_DEFAULT = DATA_FORMAT_GTFS
DATA_FORMAT_VALUES = [
    DATA_FORMAT_GTFS,
    DATA_FORMAT_BANO_FILE,
    DATA_FORMAT_OSM_FILE,
    DATA_FORMAT_DIRECTION_CONFIG,
    DATA_FORMAT_RUSPELL_CONFIG,
    DATA_FORMAT_LINES_REFERENTIAL,
    DATA_FORMAT_TR_PERIMETER,
    DATA_FORMAT_PT_EXTERNAL_SETTINGS
]
DATA_FORMAT_GENERATE_EXPORT = [
    DATA_FORMAT_GTFS,
    DATA_FORMAT_DIRECTION_CONFIG,
    DATA_FORMAT_BANO_FILE,
    DATA_FORMAT_OSM_FILE
]
DATA_FORMAT_WITH_VALIDITY = [
    DATA_FORMAT_GTFS
]

DATA_TYPE_GEOGRAPHIC = 'geographic'
DATA_TYPE_PUBLIC_TRANSPORT = 'public_transport'
DATA_TYPE_DEFAULT = DATA_TYPE_PUBLIC_TRANSPORT
DATA_TYPE_VALUES = [
    DATA_TYPE_GEOGRAPHIC,
    DATA_TYPE_PUBLIC_TRANSPORT
]

DATA_SOURCE_STATUS_FETCHING = 'fetching'
DATA_SOURCE_STATUS_FAILED = 'failed'
DATA_SOURCE_STATUS_UNCHANGED = 'unchanged'
DATA_SOURCE_STATUS_UPDATED = 'updated'
DATA_SOURCE_STATUS_NEVER_FETCHED = 'never_fetched'
DATA_SOURCE_STATUS_UNKNOWN = 'unknown'

DATA_SOURCE_STATUSES = [
    DATA_SOURCE_STATUS_FETCHING,
    DATA_SOURCE_STATUS_FAILED,
    DATA_SOURCE_STATUS_UNCHANGED,
    DATA_SOURCE_STATUS_UPDATED,
    DATA_SOURCE_STATUS_NEVER_FETCHED,
    DATA_SOURCE_STATUS_UNKNOWN,
]

EXCEPTED_DATA_SOURCES = {
    DATA_TYPE_GEOGRAPHIC: [DATA_FORMAT_BANO_FILE, DATA_FORMAT_OSM_FILE],
    DATA_TYPE_PUBLIC_TRANSPORT: [DATA_FORMAT_GTFS, DATA_FORMAT_DIRECTION_CONFIG,
                                 DATA_FORMAT_RUSPELL_CONFIG, DATA_FORMAT_LINES_REFERENTIAL,
                                 DATA_FORMAT_TR_PERIMETER, DATA_FORMAT_PT_EXTERNAL_SETTINGS]
}
