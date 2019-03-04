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

import logging
import os
import textwrap

import click

from guild import op_util

log = logging.getLogger("guild")

class ConsoleFormatter(click.HelpFormatter):

    _in_section = False

    def start_section(self, val):
        if self._in_section:
            self.dedent()
            self.dedent()
            self.write_paragraph()
        self.write_text(click.style(val, bold=True))
        self.write_paragraph()
        self.indent()
        self.indent()
        self._in_section = True

    def write_heading(self, heading):
        self.write_text(click.style(heading, bold=True))

    def write_subheading(self, val):
        self.write_text("%s:" % val)

    def write_description(self, val):
        for i, par in enumerate(val.split("\n")):
            if i > 0:
                self.write_paragraph()
            self.write_text(par)

class RestFormatter(click.HelpFormatter):

    _in_section = False
    _heading_chars = "#=^-`"
    _indent_level = 0

    def start_section(self, val):
        if self._in_section:
            self.dedent()
            self.write_paragraph()
        self.write_text(val)
        self.write_text(self._heading_char() * len(val))
        self.write_paragraph()
        self.indent()
        self._in_section = True

    def _heading_char(self):
        assert self._indent_level < len(self._heading_chars)
        return self._heading_chars[self._indent_level]

    def write_heading(self, heading):
        self.write_text(heading)
        self.write_text(self._heading_char() * len(heading))

    def write_subheading(self, val):
        self.write_heading(val)

    def write_description(self, val):
        for i, par in enumerate(val.split("\n")):
            if i == 0:
                self.write_text("*%s*" % par)
            else:
                self.write_paragraph()
                self.write_text(par)

    def write_dl(self, rows, col_max=None, col_spacing=None,
                 preserve_paragraphs=False):
        for i, (name, desc) in enumerate(rows):
            if i > 0:
                self.write_paragraph()
            self.write_text("**%s**" % name)
            super(RestFormatter, self).indent()
            self.write_text("*%s*" % desc)
            super(RestFormatter, self).dedent()

    def indent(self):
        self._indent_level += 1

    def dedent(self):
        self._indent_level -= 1

def guildfile_console_help(guildfile, model_desc=None):
    out = ConsoleFormatter()
    out.start_section("OVERVIEW")
    _write_console_help_overview(guildfile, model_desc, out)
    out.start_section("MODELS")
    _write_models(guildfile, out)
    return "".join(out.buffer)

def _write_console_help_overview(guildfile, model_desc, out):
    model_desc = model_desc or _format_guildfile_dir(guildfile)
    out.write_text(textwrap.dedent(
        """
        You are viewing help for models defined in %s.

        To run a model operation use 'guild run MODEL:OPERATION' where
        MODEL is one of the model names listed below and OPERATION is
        an associated operation.

        You may set operation flags using 'FLAG=VALUE' arguments to
        the run command. Refer to the operations below for a list of
        supported flags. Model flags apply to all operations.

        For more help, try 'guild run --help' or 'guild --help'.
        """
        % model_desc))

def _format_guildfile_dir(mf):
    if _is_cwd(mf.dir):
        return "the current directory"
    else:
        relpath = os.path.relpath(mf.dir)
        if relpath[0] != '.':
            relpath = os.path.join(".", relpath)
        return "'%s'" % relpath

def _is_cwd(path):
    return os.path.abspath(path) == os.path.abspath(os.getcwd())

def package_description(guildfile):
    out = RestFormatter()
    if guildfile.package:
        out.start_section(guildfile.package.name)
        _write_package_desc(guildfile.package, out)
    if guildfile.models:
        out.start_section("Models")
        _write_models(guildfile, out)
    return "".join(out.buffer)

def _write_package_desc(pkg, out):
    if pkg.description:
        out.write_description(pkg.description)
    if pkg.tags:
        out.write_paragraph()
        out.write_text("Keywords: %s" % " ".join(pkg.tags))

def _write_models(guildfile, out):
    i = 0
    for model in _sorted_models(guildfile.models):
        if i > 0:
            out.write_paragraph()
        _write_model(model, out)
        i += 1

def _sorted_models(models):
    def sort_key(m):
        if m.name[:1] == "_":
            return "\xff" + m.name
        return m.name
    return sorted(models.values(), key=sort_key)

def _write_model(m, out):
    out.write_heading(m.name or "Anonymous model")
    out.indent()
    if m.description:
        out.write_paragraph()
        out.write_description(m.description)
    out.write_paragraph()
    _write_operations(m, out)
    out.write_paragraph()
    if m.references:
        _write_references(m.references, out)
    out.dedent()

def _write_operations(m, out):
    out.write_subheading("Operations")
    out.write_paragraph()
    out.indent()
    if m.operations:
        prev_op = None
        for op in m.operations:
            if op.name[:1] == "_":
                continue
            if prev_op:
                out.write_paragraph()
            _write_operation(op, out)
            prev_op = op
    else:
        out.write_text(
            "No operations defined for this model")
    out.dedent()

def _write_operation(op, out):
    out.write_heading(op.name)
    out.indent()
    if op.description:
        out.write_description(op.description)
    if op.flags:
        if op.description:
            out.write_paragraph()
        _write_flags(op.flags, "Flags", out)
    out.dedent()

def _write_flags(flags, heading, out, no_flags_msg=None):
    out.write_subheading(heading)
    out.indent()
    if flags:
        out.write_dl(flags_dl(flags), preserve_paragraphs=True)
    else:
        if no_flags_msg:
            out.write_description(no_flags_msg)
    out.dedent()

def flags_dl(flags):
    if not flags:
        return []
    max_flag_len = max([len(flag.name) for flag in flags])
    return [
        (flag.name, _format_flag_desc(flag, max_flag_len))
        for flag in flags
    ]

def _format_flag_desc(flag, max_flag_len):
    lines = flag.description.split("\n")
    if flag.default is not None:
        line1_suffix = "(default is %s)" % _default_label(flag.default)
    elif flag.required:
        line1_suffix = "(required)"
    elif flag.null_label:
        line1_suffix = "(default is %s)" % flag.null_label
    else:
        line1_suffix = ""
    if lines[0]:
        lines[0] += " "
    lines[0] += line1_suffix
    if flag.choices:
        lines.append(_format_flag_choices(flag.choices, max_flag_len))
    if len(lines) > 1:
        return "\n\n".join(lines) + "\n\b\n"
    else:
        return lines[0]

def _default_label(val):
    return op_util.format_flag_val(val)

def _format_flag_choices(choices, max_flag_len):
    out = click.HelpFormatter()
    if _choices_have_description(choices):
        out.width = out.width - max_flag_len - 4
        _format_flag_choices_dl(choices, out)
        return "\n\b\n" + out.getvalue()
    else:
        out.width = out.width - max_flag_len - 4 - len("Choices:")
        _format_flag_choices_value_list(choices, out)
        return "\n\b\n" + out.getvalue()

def _choices_have_description(choices):
    for c in choices:
        if c.description:
            return True
    return False

def _format_flag_choices_dl(choices, out):
    out.write_heading("Choices")
    out.indent()
    out.write_dl(
        [(op_util.format_flag_val(choice.value),
          "\n\n".join(choice.description.split("\n")))
         for choice in choices],
        preserve_paragraphs=True)
    out.dedent()

def _format_flag_choices_value_list(choices, out):
    vals = [c.value for c in choices]
    out.write_dl([("Choices:", op_util.format_flag_val(vals))])

def _write_references(refs, out):
    out.write_subheading("References")
    out.write_paragraph()
    out.indent()
    for ref in refs:
        out.write_text("\b\n- %s" % ref)
    out.dedent()
