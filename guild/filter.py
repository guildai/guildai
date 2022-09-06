# Copyright 2017-2022 RStudio, PBC
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

import re

from guild import _lex
from guild import _yacc
from guild import yaml_util


# =================================================================
# Lexer
# =================================================================

reserved = (
    "AND",
    "OR",
    "IN",
    "NOT",
    "TRUE",
    "FALSE",
    "IS",
    "UNDEFINED",
    "CONTAINS",
)

tokens = reserved + (
    "STR_LITERAL",
    "ID",
    "NUMBER",
    "EQ",
    "NEQ",
    "LT",
    "LTE",
    "GT",
    "GTE",
    "LPAREN",
    "RPAREN",
    "LBRACKET",
    "RBRACKET",
    "COMMA",
)

# Use function defs to explicitly order lex matching.


def t_LPAREN(t):
    r"\("
    return t


def t_RPAREN(t):
    r"\)"
    return t


def t_LBRACKET(t):
    r"\["
    return t


def t_RBRACKET(t):
    r"\]"
    return t


def t_NEQ(t):
    r"<>|!="
    return t


def t_EQ(t):
    r"="
    return t


def t_LTE(t):
    r"<="
    return t


def t_LT(t):
    r"<"
    return t


def t_GTE(t):
    r">="
    return t


def t_GT(t):
    r">"
    return t


def t_COMMA(t):
    r","
    return t


reserved_map = {name.lower(): name for name in reserved}


def t_ID(t):
    r"[a-zA-Z][^ ,<>!=\n\(\)\[\]]*"
    t.type = reserved_map.get(t.value.lower(), "ID")
    return t


def t_NUMBER(t):
    r"-?\d+(\.\d+)?(e(\+|-)?(\d+))?"
    t.value = yaml_util.decode_yaml(t.value)
    return t


def t_STR_LITERAL(t):
    r"(\"([^\\\n]|(\\.))*?\")|(\'([^\\\n]|(\\.))*?\')"
    t.value = yaml_util.decode_yaml(t.value)
    return t


t_ignore = ' \t'


def t_newline(t):
    r"\n+"
    t.lexer.lineno += len(t.value)


def t_error(t):
    print(f"Illegal character '{t.value[0]}'")
    t.lexer.skip(1)


def lexer():
    return _lex.lex()


# =================================================================
# Parser
# =================================================================


def p_expression_group(p):
    "expression : LPAREN expression RPAREN"
    p[0] = p[2]


def p_expression_term(p):
    "expression : term"
    p[0] = p[1]


def p_expression_runtest(p):
    "expression : runtest"
    p[0] = p[1]


def p_expression_and(p):
    "expression : expression AND expression"
    p[0] = InfixOp(p[1], p[3], lambda x, y: x and y, "and")


def p_expression_or(p):
    "expression : expression OR expression"
    p[0] = InfixOp(p[1], p[3], lambda x, y: x or y, "or")


def p_expression_not(p):
    "expression : NOT expression"
    p[0] = UnaryOp(p[2], lambda x: not x, "not")


def p_runtest_eq(p):
    "runtest : ID EQ term"
    p[0] = RunTest(p[1], p[3], lambda x, y: x == y, "=")


def p_runtest_lt(p):
    "runtest : ID LT term"
    p[0] = RunTest(p[1], p[3], lambda x, y: x < y, "<")


def p_runtest_lte(p):
    "runtest : ID LTE term"
    p[0] = RunTest(p[1], p[3], lambda x, y: x <= y, "<=")


def p_runtest_gt(p):
    "runtest : ID GT term"
    p[0] = RunTest(p[1], p[3], lambda x, y: x > y, ">")


def p_runtest_gte(p):
    "runtest : ID GTE term"
    p[0] = RunTest(p[1], p[3], lambda x, y: x >= y, ">=")


def p_runtest_neq(p):
    "runtest : ID NEQ term"
    p[0] = RunTest(p[1], p[3], lambda x, y: x != y, "!=")


def p_runtest_is(p):
    "runtest : ID IS term"
    p[0] = RunTest(p[1], p[3], lambda x, y: x is y, " is ")


def p_runtest_is_not(p):
    "runtest : ID IS NOT term"
    p[0] = RunTest(p[1], p[4], lambda x, y: x is not y, " is not ")


def p_runtest_in(p):
    "runtest : ID IN term_list"
    p[0] = In(p[1], p[3])


def p_runtest_not_in(p):
    "runtest : ID NOT IN term_list"
    p[0] = In(p[1], p[4], not_in=True)


def p_runtest_contains(p):
    "runtest : ID CONTAINS term"
    p[0] = Contains(p[1], p[3])


def p_runtest_not_contains(p):
    "runtest : ID NOT CONTAINS term"
    p[0] = Contains(p[1], p[4], not_contains=True)


def p_term_number(p):
    "term : NUMBER"
    p[0] = Term(p[1])


def p_term_str_literal(p):
    "term : STR_LITERAL"
    p[0] = Term(p[1])


def p_term_id(p):
    "term : ID"
    p[0] = Term(p[1])


def p_term_true(p):
    "term : TRUE"
    p[0] = Term(True)


def p_term_false(p):
    "term : FALSE"
    p[0] = Term(False)


def p_term_undefined(p):
    "term : UNDEFINED"
    p[0] = Term(None)


def p_term_list(p):
    "term : term_list"
    p[0] = p[1]


def p_term_list_brackets(p):
    "term_list : LBRACKET comma_sep_terms RBRACKET"
    p[0] = p[2]


def p_comma_sep_terms_head(p):
    "comma_sep_terms : term"
    p[0] = List([p[1]])


def p_comma_sep_terms(p):
    "comma_sep_terms : comma_sep_terms COMMA term"
    p[0] = List(p[1].terms + [p[3]])


def p_error(t):
    if t is None:
        raise SyntaxError("Syntax error at EOF")
    raise SyntaxError(
        f"Syntax error at line {t.lineno}, pos "
        f"{t.lexpos}: unexpected token {t.value!r}"
    )


precedence = (
    ('right', 'AND', 'OR'),
    ('left', 'NOT'),
)

# =================================================================
# Filter implementation
# =================================================================


class Term:
    def __init__(self, val):
        self.val = val

    def __repr__(self):
        return f"<guild.filter.Term {self.val!r}>"

    def __str__(self):
        return repr(self.val)

    def __call__(self, _run):
        return self.val


class RunTest:
    def __init__(self, run_valref, target_expr, cmp, cmp_desc):
        self.run_valref = run_valref
        self.target_expr = target_expr
        self.cmp = cmp
        self.cmp_desc = cmp_desc

    def __repr__(self):
        return f"<guild.filter.RunTest {self}>"

    def __str__(self):
        return f"{self.run_valref}{self.cmp_desc}{self.target_expr}"

    def __call__(self, run):
        run_val = _get_run_val(run, self.run_valref)
        target_val = self.target_expr(run)
        return self.cmp(run_val, target_val)


def _get_run_val(run, valref):
    if valref.startswith("attr:"):
        return run.attrs.get(valref[5:])
    if valref.startswith("flag:"):
        return run.flags.get(valref[5:])
    if valref.startswith("scalar:"):
        return run.scalars.get(valref[7:])
    return run.attrs.get(valref) or run.flags.get(valref) or run.scalars.get(valref)


class In:
    def __init__(self, run_valref, target_expr, not_in=False):
        self.run_valref = run_valref
        self.target_expr = target_expr
        self.not_in = not_in

    def __repr__(self):
        return (
            f"<guild.filter.In {self.run_valref} "
            f"{'not ' if self.not_in else ''}in {self.target_expr}>"
        )

    def __call__(self, run):
        run_val = _get_run_val(run, self.run_valref)
        target_val = self.target_expr(run)
        if not isinstance(target_val, (list, tuple)):
            target_val = [target_val]
        maybe_negate = lambda x: not x if self.not_in else x
        return maybe_negate(run_val in target_val)


class List:
    def __init__(self, terms):
        self.terms = terms

    def __repr__(self):
        return f"<guild.filter.List {self}>"

    def __str__(self):
        return f"[{', '.join(str(t) for t in self.terms)}]"

    def __call__(self, run):
        return [t(run) for t in self.terms]


class InfixOp:
    def __init__(self, expr1, expr2, op, op_desc):
        self.expr1 = expr1
        self.expr2 = expr2
        self.op = op
        self.op_desc = op_desc

    def __repr__(self):
        return f"<guild.filter.InfixOp {self}>"

    def __str__(self):
        return f"{self.expr1} {self.op_desc} {self.expr2}"

    def __call__(self, run):
        return self.op(self.expr1(run), self.expr2(run))


class UnaryOp:
    def __init__(self, expr, op, op_desc):
        self.expr = expr
        self.op = op
        self.op_desc = op_desc

    def __repr__(self):
        return f"<guild.filter.UnaryOp {self}>"

    def __str__(self):
        return f"{self.op_desc} {self.expr}"

    def __call__(self, run):
        return self.op(self.expr(run))


class Contains:
    def __init__(self, run_valref, target_expr, not_contains=False):
        self.run_valref = run_valref
        self.target_expr = target_expr
        self.not_contains = not_contains

    def __repr__(self):
        return f"<guild.filter.Contains {self}>"

    def __str__(self):
        return (
            f"{self.run_valref} {'not ' if self.not_contains else ''}"
            f"contains {self.target_expr}"
        )

    def __call__(self, run):
        run_val = _get_run_val(run, self.run_valref)
        maybe_negate = lambda x: not x if self.not_contains else x
        if not run_val:
            return maybe_negate(False)
        target_val = self.target_expr(run)
        if isinstance(run_val, list):
            return maybe_negate(target_val in run_val)
        return maybe_negate(str(target_val).lower() in str(run_val).lower())


# =================================================================
# Filter API
# =================================================================


class parser:
    def __init__(self, debug=False):
        self._l = lexer()
        self._p = _yacc.yacc(debug=debug, write_tables=False)

    def parse(self, s):
        self._l.lineno = 1
        return self._p.parse(s, self._l)


class FilterRun:
    def __init__(self, attrs, flags, scalars):
        self.attrs = attrs
        self.flags = flags
        self.scalars = scalars


def runs_filter(expr):
    # TODO!

    if expr == "*":
        return lambda run: run
    return lambda run: _filter(run, expr)


def _filter(run, pattern):
    m = re.match(r"(.+?)=(.+)", pattern)
    if not m:
        return False
    flag_name, flag_val_str = m.groups()
    flag_val = yaml_util.decode_yaml(flag_val_str)
    actual_val = run.get("flags", {}).get(flag_name)
    return actual_val == flag_val
