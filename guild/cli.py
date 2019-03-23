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

import functools
import logging

import click
import six

from guild import config

log = logging.getLogger("guild")

TABLE_COL_SPACING = 2
MAX_WIDTH = 999

try:
    input = raw_input
except NameError:
    input = input

_noted = set()

def error(msg=None, exit_status=1):
    raise SystemExit(msg, exit_status)

def out(s="", wrap=False, **kw):
    if wrap:
        s = _wrap(s)
    _echo(s, **kw)

def _wrap(s):
    terminal_width = click.get_terminal_size()[0]
    width = max(min(terminal_width, 78), 40)
    return click.wrap_text(s, width)

def _echo(s, err=False, **kw):
    if config.log_output():
        if err:
            log.warning(s)
        else:
            log.info(s)
    else:
        click.echo(s, err=err, **kw)

def note(msg):
    _echo(click.style(msg, dim=True), err=True)
    _noted.add(msg)

def note_once(msg):
    if msg not in _noted:
        note(msg)

def table(data, cols, sort=None, detail=None, indent=0, err=False):
    data = sorted(data, key=_table_row_sort_key(sort))
    formatted = _format_data(data, cols + (detail or []))
    col_info = _col_info(formatted, cols)
    for item in formatted:
        _item_out(item, cols, col_info, detail, indent, MAX_WIDTH, err)

def _table_row_sort_key(sort):
    if not sort:
        return lambda _: 0
    else:
        return functools.cmp_to_key(lambda x, y: _item_cmp(x, y, sort))

def _item_cmp(x, y, sort):
    if isinstance(sort, str):
        return _val_cmp(x, y, sort)
    else:
        for part in sort:
            part_cmp = _val_cmp(x, y, part)
            if part_cmp != 0:
                return part_cmp
        return 0

def _val_cmp(x, y, sort):
    if sort.startswith("-"):
        sort = sort[1:]
        rev = -1
    else:
        rev = 1
    x_val = x.get(sort)
    y_val = y.get(sort)
    return rev * ((x_val > y_val) - (x_val < y_val))

def _format_data(data, cols):
    formatted = []
    for item0 in data:
        item = {}
        formatted.append(item)
        for col in cols:
            item[col] = _str_or_list(item0.get(col, ""))
    return formatted

def _str_or_list(x):
    if isinstance(x, list):
        return x
    elif isinstance(x, six.string_types):
        return x
    else:
        return str(x)

def _col_info(data, cols):
    info = {}
    for item in data:
        for col in cols:
            coli = info.setdefault(col, {})
            coli["width"] = max(coli.get("width", 0), len(item[col]))
    return info

def _item_out(item, cols, col_info, detail, indent, max_col_width, err):
    indent_padding = " " * indent
    click.echo(indent_padding, nl=False, err=err)
    line_pos = indent
    for i, col in enumerate(cols):
        val = item[col]
        last_col = i == len(cols) - 1
        val = _pad_col_val(val, col, col_info) if not last_col else val
        line_pos = line_pos + len(val)
        if line_pos > max_col_width:
            click.echo(val[:-(line_pos-max_col_width)], nl=False, err=err)
            break
        else:
            click.echo(val, nl=False, err=err)
    click.echo(err=err)
    terminal_width = click.get_terminal_size()[0]
    for key in (detail or []):
        click.echo(indent_padding, nl=False, err=err)
        formatted = _format_detail_val(item[key], indent, terminal_width)
        click.echo("  %s:%s" % (key, formatted), err=err)

def _format_detail_val(val, indent, terminal_width):
    if isinstance(val, list):
        if val:
            val_indent = " " * (indent + 4)
            val_width = terminal_width - len(val_indent)
            return "\n" + "\n".join([
                click.wrap_text(x, val_width, val_indent, val_indent)
                for x in val
            ])
        else:
            return " -"
    else:
        return (" %s" % val)

def _pad_col_val(val, col, col_info):
    return val.ljust(col_info[col]["width"] + TABLE_COL_SPACING)

def confirm(prompt, default=False, wrap=False):
    if wrap:
        prompt = _wrap(prompt)
    click.echo(prompt, nl=False, err=True)
    click.echo(
        " %s " % ("(Y/n)" if default else "(y/N)"),
        nl=False, err=True)
    c = input()
    yes_vals = ["y", "yes"]
    if default:
        yes_vals.append("")
    return c.lower().strip() in yes_vals

def page(text):
    click.echo_via_pager(text)

def style(text, **kw):
    return click.style(text, **kw)
