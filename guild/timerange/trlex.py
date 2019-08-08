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

from __future__ import absolute_import
from __future__ import division

import datetime
import re
import sys

from guild import _lex

reserved = (
    "TODAY",
    "YESTERDAY",
    "THIS",
    "LAST",
    "AGO",
    "BEFORE",
    "AFTER",
    "BETWEEN",
    "AND",
)

tokens = reserved + (
    "LONGDATE",
    "SHORTDATE",
    "MEDIUMDATE",
    "SHORTDATE",
    "DATETIME",
    "TIME",
    "NUMBER",
    "RESERVED",
    "MINUTE",
    "HOUR",
    "DAY",
    "WEEK",
    "MONTH",
    "YEAR",
)

t_ignore = " \t"

reserved_map = {name.lower(): name for name in reserved}

def t_LONGDATE(t):
    r"[0-9]{4}-[0-9]{1,2}-[0-9]{1,2}"
    d = _parse_date(t.value, "%Y-%m-%d")
    t.value = (d.year, d.month, d.day)
    t.type = "DATETIME"
    return t

def _parse_date(s, fmt):
    try:
        return datetime.datetime.strptime(s, fmt)
    except ValueError:
        raise ValueError("invalid date '%s'" % s)

def t_MEDIUMDATE(t):
    r"[0-9]{2}-[0-9]{1,2}-[0-9]{1,2}"
    d = _parse_date(t.value, "%y-%m-%d")
    t.value = (d.year, d.month, d.day)
    t.type = "DATETIME"
    return t

def t_SHORTDATE(t):
    r"[0-9]{1,2}-[0-9]{1,2}"
    d = _parse_date(t.value, "%m-%d")
    t.value = (datetime.datetime.today().year, d.month, d.day)
    t.type = "DATETIME"
    return t

def t_TIME(t):
    r"[0-9]+:[0-9]+"
    try:
        d = datetime.datetime.strptime(t.value, "%H:%M")
    except ValueError:
        raise ValueError("invalid time '%s'" % t.value)
    else:
        t.value = (d.hour, d.minute)
        return t

def t_MINUTE(t):
    r"minutes?"
    return t

def t_HOUR(t):
    r"hours?"
    return t

def t_DAY(t):
    r"days?"
    return t

def t_WEEK(t):
    r"weeks?"
    return t

def t_MONTH(t):
    r"months?"
    return t

def t_YEAR(t):
    r"years?"
    return t

def t_NUMBER(t):
    r"[0-9]+"
    t.value = int(t.value)
    return t

def t_RESERVED(t):
    r"[a-zA-Z]+"
    try:
        t.type = reserved_map[t.value.lower()]
    except KeyError:
        raise SyntaxError(
            "unexpected '%s' at position %i"
            % (t.value, t.lexpos))
    else:
        return t

def t_error(t):
    raise SyntaxError(
        "unexpected '%s' at position %s"
        % (t.value, t.lexpos))
    assert False, t

def lexer():
    return _lex.lex(
        module=sys.modules[__name__],
        reflags=re.IGNORECASE|re.VERBOSE)
