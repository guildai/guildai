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

import contextlib
import functools
import json
import re

import click

import guild

class Args(object):

    def __init__(self, **kw):
        for name in kw:
            setattr(self, name, kw[name])
        self.__names = list(kw)

    def __repr__(self):
        return "<guild.click_util.Args %s>" % self.as_kw()

    def as_kw(self):
        return {name: getattr(self, name) for name in self.__names}

class Group(click.Group):

    def get_command(self, ctx, cmd_name):
        for cmd in self.commands.values():
            names = re.split(", ?", cmd.name)
            if cmd_name in names:
                cmd_name = cmd.name
                break
        return super(Group, self).get_command(ctx, cmd_name)

class HelpFormatter(click.formatting.HelpFormatter):

    _text_subs = [
        (re.compile("``"), "'"),
        (re.compile("`"), ""),
        (re.compile(r"^### (.+?)$", re.MULTILINE),
         lambda m: m.group(1).upper()),
        (re.compile(r"\*\*"), ""),
    ]

    def write_text(self, text):
        super(HelpFormatter, self).write_text(self._format_text(text))

    def _format_text(self, text):
        for pattern, repl in self._text_subs:
            text = pattern.sub(repl, text)
        return text

    def write_dl(self, rows, col_max=None, col_spacing=None,
                 preserve_paragraphs=False):
        rows = [(term, self._format_text(text)) for term, text in rows]
        super(HelpFormatter, self).write_dl(
            rows, preserve_paragraphs=preserve_paragraphs)

class JSONHelpFormatter(object):

    _finalized = object()

    def __init__(self):
        self._val = {
            "version": guild.__version__
        }
        self._help_text = None
        self._cur_dl = None
        self._buf = []
        self.width = 999999999

    def write_usage(self, prog, args='', **_kw):
        self._val["usage"] = {
            "prog": prog,
            "args": args
        }

    def write_paragraph(self):
        if self._help_text is not None:
            self._help_text.append("\n")

    @contextlib.contextmanager
    def indentation(self):
        self.indent()
        try:
            yield
        finally:
            self.dedent()

    def indent(self):
        if self._help_text is None:
            self._help_text = []

    def dedent(self):
        if (self._help_text is not None and
            self._help_text is not self._finalized):
            self._val["help"] = "".join(self._help_text)
            self._help_text = self._finalized

    def write_text(self, text):
        assert self._help_text is not None
        assert self._help_text is not self._finalized
        self._help_text.append(text)

    @contextlib.contextmanager
    def section(self, name):
        if name == "Options":
            self._val["options"] = self._cur_dl = []
        elif name == "Commands":
            self._val["commands"] = self._cur_dl = []
        else:
            raise AssertionError(name)
        self.indent()
        try:
            yield
        finally:
            self.dedent()

    def write_dl(self, rows, **_kw):
        assert self._cur_dl is not None
        self._cur_dl.extend([{
            "term": term,
            "help": definition
        } for term, definition in rows])

    def getvalue(self):
        return json.dumps(self._val)

def use_args(fn0):
    def fn(*args, **kw):
        return fn0(*(args + (Args(**kw),)))
    return functools.update_wrapper(fn, fn0)

def append_params(fn, params):
    fn.__click_params__ = getattr(fn, "__click_params__", [])
    for param in reversed(params):
        if callable(param):
            param(fn)
        else:
            fn.__click_params__.append(param)

def format_error_message(e):
    msg_parts = [_format_click_error_message(e)]
    if e.ctx:
        msg_parts.append(
            "\nTry '%s' for more information."
            % cmd_help(e.ctx))
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

def cmd_help(ctx):
    return "%s %s" % (normalize_command_path(ctx.command_path),
                     ctx.help_option_names[0])

def normalize_command_path(cmd_path):
    m = re.match("^(.+?), .+$", cmd_path)
    return m.group(1) if m else cmd_path

def render_doc(fn):
    parts = re.split("({{.*}})", fn.__doc__, re.DOTALL)
    vars = fn.__globals__
    rendered_parts = [_maybe_render_doc(part, vars) for part in parts]
    fn.__doc__ = "".join(rendered_parts)
    return fn

def _maybe_render_doc(s, vars):
    m = re.match("{{(.+)}}", s)
    if not m:
        return s
    # pylint: disable=eval-used
    fn = eval(m.group(1).strip(), vars)
    return fn.__doc__
