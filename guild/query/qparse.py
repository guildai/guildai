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

import yaml

from guild import _yacc

from guild.query import Select, Scalar, Attr, Flag
from guild.query import ParseError

from guild.query import qlex

tokens = qlex.tokens

def p_query(p):
    """query : select_stmt"""
    p[0] = p[1]

def p_select_stmt(p):
    """select_stmt : SELECT col_list"""
    p[0] = Select(cols=p[2])

def p_col_list_head(p):
    """col_list : col"""
    p[0] = [p[1]]

def p_col_list(p):
    """col_list : col_list COMMA col"""
    p[0] = p[1] + [p[3]]

def p_col(p):
    """col : scalar_col
           | scalar_step_col
           | attr_col
           | flag_col
    """
    p[0] = p[1]

def p_named_col(p):
    """col : col AS col_name"""
    col = p[1]
    col.named_as = p[3]
    p[0] = col

def p_col_name(p):
    """col_name : term
                | scalar_qualifier
                | STEP
    """
    p[0] = p[1]

def p_implicit_scalar_col(p):
    """scalar_col : scalar_key"""
    p[0] = Scalar(p[1])

def p_explicit_scalar_col(p):
    """scalar_col : SCALAR_PREFIX scalar_key"""
    p[0] = Scalar(p[2])

def p_qualified_implicit_scalar_col(p):
    """scalar_col : scalar_qualifier scalar_key"""
    p[0] = Scalar(p[2], p[1])

def p_scalar_step_col(p):
    """scalar_step_col : scalar_col STEP"""
    scalar = p[1]
    scalar.step = True
    p[0] = scalar

def p_scalar_key(p):
    """scalar_key : term"""
    p[0] = p[1]

def p_scalar_qualifier(p):
    """scalar_qualifier : MIN
                        | MAX
                        | FIRST
                        | LAST
                        | AVG
                        | TOTAL
                        | COUNT
    """
    p[0] = p[1]

def p_dot_attr_col(p):
    "attr_col : DOT attr_name"
    p[0] = Attr(p[2])

def p_attr_col(p):
    "attr_col : ATTR_PREFIX attr_name"
    p[0] = Attr(p[2])

def p_attr_name(p):
    "attr_name : term"
    p[0] = p[1]

def p_equals_flag_col(p):
    "flag_col : EQUALS flag_name"
    p[0] = Flag(p[2])

def p_flag_col(p):
    "flag_col : FLAG_PREFIX flag_name"
    p[0] = Flag(p[2])

def p_flag_name(p):
    "flag_name : UNQUOTED"
    p[0] = p[1]

def p_unquoted_term(p):
    """term : UNQUOTED"""
    p[0] = p[1]

def p_quoted_term(p):
    """term : QUOTED"""
    p[0] = yaml.safe_load(p[1])

def p_error(t):
    if t is None:
        raise ParseError("query string cannot be empty")
    raise ParseError(
        "unexpected token %r, line %i, pos %i"
        % (t.value, t.lineno, t.lexpos))

class parser(object):

    def __init__(self):
        self._l = qlex.lexer()
        self._p = _yacc.yacc(debug=False, write_tables=False)

    def parse(self, s):
        self._l.lineno = 1
        return self._p.parse(s, self._l)
