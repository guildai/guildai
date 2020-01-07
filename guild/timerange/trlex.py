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

from __future__ import absolute_import
from __future__ import division

import re
import sys

from guild import _lex


class LexError(ValueError):
    pass


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
    "SHORTTIME",
    "LONGTIME",
    "NUMBER",
    "MINUTE",
    "HOUR",
    "DAY",
    "WEEK",
    "MONTH",
    "YEAR",
)

t_ignore = " \t\n"

reserved_map = {name.lower(): name for name in reserved}


def t_LONGDATE(t):
    r"([0-9]{4})-([0-9]{1,2})-([0-9]{1,2})"
    t.value = _parse_ints(t)
    return t


def _parse_ints(t):
    groups = [g for g in t.lexer.lexmatch.groups() if g is not None]
    return tuple([int(g) for g in groups[1:]])


def t_MEDIUMDATE(t):
    r"([0-9]{2})-([0-9]{1,2})-([0-9]{1,2})"
    t.value = _parse_ints(t)
    return t


def t_SHORTDATE(t):
    r"([0-9]{1,2})-([0-9]{1,2})"
    t.value = _parse_ints(t)
    return t


def t_LONGTIME(t):
    r"([0-9]{1,2}):([0-9]{2}):([0-9]{2})"
    t.value = _parse_ints(t)
    return t


def t_SHORTTIME(t):
    r"([0-9]{1,2}):([0-9]{2})"
    t.value = _parse_ints(t)
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


def t_HOUR(t):
    r"hours?|hr"
    return t


def t_MINUTE(t):
    r"minutes?|min"
    return t


def t_RESERVED(t):
    r"[a-zA-Z]+"
    try:
        t.type = reserved_map[t.value.lower()]
    except KeyError:
        raise LexError("unexpected '%s' at position %i" % (t.value, t.lexpos))
    else:
        return t


def t_error(t):
    raise LexError("unexpected '%s' at position %s" % (t.value, t.lexpos))


def lexer():
    return _lex.lex(module=sys.modules[__name__], reflags=re.IGNORECASE | re.VERBOSE)
