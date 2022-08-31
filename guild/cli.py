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

import functools
import logging
import os
import sys
import shutil
import typing

import click

from guild import ansi_util  # lightweight
from guild import config  # lightweight

log = logging.getLogger("guild")

TABLE_COL_SPACING = 2

_shell = os.getenv("SHELL")


def _max_width():
    try:
        return int(os.environ["COLUMNS"])
    except (KeyError, ValueError):
        return shutil.get_terminal_size()[0]


try:
    input = raw_input
except NameError:
    pass

_noted = set()


def error(msg=None, exit_status=1) -> typing.NoReturn:
    raise SystemExit(msg, exit_status)


def out(s="", wrap=False, **kw):
    if wrap:
        s = wrap(s)
    _echo(s, **kw)


def wrap(s, width=None):
    width = width or _default_terminal_width()
    return click.wrap_text(s, width)


def _default_terminal_width():
    width = terminal_width()
    return max(min(width, 78), 40)


def terminal_width():
    return shutil.get_terminal_size().columns


def _echo(s, err=False, **kw):
    if config.log_output():
        if err:
            log.warning(s)
        else:
            log.info(s)
    else:
        click.echo(s, err=err, **kw)


def note(msg, err=True, **kw):
    _echo(click.style(msg, dim=True), err=err, **kw)


def note_once(msg):
    if msg not in _noted:
        note(msg)
        _noted.add(msg)


def table(
    data,
    cols,
    sort=None,
    detail=None,
    detail_cb=None,
    indent=0,
    err=False,
    max_width_adj=0,
    file=None,
    **style_kw,
):
    data = sorted(data, key=_table_row_sort_key(sort))
    formatted = _format_table_data(data, cols + (detail or []))
    col_info = _col_info(formatted, cols)
    if sys.stdout.isatty():
        max_width = _max_width() + max_width_adj
    else:
        max_width = None
    for formatted_item, data_item in zip(formatted, data):
        _table_item_out(
            formatted_item,
            data_item,
            cols,
            col_info,
            detail,
            detail_cb,
            indent,
            max_width,
            err,
            file,
            style_kw,
        )


def _table_row_sort_key(sort):
    if not sort:
        return lambda _: 0
    return functools.cmp_to_key(lambda x, y: _item_cmp(x, y, sort))


def _item_cmp(x, y, sort):
    if isinstance(sort, str):
        return _val_cmp(x, y, sort)
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
    x_val_coerced = _coerce_cmp_val(x_val, y_val)
    y_val_coerced = _coerce_cmp_val(y_val, x_val_coerced)
    return rev * ((x_val_coerced > y_val_coerced) - (x_val_coerced < y_val_coerced))


def _coerce_cmp_val(x, y):
    if sys.version_info[0] == 2:
        return x
    if x is None:
        if y is None:
            return ""
        return type(y)()
    if type(x) == type(y):  # pylint: disable=unidiomatic-typecheck
        return x
    if isinstance(x, (int, float)) and isinstance(y, (int, float)):
        return x
    if isinstance(x, str):
        return x
    if isinstance(y, str):
        return ""
    return str(x)


def _format_table_data(data, cols):
    return [{col: _format_table_val(item.get(col)) for col in cols} for item in data]


def _format_table_val(val):
    if val is None:
        return ""
    if isinstance(val, str):
        return val
    return str(val)


def _col_info(data, cols):
    info = {}
    for item in data:
        for col in cols:
            col_info = info.setdefault(col, {})
            col_info["width"] = max(col_info.get("width", 0), len(item[col]))
    return info


def _table_item_out(
    formatted_item,
    data_item,
    cols,
    col_info,
    detail,
    detail_cb,
    indent,
    max_col_width,
    err,
    file,
    style_kw,
):
    indent_padding = " " * indent
    click.echo(indent_padding, file=file, nl=False, err=err)
    line_pos = indent
    for i, col in enumerate(cols):
        val = formatted_item[col]
        last_col = i == len(cols) - 1
        val = _pad_col_val(val, col, col_info) if not last_col else val
        val_display_len = len(ansi_util.strip_ansi_format(val))
        line_pos = line_pos + val_display_len
        if max_col_width is not None:
            display_val = val[: -(line_pos - max_col_width)]
        else:
            display_val = val
        if max_col_width is not None and line_pos > max_col_width:
            click.echo(
                style(display_val, **style_kw),
                file=file,
                nl=False,
                err=err,
            )
            break
        click.echo(style(val, **style_kw), file=file, nl=False, err=err)
    click.echo(file=file, err=err)
    terminal_width = shutil.get_terminal_size()[0]
    if detail_cb:
        detail_cb(data_item)
    else:
        for key in detail or []:
            click.echo(indent_padding, file=file, nl=False, err=err)
            formatted = _format_detail_val(formatted_item[key], indent, terminal_width)
            click.echo(
                style(f"  {key}:{formatted}", **style_kw),
                file=file,
                err=err,
            )


def _format_detail_val(val, indent, terminal_width):
    if isinstance(val, list):
        if val:
            val_indent = " " * (indent + 4)
            val_width = terminal_width - len(val_indent)
            return "\n" + "\n".join(
                [click.wrap_text(x, val_width, val_indent, val_indent) for x in val]
            )
        return " -"
    return f" {val}"


def _pad_col_val(val, col, col_info):
    return val.ljust(col_info[col]["width"] + TABLE_COL_SPACING)


def confirm(prompt, default=False, wrap=False):
    if wrap:
        prompt = wrap(prompt)
    click.echo(prompt, nl=False, err=True)
    yes_no_opts = "(Y/n)" if default else "(y/N)"
    click.echo(f" {yes_no_opts} ", nl=False, err=True)
    c = input()
    yes_vals = ["y", "yes"]
    if default:
        yes_vals.append("")
    return c.lower().strip() in yes_vals


def page(text):
    click.echo_via_pager(text)


def style(text, **kw):
    if not _shell:
        return text
    return click.style(text, **kw)
