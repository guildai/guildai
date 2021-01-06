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

import logging
import os
import textwrap

import click

from guild import ansi_util
from guild import click_util
from guild import flag_util

log = logging.getLogger("guild")


class ConsoleFormatter(click_util.ClickBaseHelpFormatter):

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


class RstFormatter(click_util.ClickBaseHelpFormatter):

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
                self.write_text(self._emph(par))
            else:
                self.write_paragraph()
                self.write_text(par)

    def write_dl(self, rows, col_max=None, col_spacing=None, preserve_paragraphs=False):
        for i, (name, desc) in enumerate(rows):
            if i > 0:
                self.write_paragraph()
            self.write_text(self._strong(name))
            super(RstFormatter, self).indent()
            self.write_text(self._emph(desc))
            super(RstFormatter, self).dedent()

    def indent(self):
        self._indent_level += 1

    def dedent(self):
        self._indent_level -= 1

    @staticmethod
    def _emph(s):
        if not s:
            return ""
        return "*%s*" % s

    @staticmethod
    def _strong(s):
        if not s:
            return ""
        return "**%s**" % s


class MarkdownFormatter(click_util.ClickBaseHelpFormatter):
    def __init__(self, heading_level=1):
        super(MarkdownFormatter, self).__init__()
        self._in_section = False
        self._heading_level = heading_level

    def start_section(self, val):
        if self._in_section:
            self.dedent()
            self.write_paragraph()
        self.write_text(self._heading(val))
        self.write_paragraph()
        self.indent()
        self._in_section = True

    def _heading(self, val):
        if self._heading_level <= 6:
            return "%s %s" % ("#" * self._heading_level, val)
        else:
            return "<h%i>%s</h%i>" % (self._heading_level, val, self._heading_level)

    def write_heading(self, heading):
        self.write_text(self._heading(heading))

    def write_subheading(self, val):
        self.write_heading(val)

    def write_description(self, val):
        for i, par in enumerate(val.split("\n")):
            if i == 0:
                self.write_text(self._emph(par))
            else:
                self.write_paragraph()
                self.write_text(par)

    def write_dl(self, rows, col_max=None, col_spacing=None, preserve_paragraphs=False):
        self.write_text("<dl>")
        for name, desc in rows:
            self.write_text("<dt>%s</dt>" % name)
            self.write_text("<dd>%s</dd>" % desc)
        self.write_text("</dl>")

    def indent(self):
        self._heading_level += 1

    def dedent(self):
        self._heading_level -= 1

    @staticmethod
    def _emph(s):
        if not s:
            return ""
        return "*%s*" % s

    @staticmethod
    def _strong(s):
        if not s:
            return ""
        return "**%s**" % s


def guildfile_console_help(guildfile, model_desc=None, strip_ansi_format=False):
    out = ConsoleFormatter()
    out.start_section("OVERVIEW")
    _write_console_help_overview(guildfile, model_desc, out)
    _gen_write_help(guildfile, out, fmt_section_title=str.upper)
    s = "".join(out.buffer)
    if strip_ansi_format:
        s = ansi_util.strip_ansi_format(s)
    return s


def guildfile_markdown_help(guildfile, title=None, base_heading_level=2):
    out = MarkdownFormatter(base_heading_level)
    if title:
        out.write_heading(title)
        out.indent()
        out.write_paragraph()
    out.start_section("Overview")
    _write_markdown_help_overview(out)
    _gen_write_help(guildfile, out)
    return "".join(out.buffer)


def _write_markdown_help_overview(out):
    out.write_text(
        textwrap.dedent(
            """

        Guild AI supported models and operations are listed below. To
        run an operation, you must first install Guild AI by running:

        ```
        $ pip install guildai
        ```

        Refer to [Install Guild AI](https://guild.ai/install) for
        detailed instructions.

        To run a model operation use:

        ```
        $ guild run [MODEL:]OPERATION
        ```

        `MODEL` is one of the model names listed below and `OPERATION`
        is an associated model operation or base operation.

        You may set operation flags using `FLAG=VALUE` arguments to
        the run command. Refer to the operations below for a list of
        supported flags.

        For additional help using Guild, see [Guild AI
        Documentation](https://guild.ai/docs).
        """
        )
    )


def package_description(guildfile):
    out = RstFormatter()
    if guildfile.package:
        out.start_section(guildfile.package.name)
        _write_package_desc(guildfile.package, out)
    _gen_write_help(guildfile, out)
    return "".join(out.buffer)


def _gen_write_help(guildfile, out, fmt_section_title=None):
    fmt_section_title = fmt_section_title or (lambda s: s)
    anon_model, models = _split_models(guildfile)
    if anon_model and anon_model.operations:
        out.start_section(fmt_section_title("Base Operations"))
        _write_anon_model_operations(anon_model, out)
    if models:
        out.start_section(fmt_section_title("Models"))
        _write_models(models, out)


def _write_console_help_overview(guildfile, model_desc, out):
    model_desc = model_desc or _format_guildfile_dir(guildfile)
    out.write_text(
        textwrap.dedent(
            """
        You are viewing help for operations defined in %s.

        To run an operation use 'guild run OPERATION' where OPERATION
        is one of options listed below. If an operation is associated
        with a model, include the model name as MODEL:OPERATION.

        To list available operations, run 'guild operations'.

        Set operation flags using 'FLAG=VALUE' arguments to the run
        command. Refer to the operations below for a list of supported
        flags.

        For more information on running operations, try 'guild run
        --help'. For general information, try 'guild --help'.
        """
            % model_desc
        )
    )


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


def _write_package_desc(pkg, out):
    if pkg.description:
        out.write_description(pkg.description)
    if pkg.tags:
        out.write_paragraph()
        out.write_text("Keywords: %s" % " ".join(pkg.tags))


def _split_models(guildfile):
    anon = None
    named = []
    for m in _sorted_models(guildfile.models):
        if m.name:
            named.append(m)
        else:
            anon = m
    return anon, named


def _write_anon_model_operations(m, out):
    if m.description:
        out.write_description(m.description)
        out.write_paragraph()
    _gen_write_operations(m.operations, out)


def _gen_write_operations(operations, out):
    prev_op = None
    for op in operations:
        if op.name[:1] == "_":
            continue
        if prev_op:
            out.write_paragraph()
        _write_operation(op, out)
        prev_op = op


def _write_models(models, out):
    i = 0
    for m in models:
        if i > 0:
            out.write_paragraph()
        _write_model(m, out)
        i += 1


def _sorted_models(models):
    def sort_key(m):
        if m.name[:1] == "_":
            return "\xff" + m.name
        return m.name

    return sorted(models.values(), key=sort_key)


def _write_model(m, out):
    out.write_heading(m.name)
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
        _gen_write_operations(m.operations, out)
    else:
        out.write_text("No operations defined for this model")
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
    return [(flag.name, _format_flag_desc(flag, max_flag_len)) for flag in flags]


def _format_flag_desc(flag, max_flag_len):
    lines = flag.description.split("\n")
    if flag.default is not None:
        fmt_default = flag_util.encode_flag_val(flag.default)
        line1_suffix = "(default is %s)" % fmt_default
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
        return "\n\n".join(lines)
    else:
        return lines[0]


def _format_flag_choices(choices, max_flag_len):
    out = click_util.ClickBaseHelpFormatter()
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
        [
            (
                flag_util.encode_flag_val(choice.alias or choice.value),
                "\n\n".join(choice.description.strip().split("\n")),
            )
            for choice in choices
        ],
        preserve_paragraphs=True,
    )
    out.dedent()


def _format_flag_choices_value_list(choices, out):
    out.write_dl([("Choices:", _format_choice_list(choices))])


def _format_choice_list(choices):
    vals = [c.alias or c.value for c in choices]
    fmt_vals = flag_util.encode_flag_val(vals)
    return _strip_list_brackets(fmt_vals)


def _strip_list_brackets(fmt_vals):
    if fmt_vals[:1] == "[" and fmt_vals[-1:] == "]":
        return fmt_vals[1:-1]
    return fmt_vals


def flag_edit_help(flagdef):
    lines = []
    if flagdef.description:
        lines.append(flagdef.description.split("\n", 1)[0])
    if flagdef.choices:
        lines.append("Choices: %s" % _format_choice_list(flagdef.choices))
    return "\n".join(lines)


def _format_flag_choices_for_edit(choices):
    choices_help = _format_flag_choices(choices, 0)
    return choices_help.replace("\b", "").strip()


def _write_references(refs, out):
    out.write_subheading("References")
    out.write_paragraph()
    out.indent()
    for ref in refs:
        out.write_text("\b\n- %s" % ref)
    out.dedent()


def print_model_help(modeldef):
    out = click_util.ClickBaseHelpFormatter()
    out.write_usage(
        "guild", "run [OPTIONS] {}:OPERATION [FLAG]...".format(modeldef.name)
    )
    if modeldef.description:
        out.write_paragraph()
        out.write_text(modeldef.description.replace("\n", "\n\n"))
    out.write_paragraph()
    out.write_text(
        "Use 'guild run {}:OPERATION --help-op' for help on "
        "a particular operation.".format(modeldef.name)
    )
    ops = _format_model_ops_dl(modeldef)
    if ops:
        _write_dl_section("Operations", ops, out)
    resources = _format_model_resources_dl(modeldef)
    if resources:
        _write_dl_section("Resources", resources, out)
    click.echo(out.getvalue(), nl=False)


def _format_model_ops_dl(modeldef):
    line1 = lambda s: s.split("\n")[0]
    return [(op.name, line1(op.description or "")) for op in modeldef.operations]


def _format_model_resources_dl(modeldef):
    return [(res.name, res.description) for res in modeldef.resources]


def _write_dl_section(name, dl, out):
    out.write_paragraph()
    out.write_heading(name)
    out.indent()
    out.write_dl(dl, preserve_paragraphs=True)
    out.dedent()


def print_op_help(opdef):
    out = click_util.ClickBaseHelpFormatter()
    out.write_usage("guild", "run [OPTIONS] {} [FLAG]...".format(opdef.fullname))
    if opdef.description:
        out.write_paragraph()
        out.write_text(opdef.description.replace("\n", "\n\n"))
    out.write_paragraph()
    out.write_text("Use 'guild run --help' for a list of options.")
    deps = _format_op_deps_dl(opdef)
    if deps:
        _write_dl_section("Dependencies", deps, out)
    flags = _format_op_flags_dl(opdef)
    if flags:
        _write_dl_section("Flags", flags, out)
    click.echo(out.getvalue(), nl=False)


def _format_op_deps_dl(opdef):
    model_resources = {
        res.name: res.description or "" for res in opdef.modeldef.resources
    }
    formatted = [
        (dep.spec, _dep_description(dep, model_resources)) for dep in opdef.dependencies
    ]
    # Show only deps that have descriptions (implicit user interface)
    return [item for item in formatted if item[1]]


def _dep_description(dep, model_resources):
    return dep.description or model_resources.get(dep.spec) or ""


def _format_op_flags_dl(opdef):
    seen = set()
    flags = []
    for flag in opdef.flags:
        if flag.name in seen:
            continue
        seen.add(flag.name)
        flags.append(flag)
    return flags_dl(flags)
