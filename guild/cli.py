import logging
import os
import re
import sys

import click

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
            "Try '%s %s' for more information."
            % (e.ctx.command_path, e.ctx.help_option_names[0]),
            err=True)
    sys.exit(e.exit_code)

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
    m = re.match('No such command "(.+)"', msg)
    if m:
        return "unrecognized command '%s'" % m.groups()[0]
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
