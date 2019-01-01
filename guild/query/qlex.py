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

from guild import _lex

reserved = (
    "SELECT",
    "MIN", "MAX", "FIRST", "LAST", "AVG", "TOTAL", "COUNT",
    "STEP", "AS"
)

tokens = reserved + (
    "SCALAR_PREFIX", "ATTR_PREFIX", "FLAG_PREFIX",
    "COMMA", "DOT", "EQUALS",
    "UNQUOTED",
    "QUOTED",
)

t_ignore = " \t"

def t_SCALAR_PREFIX(t):
    r"scalar:"
    return t

def t_ATTR_PREFIX(t):
    r"attr:"
    return t

def t_FLAG_PREFIX(t):
    r"flag:"
    return t

def t_DOT(t):
    r"\."
    return t

def t_COMMA(t):
    r","
    return t

def t_EQUALS(t):
    r"="
    return t

reserved_map = {name.lower(): name for name in reserved}

def t_UNQUOTED(t):
    r"[^'\",\n][^ ,\n]*"
    t.type = reserved_map.get(t.value, "UNQUOTED")
    return t

t_QUOTED = r"(\"([^\\\n]|(\\.))*?\")|(\'([^\\\n]|(\\.))*?\')"

def t_NEWLINE(t):
    r"\n+"
    t.lexer.lineno += len(t.value)

def t_error(t):
    assert False, t

def lexer():
    import sys
    return _lex.lex(module=sys.modules[__name__])
