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
from datetime import date

import pytest

from tartare.core.constants import DATA_FORMAT_TITAN, DATA_FORMAT_GTFS, DATA_FORMAT_OBITI, DATA_FORMAT_NEPTUNE
from tartare.core.models import ValidityPeriod
from tartare.core.validity_period_finder import ValidityPeriodFinder
from tartare.exceptions import InvalidFile, ValidityPeriodException
from tests.utils import _get_file_fixture_full_path


def test_zip_file_only_calendar():
    file = _get_file_fixture_full_path('gtfs/some_archive.zip')
    validity_period = ValidityPeriodFinder.select_computer_and_find(file)
    assert validity_period.start_date == date(2015, 3, 25)
    assert validity_period.end_date == date(2015, 8, 26)


def test_zip_file_only_feed_info():
    file = _get_file_fixture_full_path('validity_period/gtfs_with_feed_info.zip')
    validity_period = ValidityPeriodFinder.select_computer_and_find(file)
    assert validity_period.start_date == date(2016, 4, 11)
    assert validity_period.end_date == date(2016, 12, 31)


def test_zip_file_only_feed_info_invalid():
    file = _get_file_fixture_full_path('validity_period/gtfs_with_feed_info_invalid.zip')
    with pytest.raises(InvalidFile) as excinfo:
        ValidityPeriodFinder.select_computer_and_find(file)
    assert str(excinfo.value) == "impossible to parse file feed_info.txt, error Usecols do not match names."


def test_zip_file_only_feed_info_missing_dates():
    file = _get_file_fixture_full_path('validity_period/gtfs_with_feed_info_missing_dates.zip')
    validity_period = ValidityPeriodFinder.select_computer_and_find(file)
    assert validity_period.start_date == date(2016, 10, 4), print(validity_period.start_date)
    assert validity_period.end_date == date(2016, 12, 24), print(validity_period.end_date)


def test_zip_file_invalid():
    file = _get_file_fixture_full_path('gtfs/bob.zip')
    with pytest.raises(InvalidFile) as excinfo:
        ValidityPeriodFinder.select_computer_and_find(file)
    assert str(excinfo.value) == "{} is not a zip file or not exist".format(file)


@pytest.mark.parametrize("data_format", [
    DATA_FORMAT_GTFS,
    DATA_FORMAT_TITAN,
    DATA_FORMAT_OBITI,
    DATA_FORMAT_NEPTUNE,
])
def test_not_zipfile(data_format):
    file = _get_file_fixture_full_path('ntfs/calendar.txt')
    with pytest.raises(InvalidFile) as excinfo:
        ValidityPeriodFinder.select_computer_and_find(file, data_format)
    assert str(excinfo.value) == "{} is not a zip file or not exist".format(file)


@pytest.mark.parametrize("data_format,message", [
    (DATA_FORMAT_GTFS, 'file zip {file} without at least one of calendar.txt,calendar_dates.txt'),
    (DATA_FORMAT_TITAN, 'file zip {file} without CALENDRIER_VERSION_LIGNE.txt'),
    (DATA_FORMAT_OBITI, 'file zip {file} without vehiclejourney.csv'),
    (DATA_FORMAT_NEPTUNE, 'file zip {file} without at least one xml'),
])
def test_empty_zipfile(data_format, message):
    file = _get_file_fixture_full_path('validity_period/empty_archive.zip')
    with pytest.raises(InvalidFile) as excinfo:
        ValidityPeriodFinder.select_computer_and_find(file, data_format)
    assert str(excinfo.value) == message.format(file=file)


def test_calendar_without_end_date_column():
    file = _get_file_fixture_full_path('validity_period/calendar_without_end_date.zip')
    with pytest.raises(InvalidFile) as excinfo:
        ValidityPeriodFinder.select_computer_and_find(file)
    assert str(excinfo.value) == "impossible to parse file calendar.txt, error Usecols do not match names."


def test_calendar_without_start_date_column():
    file = _get_file_fixture_full_path('validity_period/calendar_without_start_date.zip')
    with pytest.raises(InvalidFile) as excinfo:
        ValidityPeriodFinder.select_computer_and_find(file)
    assert str(excinfo.value) == "impossible to parse file calendar.txt, error Usecols do not match names."


def test_gtfs_without_calendar():
    file = _get_file_fixture_full_path('validity_period/gtfs_without_calendar.zip')
    validity_period = ValidityPeriodFinder.select_computer_and_find(file)
    assert validity_period.start_date == date(2016, 10, 4)
    assert validity_period.end_date == date(2016, 12, 24)


def test_calendar_with_not_date():
    file = _get_file_fixture_full_path('validity_period/calendar_invalid_end_date.zip')
    with pytest.raises(InvalidFile) as excinfo:
        ValidityPeriodFinder.select_computer_and_find(file)
    assert str(excinfo.value) == "impossible to parse file calendar.txt, " \
                                 "error time data 'AAAA' does not match format '%Y%m%d' (match)"


def test_calendar_dates_without_exception_type():
    file = _get_file_fixture_full_path('validity_period/calendar_dates_without_exception_type.zip')
    with pytest.raises(InvalidFile) as excinfo:
        ValidityPeriodFinder.select_computer_and_find(file)
    assert str(excinfo.value) == "impossible to parse file calendar_dates.txt, error Usecols do not match names."


def test_calendar_dates_without_dates():
    file = _get_file_fixture_full_path('validity_period/calendar_dates_without_dates.zip')
    with pytest.raises(InvalidFile) as excinfo:
        ValidityPeriodFinder.select_computer_and_find(file)
    assert str(excinfo.value) == "impossible to parse file calendar_dates.txt, error Usecols do not match names."


def test_add_dates():
    """
        calendar.txt   :     20170102                    20170131
                                *--------------------------*
        calendar_dates :
                add dates : 20170101 and 20170215

                production date : 20170101 to 20170215
    """

    file = _get_file_fixture_full_path('validity_period/add_dates.zip')
    validity_period = ValidityPeriodFinder.select_computer_and_find(file)
    assert validity_period.start_date == date(2017, 1, 1)
    assert validity_period.end_date == date(2017, 2, 15)


def test_remove_dates():
    """
        calendar.txt   :     20170102                    20170131
                                *--------------------------*
        calendar_dates :
                remove dates : 20170102, 20170103, 20170115 and 20170131

                production date : 20170104 to 20170130
    """

    file = _get_file_fixture_full_path('validity_period/remove_dates.zip')
    validity_period = ValidityPeriodFinder.select_computer_and_find(file)
    assert validity_period.start_date == date(2017, 1, 4)
    assert validity_period.end_date == date(2017, 1, 30)


def test_calendar_with_many_periods():
    file = _get_file_fixture_full_path('validity_period/calendar_many_periods.zip')
    validity_period = ValidityPeriodFinder.select_computer_and_find(file)
    assert validity_period.start_date == date(2017, 1, 2)
    assert validity_period.end_date == date(2017, 7, 20)


def test_calendar_dates_with_headers_only():
    file = _get_file_fixture_full_path('validity_period/calendar_dates_with_headers_only.zip')
    validity_period = ValidityPeriodFinder.select_computer_and_find(file)
    assert validity_period.start_date == date(2017, 1, 2)
    assert validity_period.end_date == date(2017, 1, 20)


def test_calendar_with_headers_only():
    file = _get_file_fixture_full_path('validity_period/calendar_with_headers_only.zip')
    with pytest.raises(InvalidFile) as excinfo:
        ValidityPeriodFinder.select_computer_and_find(file)
    assert str(excinfo.value).startswith('impossible to find validity period')


def test_calendar_dates_with_empty_line():
    file = _get_file_fixture_full_path('validity_period/calendar_dates_with_empty_line.zip')
    validity_period = ValidityPeriodFinder.select_computer_and_find(file)
    assert validity_period.start_date == date(2017, 1, 2)
    assert validity_period.end_date == date(2017, 1, 20)


def test_calendar_with_empty_line_and_remove_date_only():
    file = _get_file_fixture_full_path('validity_period/calendar_with_empty_line_remove_dates_only.zip')
    with pytest.raises(InvalidFile) as excinfo:
        ValidityPeriodFinder.select_computer_and_find(file)
    assert str(excinfo.value).startswith('impossible to find validity period')


def test_calendar_with_empty_line_and_add_date_only():
    file = _get_file_fixture_full_path('validity_period/calendar_with_empty_line_add_dates_only.zip')
    validity_period = ValidityPeriodFinder.select_computer_and_find(file)
    assert validity_period.start_date == date(2017, 1, 2)
    assert validity_period.end_date == date(2017, 1, 31)


def test_gtfs_feed_info_with_2_rows():
    file = _get_file_fixture_full_path('validity_period/gtfs_feed_info_with_2_rows.zip')
    with pytest.raises(InvalidFile) as excinfo:
        ValidityPeriodFinder.select_computer_and_find(file)
    assert str(excinfo.value) == 'impossible to find validity period, invalid file feed_info.txt'


@pytest.mark.parametrize(
    "validity_periods,expected_message", [
        ([ValidityPeriod(date(2015, 1, 20), date(2015, 7, 14))],
         "calculating validity period union on past periods (end_date: 14/07/2015 < now: 15/01/2017)"),
        ([ValidityPeriod(date(2015, 1, 20), date(2015, 7, 14)),
          ValidityPeriod(date(2016, 2, 20), date(2016, 11, 14))],
         "calculating validity period union on past periods (end_date: 14/11/2016 < now: 15/01/2017)"),
        ([ValidityPeriod(date(2016, 12, 10), date(2017, 1, 1)),
          ValidityPeriod(date(2015, 1, 20), date(2015, 7, 14)),
          ValidityPeriod(date(2016, 2, 20), date(2016, 11, 14))],
         "calculating validity period union on past periods (end_date: 01/01/2017 < now: 15/01/2017)")
    ])
def test_compute_for_data_format_union_past(validity_periods, expected_message):
    with pytest.raises(ValidityPeriodException) as excinfo:
        ValidityPeriod.union(validity_periods).to_valid(current_date=date(year=2017, month=1, day=15))
    assert str(excinfo.value) == expected_message


def test_compute_for_data_format_union_empty():
    with pytest.raises(ValidityPeriodException) as excinfo:
        ValidityPeriod.union([])
    assert str(excinfo.value) == 'empty validity period list given to calculate union'


@pytest.mark.parametrize(
    "validity_period_dates,expected_period", [
        # one contributor
        ([(date(2017, 1, 20), date(2017, 7, 14))],
         ValidityPeriod(date(2017, 1, 20), date(2017, 7, 14))),
        # one contributor more than one year now inside
        ([(date(2017, 1, 1), date(2018, 3, 15))],
         ValidityPeriod(date(2017, 1, 8), date(2018, 1, 7))),
        # one contributor more than one year now outside
        ([(date(2018, 1, 15), date(2020, 1, 15))],
         ValidityPeriod(date(2018, 1, 15), date(2019, 1, 14))),
        # cross
        ([(date(2017, 1, 1), date(2017, 7, 1)), (date(2017, 3, 1), date(2017, 9, 1))],
         ValidityPeriod(date(2017, 1, 1), date(2017, 9, 1))),
        # next
        ([(date(2017, 1, 15), date(2017, 3, 1)), (date(2017, 7, 1), date(2017, 12, 11))],
         ValidityPeriod(date(2017, 1, 15), date(2017, 12, 11))),
        # before
        ([(date(2017, 7, 1), date(2017, 9, 1)), (date(2017, 1, 9), date(2017, 3, 1))],
         ValidityPeriod(date(2017, 1, 9), date(2017, 9, 1))),
        # included
        ([(date(2017, 1, 1), date(2017, 12, 1)), (date(2017, 3, 9), date(2017, 3, 6))],
         ValidityPeriod(date(2017, 1, 1), date(2017, 12, 1))),
        # more than one year now inside
        ([(date(2017, 1, 1), date(2017, 7, 1)), (date(2018, 3, 1), date(2018, 9, 1))],
         ValidityPeriod(date(2017, 1, 8), date(2018, 1, 7))),
        # more than one year now outside
        ([(date(2018, 1, 1), date(2018, 7, 1)), (date(2019, 3, 1), date(2019, 9, 1))],
         ValidityPeriod(date(2018, 1, 1), date(2018, 12, 31))),
        # 3 contrib
        ([(date(2018, 1, 1), date(2018, 4, 1)), (date(2018, 10, 1), date(2018, 12, 11)),
          (date(2018, 8, 11), date(2018, 10, 13))],
         ValidityPeriod(date(2018, 1, 1), date(2018, 12, 11))),
    ])
def test_compute_for_data_format_union_valid(validity_period_dates, expected_period):
    validity_period_containers = []
    for contrib_begin_date, contrib_end_date in validity_period_dates:
        validity_period_containers.append(ValidityPeriod(contrib_begin_date, contrib_end_date))
    result_period = ValidityPeriod.union(validity_period_containers).to_valid(
        current_date=date(year=2017, month=1, day=15))
    assert expected_period.start_date == result_period.start_date
    assert expected_period.end_date == result_period.end_date


def test_titan_data_set():
    file = _get_file_fixture_full_path('validity_period/other_data_formats/titan.zip')
    validity_period = ValidityPeriodFinder.select_computer_and_find(file, DATA_FORMAT_TITAN)
    assert validity_period.start_date == date(2018, 1, 2)
    assert validity_period.end_date == date(2018, 6, 18)


def test_obiti_data_set():
    file = _get_file_fixture_full_path('validity_period/other_data_formats/obiti.zip')
    validity_period = ValidityPeriodFinder.select_computer_and_find(file, DATA_FORMAT_OBITI)
    assert validity_period.start_date == date(2017, 8, 28)
    assert validity_period.end_date == date(2019, 1, 2)


@pytest.mark.parametrize("fixture,message", [
    ('obiti_invalid_regime.zip', 'file zip {file} without validitypattern.csv'),
    ('obiti_invalid_period.zip', 'file zip {file} without periode.csv'),
])
def test_obiti_data_set_invalid(fixture, message):
    file = _get_file_fixture_full_path('validity_period/other_data_formats/{}'.format(fixture))
    with pytest.raises(InvalidFile) as excinfo:
        ValidityPeriodFinder.select_computer_and_find(file, DATA_FORMAT_OBITI)
    assert str(excinfo.value) == message.format(file=file)


def test_neptune_data_set():
    file = _get_file_fixture_full_path('validity_period/other_data_formats/neptune.zip')
    validity_period = ValidityPeriodFinder.select_computer_and_find(file, DATA_FORMAT_NEPTUNE)
    assert validity_period.start_date == date(2017, 12, 21)
    assert validity_period.end_date == date(2018, 2, 27)
