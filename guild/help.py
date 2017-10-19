import os
import textwrap

import click

class ConsoleFormatter(click.HelpFormatter):

    def write_section(self, val):
        self.write_text(click.style(val, bold=True))

    def write_heading(self, val):
        self.write_text(click.style(val, bold=True))

    def write_subheading(self, val):
        self.write_text("%s:" % val)

    def write_description(self, val):
        self.write_text(val)

class RestFormatter(click.HelpFormatter):

    def write_section(self, val):
        self.write_text(val)
        self.write_text("=" * len(val))

    def write_heading(self, val):
        self.write_text(val)
        self.write_text("-" * len(val))

    def write_subheading(self, val):
        self.write_text(val)
        self.write_text("." * len(val))

    def write_description(self, val):
        self.write_text("*%s*" % val)

    def write_dl(self, rows):
        for name, desc in rows:
            self.write_text("**%s**" % name)
            super(RestFormatter, self).indent()
            self.write_text(desc)
            super(RestFormatter, self).dedent()
            self.write_paragraph()

    def indent(self):
        pass

    def dedent(self):
        pass

def models_console_help(models):
    out = ConsoleFormatter()

    def _write_section(name, writer):
        out.write_section(name)
        out.write_paragraph()
        out.indent()
        writer(models, out)
        out.dedent()

    _write_section("OVERVIEW", _write_console_help_overview)
    out.write_paragraph()
    _write_section("MODELS", _write_models)

    return "".join(out.buffer)

def _write_console_help_overview(models, out):
    out.write_text(textwrap.dedent(
        """

        You are viewing help models defined in %s.

        To run an operation, use 'guild run MODEL:OPERATION' where
        MODEL is one of the model names listed below and OPERATION is
        an associated operation.

        You may set operation flags using 'FLAG=VALUE' arguments to
        the run command.

        For more help, try 'guild run --help' or 'guild --help'.

        """
        % _format_models_src(models.src)))

def _format_models_src(path):
    relpath = os.path.relpath(path)
    if relpath[0] != '.':
        relpath = os.path.join(".", relpath)
    return relpath

def package_description(models, modelfile_url=None):
    out = RestFormatter()
    _write_models(models, out)
    return "".join(out.buffer)

def _write_models(models, out):
    for model in models:
        out.write_paragraph()
        _write_model(model, out)

def _write_model(m, out):
    out.write_heading(m.name)
    out.indent()
    if m.description:
        out.write_paragraph()
        out.write_description(m.description)
    out.write_paragraph()
    _write_operations(m, out)
    out.write_paragraph()
    _write_flags(m, out)
    out.dedent()

def _write_operations(m, out):
    out.write_subheading("Operations")
    out.write_paragraph()
    out.indent()
    if m.operations:
        out.write_dl([
            (op.name, op.description or "")
            for op in m.operations])
    else:
        out.write_text("There are no operations defined for this model.")
    out.dedent()

def _write_flags(m, out):
    out.write_subheading("Flags")
    out.write_paragraph()
    out.indent()
    if m.flags:
        out.write_dl([
            (flag.name, _flag_desc(flag))
            for flag in m.flags])
    else:
        out.write_text("There are no flags defined for this model.")
    out.dedent()

def _flag_desc(flag):
    desc = flag.description or ""
    if flag.value is None:
        return desc
    else:
        return "%s (default is %s)" % (desc, flag.value)

"""
def package_description(models, modelfile_url=None):
    out = click.HelpFormatter()
    for i, model in enumerate(models):
        if i > 0:
            out.write_paragraph()
        _pkg_desc_model(model, out)
    return "".join(out.buffer)

def _pkg_desc_model(m, out):
    _pkg_desc_heading(m.name, out)
    if m.description:
        out.write_paragraph()
        out.write_text("*%s*" % m.description)

def _pkg_desc_heading(val, out):
    out.write_text(val)
    out.write_text("=" * len(val))


def package_description(models, modelfile=None):
    out = []
    for model in models:
        out.extend(_rst_model_title(model))
        out.extend(_rst_model_description(model))
        out.extend(_rst_model_ops(model))
        out.extend(_rst_model_flags(model))
    out.extend(_rst_package_epilogue(modelfile))
    return "\n".join(out)

def _rst_model_title(m):
    return _rst_heading(m.name, "=")

def _rst_heading(val, char):
    return [val, char * len(val), ""]

def _rst_model_description(m):
    if not m.description:
        return []
    return [_rst_em(m.description), ""]

def _rst_model_ops(m):
    out = []
    out.extend(_rst_heading("Operations", "-"))
    if m.operations:
        for op in m.operations:
            out.extend(_rst_op(op))
    else:
        out.append(_rst_em("There are no operations defined for this model."))
    return out

def _rst_op(op):
    return _rst_deflist_item(
        _rst_strong(op.name),
        op.description)

def _rst_model_flags(m):
    out = []
    out.extend(_rst_heading("Flags", "-"))
    if m.flags:
        for flag in m.flags:
            out.extend(_rst_flag(flag))
    else:
        out.append(_rst_em("There are no flags defined for this model."))
    return out

def _rst_flag(flag):
    val = flag.value if flag.value is not None else "No default value"
    return _rst_deflist_item(
        "%s (%s)" % (_rst_strong(flag.name), val),
        flag.description or "No description")

def _rst_package_epilogue(modelfile):
    if not modelfile:
        return []
    return [
        "----",
        "Modelfile: %s" % modelfile
    ]

def _rst_em(val):
    return "*%s*" % val

def _rst_strong(val):
    return "**%s**" % val

def _rst_deflist_item(name, value):
    return [name, "  %s" % value, ""]
"""
