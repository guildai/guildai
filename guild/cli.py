import logging
import os
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
    except click.exceptions.MissingParameter as e:
        _handle_missing_parameter(e)
    except click.exceptions.ClickException as e:
        _handle_click_exception(e)
    except Exit as e:
        _print_error_and_exit(prog, e.msg, e.exit_status)

def _handle_keyboard_interrupt():
    sys.exit(1)

def _handle_missing_parameter(e):
    """Workaround for https://github.com/pallets/click/issues/855"""
    click.echo(
        "%s\n"
        "Try '%s %s' for help.\n"
        "\n"
        "Error: missing argument for %s"
        % (e.ctx.get_usage(),
           e.ctx.command_path,
           e.ctx.help_option_names[0],
           e.param.human_readable_name),
        err=True)
    sys.exit(e.exit_code)

def _handle_click_exception(e):
    e.show()
    sys.exit(e.exit_code)

def _print_error_and_exit(prog, msg, exit_status):
    if msg:
        click.echo("%s: %s" % (prog, msg), err=True)
    sys.exit(exit_status)

def error(msg=None, exit_status=1):
    raise Exit(msg, exit_status)

def out(s, **kw):
    click.echo(s, **kw)
