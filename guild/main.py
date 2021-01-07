# Copyright 2017-2020 TensorHub, Inc.
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

import os
import sys

import click

from guild import click_util
from guild import exit_code

from guild.commands import main as main_cmd


def main():
    _configure_help_formatter()
    try:
        # pylint: disable=unexpected-keyword-arg,no-value-for-parameter
        main_cmd.main(standalone_mode=False)
    except click.exceptions.Abort:
        _handle_keyboard_interrupt()
    except click.exceptions.ClickException as e:
        _handle_click_exception(e)
    except SystemExit as e:
        _handle_system_exit(e)


def _configure_help_formatter():
    if os.getenv("GUILD_HELP_JSON"):
        click.Context.make_formatter = _make_json_formatter
    else:
        click.Context.make_formatter = _make_plaintext_formatter


def _make_json_formatter(_self):
    return click_util.JSONHelpFormatter()


def _make_plaintext_formatter(_self):
    return click_util.HelpFormatter()


def _handle_keyboard_interrupt():
    sys.exit(1)


def _handle_click_exception(e):
    msg = click_util.format_error_message(e)
    _print_error_and_exit(msg, e.exit_code)


def _print_error_and_exit(msg, exit_status):
    if msg:
        click.echo("guild: %s" % msg, err=True)
    sys.exit(exit_status)


def _handle_system_exit(e):
    msg, code = system_exit_params(e)
    _print_error_and_exit(msg, code)


def system_exit_params(e):
    if isinstance(e.code, tuple) and len(e.code) == 2:
        msg, code = e.code
    elif isinstance(e.code, int):
        msg, code = None, e.code
    else:
        msg, code = e.code, exit_code.DEFAULT_ERROR
    return msg, code
