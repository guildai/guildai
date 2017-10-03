import logging
import os
import re
import sys

import click

TABLE_COL_SPACING = 2

class Exit(Exception):

    def __init__(self, msg, exit_status):
        super(Exit, self).__init__()
        self.msg = msg
        self.exit_status = exit_status

    def __str__(self):
        return "(%i) %s" % (self.exit_status, self.msg)

def main(debug):
    _init_logging(debug)

def _init_logging(debug):
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")

def apply_main(cmd):
    prog = os.path.basename(sys.argv[0])
    try:
        cmd.main(standalone_mode=False)
    except click.exceptions.Abort:
        _handle_keyboard_interrupt()
    except click.exceptions.ClickException as e:
        _handle_click_exception(e, prog)
    except Exit as e:
        _print_error_and_exit(prog, e.msg, e.exit_status)

def _handle_keyboard_interrupt():
    sys.exit(1)

def _handle_click_exception(e, prog):
    click.echo("%s: %s" % (prog, _format_click_error_message(e)), err=True)
    if e.ctx:
        click.echo(
            "Try '%s' for more information." % ctx_cmd_help(e.ctx),
            err=True)
    sys.exit(e.exit_code)

def ctx_cmd_help(ctx):
    return "%s %s" % (_normalize_command_name(ctx.command_path),
                     ctx.help_option_names[0])

def _normalize_command_name(cmd_path):
    m = re.match("^(.+?), .+$", cmd_path)
    return m.group(1) if m else cmd_path

def _format_click_error_message(e):
    if isinstance(e, click.exceptions.MissingParameter):
        return _format_missing_parameter_error(e)
    elif isinstance(e, click.exceptions.NoSuchOption):
        return _format_no_such_option_error(e)
    elif isinstance(e, click.exceptions.UsageError):
        return _format_usage_error(e)
    else:
        return e.format_message()

def _format_missing_parameter_error(e):
    return "missing argument for %s" % e.param.human_readable_name

def _format_no_such_option_error(e):
    if e.possibilities:
        more_help = " (did you mean %s?)" % e.possibilities[0]
    else:
        more_help = ""
    return "unrecognized option '%s'%s" % (e.option_name, more_help)

def _format_usage_error(e):
    msg = e.format_message()
    replacements = [
        ('No such command "(.+)"',
         "unrecognized command '%s'"),
        ("Got unexpected extra argument \\((.+?)\\)",
         "unexpected extra argument '%s'")
    ]
    for msg_pattern, new_msg_pattern in replacements:
        m = re.match(msg_pattern, msg)
        if m:
            return new_msg_pattern % m.groups()
    else:
        return msg

def _print_error_and_exit(prog, msg, exit_status):
    if msg:
        click.echo("%s: %s" % (prog, msg), err=True)
    sys.exit(exit_status)

def error(msg=None, exit_status=1):
    raise Exit(msg, exit_status)

def out(s, **kw):
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

def confirm(prompt):
    click.echo(prompt, nl=False)
    click.echo(" (y/N) ", nl=False)
    c = input()
    return c.lower() in ["y", "yes"]

def input(prompt=""):
    try:
        return raw_input(prompt)
    except NameError:
        return input(prompt)
