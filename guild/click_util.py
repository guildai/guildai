# Copyright 2017 TensorHub, Inc.
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
import re

import click

class Args(object):

    def __init__(self, kw):
        for name in kw:
            setattr(self, name, kw[name])

def use_args(fn0):
    def fn(*args, **kw):
        return fn0(*(args + (Args(kw),)))
    return functools.update_wrapper(fn, fn0)

def append_params(fn, params):
    fn.__click_params__ = getattr(fn, "__click_params__", [])
    fn.__click_params__.extend(reversed(params))

def format_error_message(e):
    msg_parts = [_format_click_error_message(e)]
    if e.ctx:
        msg_parts.append(
            "\nTry '%s' for more information."
            % ctx_cmd_help(e.ctx))
    return "".join(msg_parts)

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
         "unexpected extra argument '%s'"),
        ("Got unexpected extra arguments \\((.+?)\\)",
         "unexpected extra arguments '%s'"),
    ]
    for msg_pattern, new_msg_pattern in replacements:
        m = re.match(msg_pattern, msg)
        if m:
            return new_msg_pattern % m.groups()
    return msg

def ctx_cmd_help(ctx):
    return "%s %s" % (_normalize_command_name(ctx.command_path),
                     ctx.help_option_names[0])

def _normalize_command_name(cmd_path):
    m = re.match("^(.+?), .+$", cmd_path)
    return m.group(1) if m else cmd_path
