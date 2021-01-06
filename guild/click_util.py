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

import contextlib
import functools
import json
import os
import re

import click

import guild

CMD_SPLIT_P = re.compile(r", ?")


def NUMBER(s):
    try:
        return int(s)
    except ValueError:
        try:
            return float(s)
        except ValueError:
            raise ValueError("%s is not a valid number")


class Args(object):
    def __init__(self, **kw):
        self.__names = set()
        for name in kw:
            setattr(self, name, kw[name])

    def __repr__(self):
        return "<guild.click_util.Args %s>" % self.as_kw()

    def as_kw(self):
        return {name: getattr(self, name) for name in self.__names}

    def __setattr__(self, name, val):
        self.__dict__[name] = val
        if name[0] != "_":
            self.__names.add(name)

    def copy(self, **kw):
        copy_kw = self.as_kw()
        copy_kw.update(kw)
        return Args(**copy_kw)


class Group(click.Group):
    def get_command(self, ctx, cmd_name):
        for cmd in self.commands.values():
            names = CMD_SPLIT_P.split(cmd.name)
            if cmd_name in names:
                cmd_name = cmd.name
                break
        return super(Group, self).get_command(ctx, cmd_name)


class ClickBaseHelpFormatter(click.formatting.HelpFormatter):
    """Patched version of click's HelpFormatter class.

    Overrides write_dl to support preserve paragraphs.
    """

    # pylint: disable=arguments-differ
    def write_dl(self, rows, col_max=30, col_spacing=2, preserve_paragraphs=False):
        rows = list(rows)
        widths = click.formatting.measure_table(rows)
        if len(widths) != 2:
            raise TypeError("Expected two columns for definition list")

        first_col = min(widths[0], col_max) + col_spacing

        for first, second in click.formatting.iter_rows(rows, len(widths)):
            self.write("{:>{w}}{}".format("", first, w=self.current_indent))
            if not second:
                self.write("\n")
                continue
            if click.formatting.term_len(first) <= first_col - col_spacing:
                self.write(" " * (first_col - click.formatting.term_len(first)))
            else:
                self.write("\n")
                self.write(" " * (first_col + self.current_indent))

            text_width = max(self.width - first_col - 2, 10)
            wrapped_text = click.formatting.wrap_text(
                second, text_width, preserve_paragraphs=preserve_paragraphs
            )
            lines = wrapped_text.splitlines()

            if lines:
                self.write("{}\n".format(lines[0]))

                for line in lines[1:]:
                    self.write(
                        "{:>{w}}{}\n".format(
                            "", line, w=first_col + self.current_indent
                        )
                    )

                if len(lines) > 1:
                    # separate long help from next option
                    self.write("\n")
            else:
                self.write("\n")


class HelpFormatter(ClickBaseHelpFormatter):

    _text_subs = [
        (re.compile("``"), "'"),
        (re.compile("`"), ""),
        (re.compile(r"^### (.+?)$", re.MULTILINE), lambda m: m.group(1).upper()),
        (re.compile(r"\*\*"), ""),
    ]

    def write_text(self, text):
        super(HelpFormatter, self).write_text(self._format_text(text))

    def _format_text(self, text):
        for pattern, repl in self._text_subs:
            text = pattern.sub(repl, text)
        return text

    def write_dl(self, rows, col_max=None, col_spacing=None, preserve_paragraphs=False):
        rows = [(term, self._format_text(text)) for term, text in rows]
        super(HelpFormatter, self).write_dl(
            rows, preserve_paragraphs=preserve_paragraphs
        )


class JSONHelpFormatter(object):

    _finalized = object()

    def __init__(self):
        self._val = {"version": guild.__version__}
        self._help_text = None
        self._cur_dl = None
        self._buf = []
        self.width = 999999999

    def write_usage(self, prog, args='', **_kw):
        self._val["usage"] = {"prog": prog, "args": args}

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
        if self._help_text is not None and self._help_text is not self._finalized:
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
        self._cur_dl.extend(
            [{"term": term, "help": definition} for term, definition in rows]
        )

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
    ctx = getattr(e, "ctx", None)
    if ctx:
        msg_parts.append("\nTry '%s' for more information." % cmd_help(e.ctx))
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
        ("No such command \"(.+)\"", "unrecognized command '%s'"),
        ("Got unexpected extra argument \\((.+?)\\)", "unexpected extra argument '%s'"),
        (
            "Got unexpected extra arguments \\((.+?)\\)",
            "unexpected extra arguments '%s'",
        ),
    ]
    for msg_pattern, new_msg_pattern in replacements:
        m = re.match(msg_pattern, msg)
        if m:
            return new_msg_pattern % m.groups()
    return msg


def cmd_help(ctx):
    return "%s %s" % (
        normalize_command_path(ctx.command_path),
        ctx.help_option_names[0],
    )


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


def completion_filename(ext=None, **_kw):
    if os.getenv("_GUILD_COMPLETE") == "complete":
        return _compgen_filenames("file", ext)
    else:
        return []


def completion_dir(**_kw):
    if os.getenv("_GUILD_COMPLETE") == "complete":
        return ["!!dir"]
    else:
        return []


def completion_opnames(names):
    if os.getenv("_GUILD_COMPLETE") == "complete":
        return ["!!no-colon-wordbreak"] + names
    else:
        return []


def _compgen_filenames(type, ext):
    if not ext:
        return ["!!%s:*" % type]
    return ["!!%s:*.@(%s)" % (type, "|".join(ext))]


def completion_nospace():
    if os.getenv("_GUILD_COMPLETE") == "complete":
        return ["!!nospace"]
    else:
        return []


def completion_batchfile(ext=None):
    if os.getenv("_GUILD_COMPLETE") == "complete":
        return _compgen_filenames("batchfile", ext)
    else:
        return []


def completion_command(filter=None):
    if os.getenv("_GUILD_COMPLETE") == "complete":
        if filter:
            return ["!!command:%s" % filter]
        else:
            return ["!!command"]
    else:
        return []


def completion_run_dirpath(run_dir, all=False):
    if os.getenv("_GUILD_COMPLETE") == "complete":
        if all:
            return ["!!allrundirs:%s" % run_dir]
        else:
            return ["!!rundirs:%s" % run_dir]
    else:
        return []


def completion_run_filepath(run_dir):
    if os.getenv("_GUILD_COMPLETE") == "complete":
        return ["!!runfiles:%s" % run_dir]
    else:
        return []


def completion_safe_apply(ctx, f, args):
    from guild import config

    with config.SetGuildHome(ctx.parent.params.get("guild_home")):
        try:
            return f(*args)
        except (Exception, SystemExit):
            if os.getenv("_GUILD_COMPLETE_DEBUG") == "1":
                raise
            return None


def patch_click():
    try:
        from click import _bashcomplete
    except ImportError:
        from click import shell_completion

        shell_completion._is_incomplete_option = _patched_is_incomplete_option
    else:
        _bashcomplete.is_incomplete_option = _patched_is_incomplete_option


def _patched_is_incomplete_option(all_args, cmd_param):
    """Patched version of is_complete_option.

    Fixes issue testing a cmd param against the current list of
    args. Upstream version does not consider combined short form args
    and so a command like `guild check -nt <auto>` doesn't work. The
    patched version considers that `t` above is the current param
    option.
    """
    from click import _bashcomplete

    if not isinstance(cmd_param, _bashcomplete.Option):
        return False
    if cmd_param.is_flag:
        return False
    last_option = None
    for index, arg_str in enumerate(
        reversed([arg for arg in all_args if arg != _bashcomplete.WORDBREAK])
    ):
        if index + 1 > cmd_param.nargs:
            break
        if _bashcomplete.start_of_option(arg_str):
            last_option = arg_str

    if not last_option:
        return False
    if last_option[:2] == "--":
        return last_option in cmd_param.opts

    assert last_option[:1] == "-", last_option
    for i in range(len(last_option), 0, -1):
        if "-%s" % last_option[i:] in cmd_param.opts:
            return True
    return False


if os.getenv("SKIP_PATCH_CLICK") != "1":
    patch_click()
