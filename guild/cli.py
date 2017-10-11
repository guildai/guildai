import logging
import os
import re
import sys

import click

TABLE_COL_SPACING = 2

def error(msg=None, exit_status=1):
    raise SystemExit(msg, exit_status)

def out(s="", **kw):
    click.echo(s, **kw)

def table(data, cols, sort=None, detail=None, indent=0, err=False):
    data = sorted(data, _data_cmp(sort))
    formatted = _format_data(data, cols + (detail or []))
    col_info = _col_info(formatted, cols)
    for item in formatted:
        _item_out(item, cols, col_info, detail, indent, err)

def _data_cmp(sort):
    if sort is None:
        return lambda _x, _y: 0
    else:
        return lambda x, y: _item_cmp(x, y, sort)

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
        return -cmp(x.get(sort), y.get(sort))
    else:
        return cmp(x.get(sort), y.get(sort))

def _format_data(data, cols):
    formatted = []
    for item0 in data:
        item = {}
        formatted.append(item)
        for col in cols:
            item[col] = str(item0.get(col, ""))
    return formatted

def _col_info(data, cols):
    info = {}
    for item in data:
        for col in cols:
            coli = info.setdefault(col, {})
            coli["width"] = max(coli.get("width", 0), len(item[col]))
    return info

def _item_out(item, cols, col_info, detail, indent, err):
    indent_padding = " " * indent
    click.echo(indent_padding, nl=False, err=err)
    for i, col in enumerate(cols):
        val = item[col]
        last_col = i == len(cols) - 1
        padded = _pad_col_val(val, col, col_info) if not last_col else val
        click.echo(padded, nl=False, err=err)
    click.echo(err=err)
    for key in (detail or []):
        click.echo(indent_padding, nl=False, err=err)
        click.echo("  %s: %s" % (key, item[key]), err=err)

def _pad_col_val(val, col, col_info):
    return val.ljust(col_info[col]["width"] + TABLE_COL_SPACING)

def confirm(prompt, default=False):
    click.echo(prompt, nl=False)
    click.echo(" %s " % ("(Y/n)" if default else "(y/N)"), nl=False)
    c = input()
    yes_vals = ["y", "yes"]
    if default:
        yes_vals.append("")
    return c.lower().strip() in yes_vals

def input(prompt=""):
    try:
        return raw_input(prompt)
    except NameError:
        return input(prompt)
