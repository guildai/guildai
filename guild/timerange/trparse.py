# Copyright 2017-2020 TensorHub, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
spec : unit-range
     | operator-range
     | last-unit
     | explicit-range

unit-range : TODAY
           | YESTERDAY
           | THIS unit
           | NUMBER unit AGO

unit : MINUTE | HOUR | DAY | WEEK | MONTH | YEAR

operator-range : operator range

operator : BEFORE | AFTER

datetime : date | time | date time

date : SHORTDATE | MEDIUMDATE | LONGDATE

time : SHORTTIME | LONGTIME

last-unit : LAST delta-unit
          | LAST NUMBER delta-unit

delta-unit : MINUTE | HOUR | DAY

explicit-range : BETWEEN range AND range

range : unit-range | operator-range | datetime
"""

from __future__ import absolute_import
from __future__ import division

from datetime import datetime, date, time, timedelta

from guild import _yacc

from . import trlex


class ParseError(ValueError):
    pass


tokens = trlex.tokens


def p_spec(p):
    """spec : unit_range
    | operator_range
    | last_unit
    | explicit_range
    | explicit_datetime
    """
    p[0] = p[1]


###################################################################
# Date / time
###################################################################


def p_datetime_date(p):
    "datetime : date"
    date = p[1]
    p[0] = lambda ref: _datetime_for_date(date(ref))


def _datetime_for_date(d):
    return datetime_for_date(d.year, d.month, d.day)


def p_datetime_time(p):
    "datetime : time"
    time = p[1]
    p[0] = lambda ref: _datetime(ref.date(), time)


def p_datetime_datetime(p):
    "datetime : date time"
    date = p[1]
    time = p[2]
    p[0] = lambda ref: _datetime(date(ref), time)


def _datetime(d, t):
    args = (d.year, d.month, d.day, t.hour, t.minute, t.second)
    if isinstance(t, time_for_longtime):
        return datetime_for_longtime(*args)
    return datetime(*args)


def p_date_short(p):
    "date : SHORTDATE"
    short = p[1]
    p[0] = lambda ref: _date_for_short(short, ref)


def _date_for_short(short, ref):
    month, day = short
    return date(ref.year, month, day)


def p_date_medium(p):
    "date : MEDIUMDATE"
    medium = p[1]
    p[0] = lambda ref: _date_for_medium(medium, ref)


def _date_for_medium(medium, ref):
    year, month, day = medium
    assert year >= 0 and year <= 100, year
    ref_c = ref.year // 100 * 100
    return date(ref_c + year, month, day)


def p_date_long(p):
    "date : LONGDATE"
    year, month, day = p[1]
    p[0] = lambda _ref: date(year, month, day)


def p_time_shorttime(p):
    "time : SHORTTIME"
    hour, minute = p[1]
    p[0] = time(hour, minute)


def p_time_longtime(p):
    "time : LONGTIME"
    hour, minute, second = p[1]
    p[0] = time_for_longtime(hour, minute, second)


###################################################################
# Minute ranges
###################################################################


def p_unit_range_this_minute(p):
    "unit_range : THIS MINUTE"
    p[0] = _minute_range


def p_unit_range_minute_ago(p):
    "unit_range : NUMBER MINUTE AGO"
    shift = p[1]
    p[0] = lambda ref: _minute_range(ref, -shift)


def _minute_range(ref, shift=0):
    start = _reset_minute(ref)
    end = start + timedelta(minutes=1)
    return _shift(start, end, minutes=shift)


def _reset_minute(ref):
    return ref.replace(second=0, microsecond=0)


###################################################################
# Hour ranges
###################################################################


def p_unit_range_this_hour(p):
    "unit_range : THIS HOUR"
    p[0] = _hour_range


def p_unit_range_hour_ago(p):
    "unit_range : NUMBER HOUR AGO"
    shift = p[1]
    p[0] = lambda ref: _hour_range(ref, -shift)


def _hour_range(ref, shift=0):
    start = _reset_hour(ref)
    end = start + timedelta(hours=1)
    return _shift(start, end, hours=shift)


def _reset_hour(ref):
    return ref.replace(minute=0, second=0, microsecond=0)


###################################################################
# Day ranges
###################################################################


def p_unit_range_this_day(p):
    "unit_range : THIS DAY"
    p[0] = _day_range


def p_unit_range_today(p):
    "unit_range : TODAY"
    p[0] = _day_range


def p_unit_range_day_ago(p):
    "unit_range : NUMBER DAY AGO"
    shift = p[1]
    p[0] = lambda ref: _day_range(ref, -shift)


def p_unit_range_yesterday(p):
    "unit_range : YESTERDAY"
    p[0] = lambda ref: _day_range(ref, -1)


def _day_range(ref, shift=0):
    start = ref.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    return _shift(start, end, days=shift)


###################################################################
# Week ranges
###################################################################


def p_unit_range_this_week(p):
    "unit_range : THIS WEEK"
    p[0] = _week_range


def p_unit_range_week_ago(p):
    "unit_range : NUMBER WEEK AGO"
    shift = p[1]
    p[0] = lambda ref: _week_range(ref, -shift)


def _week_range(ref, shift=0):
    ref_day = ref.replace(hour=0, minute=0, second=0, microsecond=0)
    start = ref_day - timedelta(days=ref_day.weekday())
    shifted_start = start + timedelta(days=shift * 7)
    shifted_end = shifted_start + timedelta(days=7)
    return shifted_start, shifted_end


###################################################################
# Month ranges
###################################################################


def p_unit_range_this_month(p):
    "unit_range : THIS MONTH"
    p[0] = _month_range


def p_unit_range_month_ago(p):
    "unit_range : NUMBER MONTH AGO"
    shift = p[1]
    p[0] = lambda ref: _month_range(ref, -shift)


def _month_range(ref, shift=0):
    assert shift <= 0, ("shifting forward not supported", shift)
    start = ref.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    shifted_start = _shift_months_back(start, -shift)
    shifted_end = _end_of_month(shifted_start)
    return shifted_start, shifted_end


def _shift_months_back(date, shift):
    assert date.day == 1, date
    for _ in range(shift):
        date = (date - timedelta(days=1)).replace(day=1)
    return date


def _end_of_month(ref):
    next_month = ref.replace(day=28) + timedelta(days=4)
    return next_month - timedelta(days=next_month.day)


###################################################################
# Year ranges
###################################################################


def p_unit_range_this_year(p):
    "unit_range : THIS YEAR"
    p[0] = _year_range


def p_unit_range_year_ago(p):
    "unit_range : NUMBER YEAR AGO"
    shift = p[1]
    p[0] = lambda ref: _year_range(ref, -shift)


def _year_range(ref, shift=0):
    start = ref.replace(
        year=ref.year + shift, month=1, day=1, hour=0, minute=0, second=0, microsecond=0
    )
    end = start.replace(year=start.year + 1)
    return start, end


###################################################################
# Operator ranges
###################################################################


def p_operator_range_before_unit_range(p):
    "operator_range : BEFORE unit_range"
    unit_range = p[2]
    p[0] = lambda ref: (None, unit_range(ref)[0])


def p_operator_range_before_datetime(p):
    "operator_range : BEFORE datetime"
    end = p[2]
    p[0] = lambda ref: (None, end(ref))


def p_operator_range_after_unit_range(p):
    "operator_range : AFTER unit_range"
    unit_range = p[2]
    p[0] = lambda ref: (unit_range(ref)[1], None)


def p_operator_range_after_datetime(p):
    "operator_range : AFTER datetime"
    start = p[2]
    p[0] = lambda ref: (start(ref), None)


###################################################################
# Last unit
###################################################################


def p_last_unit(p):
    "last_unit : LAST delta_unit"
    delta = _unit_delta(1, p[2])
    p[0] = lambda ref: (ref - delta, None)


def p_last_n_unit(p):
    "last_unit : LAST NUMBER delta_unit"
    delta = _unit_delta(p[2], p[3])
    p[0] = lambda ref: (ref - delta, None)


def p_delta_unit(p):
    """delta_unit : MINUTE
    | HOUR
    | DAY"""
    p[0] = p[1].lower()[:1]


def _unit_delta(n, unit):
    unit = unit.lower()
    if unit == "m":
        return timedelta(minutes=n)
    elif unit == "h":
        return timedelta(hours=n)
    elif unit == "d":
        return timedelta(days=n)
    else:
        assert False, unit


###################################################################
# Explicit range
###################################################################


def p_explicit_range(p):
    "explicit_range : BETWEEN range AND range"
    p1 = p[2]
    p2 = p[4]
    p[0] = lambda ref: _between(p1, p2, ref)


def _between(p1, p2, ref):
    start1, end1 = p1(ref)
    start2, end2 = p2(ref)
    if start1 < start2:
        return start1, end2
    else:
        return start2, end1


def p_range_range(p):
    """range : unit_range
    | operator_range"""
    p[0] = p[1]


def p_range_datetime(p):
    "range : datetime"
    datetime = p[1]
    p[0] = lambda ref: (datetime(ref), datetime(ref))


###################################################################
# Explicit date/time
###################################################################


def p_explicit_datetime(p):
    "explicit_datetime : datetime"
    datetime = p[1]
    p[0] = lambda ref: _datetime_range(datetime(ref))


def _datetime_range(dt):
    if isinstance(dt, datetime_for_date):
        return _day_range(dt)
    elif isinstance(dt, datetime_for_longtime):
        return _second_range(dt)
    else:
        return _minute_range(dt)


def _second_range(ref):
    start = _reset_second(ref)
    end = start + timedelta(seconds=1)
    return start, end


def _reset_second(dt):
    return dt.replace(microsecond=0)


###################################################################
# Remaining API
###################################################################


def p_error(t):
    if t is None:
        raise ParseError("spec cannot be empty")
    raise ParseError("unexpected '%s' at pos %i" % (t.value, t.lexpos))


def _shift(start, end, **delta_kw):
    shift = timedelta(**delta_kw)
    return start + shift, end + shift


class datetime_for_date(datetime):
    """Denotes a datetime object created from a date-only user spec.

    Date only spec has a different meaning in some cases as it implies
    a day interval rather than a minute or second interval.
    """


class time_for_longtime(time):
    """Denotes a time object created with a long time user spec.

    Used when constructing a `datetime_for_longtime` object.
    """


class datetime_for_longtime(datetime):
    """Denotes a datetime object created with a long time user spec.

    A long time spec includes seconds, which implies in some cases
    that an interval should be in seconds rather than minutes.
    """


class parser(object):
    def __init__(self):
        self._l = trlex.lexer()
        self._p = _yacc.yacc(debug=False, write_tables=False)

    def parse(self, s):
        return self._p.parse(s, self._l)
