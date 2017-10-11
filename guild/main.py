import os
import sys

import click

import guild.click_util
import guild.main_cmd

def main():
    try:
        guild.main_cmd.main(standalone_mode=False)
    except click.exceptions.Abort:
        _handle_keyboard_interrupt()
    except click.exceptions.ClickException as e:
        _handle_click_exception(e,)
    except SystemExit as e:
        _handle_system_exit(e)

def _handle_keyboard_interrupt():
    sys.exit(1)

def _handle_click_exception(e):
    msg = guild.click_util.format_error_message(e)
    _print_error_and_exit(msg, e.exit_code)

def _print_error_and_exit(msg, exit_status):
    if msg:
        prog = os.path.basename(sys.argv[0])
        click.echo("%s: %s" % (prog, msg), err=True)
    sys.exit(exit_status)

def _handle_system_exit(e):
    if isinstance(e.code, tuple) and len(e.code) == 2:
        msg, code = e.code
    elif isinstance(e.code, int):
        msg, code = None, e.code
    else:
        msg, code = e.message, 1
    _print_error_and_exit(msg, code)
