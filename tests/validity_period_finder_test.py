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
from freezegun import freeze_time

from tartare.core.context import ContributorContext
from tartare.core.models import ValidityPeriod, Contributor
from tartare.exceptions import InvalidFile, ValidityPeriodException
from tartare.validity_period_finder import ValidityPeriodFinder
from tests.utils import _get_file_fixture_full_path


def test_zip_file_only_calendar():
    finder = ValidityPeriodFinder()
    file = _get_file_fixture_full_path('gtfs/some_archive.zip')
    start_date, end_date = finder.get_validity_period(file)
    assert start_date == date(2015, 3, 25)
    assert end_date == date(2015, 8, 26)


def test_zip_file_only_feed_info():
    finder = ValidityPeriodFinder()
    file = _get_file_fixture_full_path('validity_period/gtfs_with_feed_info.zip')
    start_date, end_date = finder.get_validity_period(file)
    assert start_date == date(2016, 4, 11)
    assert end_date == date(2016, 12, 31)


def test_zip_file_only_feed_info_invalid():
    finder = ValidityPeriodFinder()
    file = _get_file_fixture_full_path('validity_period/gtfs_with_feed_info_invalid.zip')
    with pytest.raises(InvalidFile) as excinfo:
        finder.get_validity_period(file)
    assert str(excinfo.value) == "Header not found in file feed_info.txt, Error : 'feed_start_date' is not in list"


def test_zip_file_only_feed_info_missing_dates():
    finder = ValidityPeriodFinder()
    file = _get_file_fixture_full_path('validity_period/gtfs_with_feed_info_missing_dates.zip')
    start_date, end_date = finder.get_validity_period(file)
    assert start_date == date(2016, 10, 4), print(start_date)
    assert end_date == date(2016, 12, 24), print(end_date)


def test_zip_file_invalid():
    finder = ValidityPeriodFinder()
    file = _get_file_fixture_full_path('gtfs/bob.zip')
    with pytest.raises(InvalidFile) as excinfo:
        finder.get_validity_period(file)
    assert str(excinfo.value) == "{} is not a zip file or not exist.".format(file)


def test_not_zipfile():
    finder = ValidityPeriodFinder()
    file = _get_file_fixture_full_path('ntfs/calendar.txt')
    with pytest.raises(InvalidFile) as excinfo:
        finder.get_validity_period(file)
    assert str(excinfo.value) == "{} is not a zip file or not exist.".format(file)


def test_calendar_without_end_date_column():
    finder = ValidityPeriodFinder()
    file = _get_file_fixture_full_path('validity_period/calendar_without_end_date.zip')
    with pytest.raises(InvalidFile) as excinfo:
        finder.get_validity_period(file)
    assert str(excinfo.value) == "Header not found in file calendar.txt, Error : 'end_date' is not in list"


def test_calendar_without_start_date_column():
    finder = ValidityPeriodFinder()
    file = _get_file_fixture_full_path('validity_period/calendar_without_start_date.zip')
    with pytest.raises(InvalidFile) as excinfo:
        finder.get_validity_period(file)
    assert str(excinfo.value) == "Header not found in file calendar.txt, Error : 'start_date' is not in list"


def test_gtfs_without_calendar():
    finder = ValidityPeriodFinder()
    file = _get_file_fixture_full_path('validity_period/gtfs_without_calendar.zip')
    start_date, end_date = finder.get_validity_period(file)
    assert start_date == date(2016, 10, 4)
    assert end_date == date(2016, 12, 24)


def test_calendar_with_not_date():
    finder = ValidityPeriodFinder()
    file = _get_file_fixture_full_path('validity_period/calendar_invalid_end_date.zip')
    with pytest.raises(InvalidFile) as excinfo:
        finder.get_validity_period(file)
    assert str(excinfo.value) == "Impossible to parse file calendar.txt, " \
                                 "Error time data 'AAAA' does not match format '%Y%m%d' (match)"


def test_calendar_dates_without_exception_type():
    finder = ValidityPeriodFinder()
    file = _get_file_fixture_full_path('validity_period/calendar_dates_without_exception_type.zip')
    with pytest.raises(InvalidFile) as excinfo:
        finder.get_validity_period(file)
    assert str(excinfo.value) == "Header not found in file calendar_dates.txt, Error : 'exception_type' is not in list"


def test_calendar_dates_without_dates():
    finder = ValidityPeriodFinder()
    file = _get_file_fixture_full_path('validity_period/calendar_dates_without_dates.zip')
    with pytest.raises(InvalidFile) as excinfo:
        finder.get_validity_period(file)
    assert str(excinfo.value) == "Header not found in file calendar_dates.txt, Error : 'date' is not in list"


def test_add_dates():
    """
        calendar.txt   :     20170102                    20170131
                                *--------------------------*
        calendar_dates :
                add dates : 20170101 and 20170215

                production date : 20170101 to 20170215
    """
    finder = ValidityPeriodFinder()
    file = _get_file_fixture_full_path('validity_period/add_dates.zip')
    start_date, end_date = finder.get_validity_period(file)
    assert start_date == date(2017, 1, 1)
    assert end_date == date(2017, 2, 15)


def test_remove_dates():
    """
        calendar.txt   :     20170102                    20170131
                                *--------------------------*
        calendar_dates :
                remove dates : 20170102, 20170103, 20170115 and 20170131

                production date : 20170104 to 20170130
    """
    finder = ValidityPeriodFinder()
    file = _get_file_fixture_full_path('validity_period/remove_dates.zip')
    start_date, end_date = finder.get_validity_period(file)
    assert start_date == date(2017, 1, 4)
    assert end_date == date(2017, 1, 30)


def test_calendar_with_many_periods():
    finder = ValidityPeriodFinder()
    file = _get_file_fixture_full_path('validity_period/calendar_many_periods.zip')
    start_date, end_date = finder.get_validity_period(file)
    assert start_date == date(2017, 1, 2)
    assert end_date == date(2017, 7, 20)


def test_calendar_dates_with_headers_only():
    finder = ValidityPeriodFinder()
    file = _get_file_fixture_full_path('validity_period/calendar_dates_with_headers_only.zip')
    start_date, end_date = finder.get_validity_period(file)
    assert start_date == date(2017, 1, 2)
    assert end_date == date(2017, 1, 20)


def test_calendar_with_headers_only():
    finder = ValidityPeriodFinder()
    file = _get_file_fixture_full_path('validity_period/calendar_with_headers_only.zip')
    with pytest.raises(InvalidFile) as excinfo:
        finder.get_validity_period(file)
    assert str(excinfo.value).startswith('Impossible to find validity period')


def test_calendar_dates_with_empty_line():
    finder = ValidityPeriodFinder()
    file = _get_file_fixture_full_path('validity_period/calendar_dates_with_empty_line.zip')
    start_date, end_date = finder.get_validity_period(file)
    assert start_date == date(2017, 1, 2)
    assert end_date == date(2017, 1, 20)


def test_calendar_with_empty_line_and_remove_date_only():
    finder = ValidityPeriodFinder()
    file = _get_file_fixture_full_path('validity_period/calendar_with_empty_line_remove_dates_only.zip')
    with pytest.raises(InvalidFile) as excinfo:
        finder.get_validity_period(file)
    assert str(excinfo.value).startswith('Impossible to find validity period')


def test_calendar_with_empty_line_and_add_date_only():
    finder = ValidityPeriodFinder()
    file = _get_file_fixture_full_path('validity_period/calendar_with_empty_line_add_dates_only.zip')
    start_date, end_date = finder.get_validity_period(file)
    assert start_date == date(2017, 1, 2)
    assert end_date == date(2017, 1, 31)


def test_gtfs_feed_info_with_2_rows():
    finder = ValidityPeriodFinder()
    file = _get_file_fixture_full_path('validity_period/gtfs_feed_info_with_2_rows.zip')
    with pytest.raises(InvalidFile) as excinfo:
        finder.get_validity_period(file)
    assert str(excinfo.value) == 'Impossible to find validity period, invalid feed_info.txt file.'

dummy_contrib = Contributor('cid', 'cname', 'pref')


@freeze_time("2017-01-15")
@pytest.mark.parametrize(
    "validity_periods,expected_message", [
        ([ContributorContext(dummy_contrib, validity_period=ValidityPeriod(date(2015, 1, 20), date(2015, 7, 14)))],
         "calculating validity period union on past periods (end_date: 14/07/2015 < now: 15/01/2017)"),
        ([ContributorContext(dummy_contrib, validity_period=ValidityPeriod(date(2015, 1, 20), date(2015, 7, 14))),
          ContributorContext(dummy_contrib, validity_period=ValidityPeriod(date(2016, 2, 20), date(2016, 11, 14)))],
         "calculating validity period union on past periods (end_date: 14/11/2016 < now: 15/01/2017)"),
        ([ContributorContext(dummy_contrib, validity_period=ValidityPeriod(date(2016, 12, 10), date(2017, 1, 1))),
          ContributorContext(dummy_contrib, validity_period=ValidityPeriod(date(2015, 1, 20), date(2015, 7, 14))),
          ContributorContext(dummy_contrib, validity_period=ValidityPeriod(date(2016, 2, 20), date(2016, 11, 14)))],
         "calculating validity period union on past periods (end_date: 01/01/2017 < now: 15/01/2017)")
    ])
def test_get_validity_period_union_past(validity_periods, expected_message):
    with pytest.raises(ValidityPeriodException) as excinfo:
        ValidityPeriodFinder.get_validity_period_union(validity_periods)
    assert str(excinfo.value) == expected_message


def test_get_validity_period_union_empty():
    with pytest.raises(ValidityPeriodException) as excinfo:
        ValidityPeriodFinder.get_validity_period_union([])
    assert str(excinfo.value) == 'empty validity period list given to calculate union'

@freeze_time("2017-01-15")
@pytest.mark.parametrize(
    "validity_period_dates,expected_period", [
        # one contributor
        ([(date(2017, 1, 20), date(2017, 7, 14))],
         ValidityPeriod(date(2017, 1, 20), date(2017, 7, 14))),
        # one contributor more than one year now inside
        ([(date(2017, 1, 1), date(2018, 3, 15))],
         ValidityPeriod(date(2017, 1, 15), date(2018, 1, 14))),
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
         ValidityPeriod(date(2017, 1, 15), date(2018, 1, 14))),
        # more than one year now outside
        ([(date(2018, 1, 1), date(2018, 7, 1)), (date(2019, 3, 1), date(2019, 9, 1))],
         ValidityPeriod(date(2018, 1, 1), date(2018, 12, 31))),
        # 3 contrib
        ([(date(2018, 1, 1), date(2018, 4, 1)), (date(2018, 10, 1), date(2018, 12, 11)),
          (date(2018, 8, 11), date(2018, 10, 13))],
         ValidityPeriod(date(2018, 1, 1), date(2018, 12, 11))),
    ])
def test_get_validity_period_union_valid(validity_period_dates, expected_period):
    validity_period_containers = []
    for contrib_begin_date, contrib_end_date in validity_period_dates:
        validity_period_containers.append(ContributorContext(contributor=dummy_contrib,
                                                             validity_period=ValidityPeriod(contrib_begin_date,
                                                                                            contrib_end_date)))
    result_period = ValidityPeriodFinder.get_validity_period_union(validity_period_containers)
    assert expected_period.start_date == result_period.start_date
    assert expected_period.end_date == result_period.end_date
