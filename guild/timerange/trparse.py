# Copyright 2017-2019 TensorHub, Inc.
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
spec : unit-period | operator-period | explicit-period

unit-period : TODAY
            | YESTERDAY
            | THIS unit
            | LAST unit
            | NUMBER unit AGO

unit : MINUTE | HOUR | DAY | WEEK | MONTH | YEAR

operator-period : operator period-marker

operator : BEFORE | after

after : AFTER | SINCE

datetime : date
         | TIME
         | date TIME

date : SHORTDATE
     | MEDIUMDATE
     | LONGDATE

explicit-period : BETWEEN period AND period

period : unit-period | operator-period | datetime
"""

from __future__ import absolute_import
from __future__ import division

from datetime import datetime, date, time, timedelta

from guild import _yacc

from . import ParseError
from . import trlex

tokens = trlex.tokens

def p_spec(p):
    """spec : unit_period
            | operator_period
            | explicit_period
    """
    p[0] = p[1]

###################################################################
# Special periods
###################################################################

def p_unit_period_today(p):
    "unit_period : TODAY"
    p_unit_period_this_day(p)

def p_unit_period_yesterday(p):
    "unit_period : YESTERDAY"
    p_unit_period_last_day(p)

###################################################################
# Minute periods
###################################################################

def p_unit_period_this_minute(p):
    "unit_period : THIS MINUTE"
    p[0] = _minute_period

def p_unit_period_last_minute(p):
    "unit_period : LAST MINUTE"
    p[0] = lambda ref: _minute_period(ref, -1)

def p_unit_period_minute_ago(p):
    "unit_period : NUMBER MINUTE AGO"
    shift = p[1]
    p[0] = lambda ref: _minute_period(ref, -shift)

def _minute_period(ref, shift=0):
    start = ref.replace(second=0, microsecond=0)
    end = start + timedelta(minutes=1)
    return _shift(start, end, minutes=shift)

###################################################################
# Hour periods
###################################################################

def p_unit_period_this_hour(p):
    "unit_period : THIS HOUR"
    p[0] = _hour_period

def p_unit_period_last_hour(p):
    "unit_period : LAST HOUR"
    p[0] = lambda ref: _hour_period(ref, -1)

def p_unit_period_hour_ago(p):
    "unit_period : NUMBER HOUR AGO"
    shift = p[1]
    p[0] = lambda ref: _hour_period(ref, -shift)

def _hour_period(ref, shift=0):
    start = ref.replace(minute=0, second=0, microsecond=0)
    end = start + timedelta(hours=1)
    return _shift(start, end, hours=shift)

###################################################################
# Day periods
###################################################################

def p_unit_period_this_day(p):
    "unit_period : THIS DAY"
    p[0] = _day_period

def p_unit_period_last_day(p):
    "unit_period : LAST DAY"
    p[0] = lambda ref: _day_period(ref, -1)

def p_unit_period_day_ago(p):
    "unit_period : NUMBER DAY AGO"
    shift = p[1]
    p[0] = lambda ref: _day_period(ref, -shift)

def _day_period(ref, shift=0):
    start = ref.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    return _shift(start, end, days=shift)

###################################################################
# Week periods
###################################################################

def p_unit_period_this_week(p):
    "unit_period : THIS WEEK"
    p[0] = _week_period

def p_unit_period_last_week(p):
    "unit_period : LAST WEEK"
    p[0] = lambda ref: _week_period(ref, -1)

def p_unit_period_week_ago(p):
    "unit_period : NUMBER WEEK AGO"
    shift = p[1]
    p[0] = lambda ref: _week_period(ref, -shift)

def _week_period(ref, shift=0):
    ref_day = ref.replace(hour=0, minute=0, second=0, microsecond=0)
    start = ref_day - timedelta(days=ref_day.weekday())
    shifted_start = start + timedelta(days=shift * 7)
    shifted_end = shifted_start + timedelta(days=7)
    return shifted_start, shifted_end

###################################################################
# Month periods
###################################################################

def p_unit_period_this_month(p):
    "unit_period : THIS MONTH"
    p[0] = _month_period

def p_unit_period_last_month(p):
    "unit_period : LAST MONTH"
    p[0] = lambda ref: _month_period(ref, -1)

def p_unit_period_month_ago(p):
    "unit_period : NUMBER MONTH AGO"
    shift = p[1]
    p[0] = lambda ref: _month_period(ref, -shift)

def _month_period(ref, shift=0):
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
# Year periods
###################################################################

def p_unit_period_this_year(p):
    "unit_period : THIS YEAR"
    p[0] = _year_period

def p_unit_period_last_year(p):
    "unit_period : LAST YEAR"
    p[0] = lambda ref: _year_period(ref, -1)

def p_unit_period_year_ago(p):
    "unit_period : NUMBER YEAR AGO"
    shift = p[1]
    p[0] = lambda ref: _year_period(ref, -shift)

def _year_period(ref, shift=0):
    start = ref.replace(
        year=ref.year + shift,
        month=1,
        day=1,
        hour=0,
        minute=0,
        second=0,
        microsecond=0)
    end = start.replace(year=start.year + 1)
    return start, end

###################################################################
# Operator periods
###################################################################

def p_operator_period_before_unit_period(p):
    "operator_period : BEFORE unit_period"
    unit_period = p[2]
    p[0] = lambda ref: (None, unit_period(ref)[0])

def p_operator_period_before_datetime(p):
    "operator_period : BEFORE datetime"
    end = p[2]
    p[0] = lambda ref: (None, end(ref))

def p_operator_period_after_unit_period(p):
    "operator_period : after unit_period"
    unit_period = p[2]
    p[0] = lambda ref: (unit_period(ref)[1], None)

def p_operator_period_after_datetime(p):
    "operator_period : after datetime"
    start = p[2]
    p[0] = lambda ref: (start(ref), None)

def p_after(p):
    """after : AFTER
             | SINCE
    """
    p[0] = p[1]

###################################################################
# Explicit period
###################################################################

def p_explicit_period(p):
    "explicit_period : BETWEEN period AND period"
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

def p_period_range(p):
    """period : unit_period
              | operator_period"""
    p[0] = p[1]

def p_period_datetime(p):
    "period : datetime"
    datetime = p[1]
    p[0] = lambda ref: (datetime(ref), datetime(ref))

###################################################################
# Core
###################################################################

def p_datetime_date(p):
    "datetime : date"
    date = p[1]
    p[0] = lambda ref: datetime.combine(date(ref), time())

def p_datetime_time(p):
    "datetime : time"
    time = p[1]
    p[0] = lambda ref: datetime.combine(ref.date(), time)

def p_datetime_datetime(p):
    "datetime : date time"
    date = p[1]
    time = p[2]
    p[0] = lambda ref: datetime.combine(date(ref), time)

def p_date_short(p):
    "date : SHORTDATE"
    short = p[1]
    p[0] = lambda ref: _date_from_short(short, ref)

def _date_from_short(short, ref):
    month, day = short
    return date(ref.year, month, day)

def p_date_medium(p):
    "date : MEDIUMDATE"
    medium = p[1]
    p[0] = lambda ref: _date_from_medium(medium, ref)

def _date_from_medium(medium, ref):
    year, month, day = medium
    assert year >= 0 and year <= 100, year
    ref_c = ref.year // 100 * 100
    return date(ref_c + year, month, day)

def p_date_long(p):
    "date : LONGDATE"
    year, month, day = p[1]
    p[0] = lambda _ref: date(year, month, day)

def p_time(p):
    "time : TIME"
    hour, minute = p[1]
    p[0] = time(hour, minute)

def p_error(t):
    if t is None:
        raise ParseError("spec cannot be empty")
    raise ParseError(
        "unexpected '%s' at pos %i"
        % (t.value, t.lexpos))

def _shift(start, end, **delta_kw):
    shift = timedelta(**delta_kw)
    return start + shift, end + shift

class parser(object):

    def __init__(self):
        self._l = trlex.lexer()
        self._p = _yacc.yacc(debug=False, write_tables=False)

    def parse(self, s):
        return self._p.parse(s, self._l)
