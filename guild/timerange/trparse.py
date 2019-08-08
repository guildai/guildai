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

operator-period: operator period-marker

explicit-period: BETWEEN period-marked AND period-marker

period-marker : unit-period | DATETIME

unit : MINUTE | HOUR | DAY | WEEK | MONTH | YEAR

operator : BEFORE | AFTER
"""

from __future__ import absolute_import
from __future__ import division

from datetime import timedelta as delta

from guild import _yacc

from . import ParseError
from . import trlex

tokens = trlex.tokens

def p_spec(p):
    """spec : unit_period
            | operator_period
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
    end = start + delta(minutes=1)
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
    end = start + delta(hours=1)
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
    end = start + delta(days=1)
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
    start = ref_day - delta(days=ref_day.weekday())
    shifted_start = start + delta(days=shift * 7)
    shifted_end = shifted_start + delta(days=7)
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
        date = (date - delta(days=1)).replace(day=1)
    return date

def _end_of_month(ref):
    next_month = ref.replace(day=28) + delta(days=4)
    return next_month - delta(days=next_month.day)

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

def p_operator_period_before(p):
    "operator_period : BEFORE unit_period"
    p[0] = (None, p[2][0])

def p_operator_period_after(p):
    "operator_period : AFTER unit_period"
    p[0] = (p[2][0], None)

def p_error(t):
    if t is None:
        raise ParseError("spec cannot be empty")
    raise ParseError(
        "unexpected '%s' at pos %i"
        % (t.value, t.lexpos))

def _shift(start, end, **delta_kw):
    shift = delta(**delta_kw)
    return start + shift, end + shift

class parser(object):

    def __init__(self):
        self._l = trlex.lexer()
        self._p = _yacc.yacc(debug=False, write_tables=False)

    def parse(self, s):
        return self._p.parse(s, self._l)
