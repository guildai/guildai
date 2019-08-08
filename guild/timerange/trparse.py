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

from datetime import datetime as dt
from datetime import date, time
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

def p_unit_period_today(p):
    "unit_period : TODAY"
    p_unit_period_this_day(p)

def p_unit_period_yesterday(p):
    "unit_period : YESTERDAY"
    #p_unit_period_last_day(p)
    #start = dt.combine(date.today() - delta(days=1), time())
    #end = start + delta(days=1)
    #p[0] = (start, end)
    p[0] = "TODO"

def p_unit_period_this_minute(p):
    "unit_period : THIS MINUTE"
    start = dt.now().replace(second=0, microsecond=0)
    end = start + delta(minutes=1)
    p[0] = (start, end)

def p_unit_period_this_hour(p):
    "unit_period : THIS HOUR"
    start = dt.now().replace(minute=0, second=0, microsecond=0)
    end = start + delta(hours=1)
    p[0] = (start, end)

def p_unit_period_this_day(p):
    "unit_period : THIS DAY"
    start = dt.combine(date.today(), time())
    end = start + delta(days=1)
    p[0] = (start, end)

def p_unit_period_this_week(p):
    "unit_period : THIS WEEK"
    today = date.today()
    start = dt.combine(today - delta(today.weekday()), time())
    end = start + delta(days=7)
    p[0] = (start, end)

def p_unit_period_this_month(p):
    "unit_period : THIS MONTH"
    start = dt.combine(date.today().replace(day=1), time())
    end = end_of_month(start)
    p[0] = (start, end)

def end_of_month(ref):
    # Credit: https://stackoverflow.com/a/13565185
    next_month = ref.replace(day=28) + delta(days=4)
    return next_month - delta(days=next_month.day)

def p_unit_period_this_year(p):
    "unit_period : THIS YEAR"
    start = dt.combine(date.today().replace(month=1, day=1), time())
    end = start.replace(month=12, day=31)
    p[0] = (start, end)

def p_operator_period_before(p):
    "operator_period : BEFORE unit_period"
    p[0] = (None, p[2][0])

def p_operator_period_after(p):
    "operator_period : AFTER unit_period"
    p[0] = (p[2][0], None)

def p_error(t):
    if t is None:
        raise ParseError("query string cannot be empty")
    raise ParseError(
        "unexpected '%s' at pos %i"
        % (t.value, t.lineno, t.lexpos))

class parser(object):

    def __init__(self):
        self._l = trlex.lexer()
        self._p = _yacc.yacc(debug=False, write_tables=False)

    def parse(self, s):
        return self._p.parse(s, self._l)
