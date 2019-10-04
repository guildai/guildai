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

import logging
import os
import sys

from guild import cli
from guild import cmd_impl_support
from guild import help as helplib
from guild import op2 as oplib
from guild import op_util2 as op_util
from guild import run as runlib
from guild import run_util
from guild import summary
from guild import util
from guild import var

log = logging.getLogger("guild")

###################################################################
# State
###################################################################

class State(object):

    def __init__(self, args, restart_run, opdef, flag_vals,
                 batch_files, stage):
        self.args = args
        self.restart_run = restart_run
        self.opdef = opdef
        self.flag_vals = flag_vals
        self.batch_files = batch_files
        self.stage = stage

def _state_for_args(args):
    restart_run = _state_restart_run(args.restart or args.start)
    opdef = _state_opdef(args, restart_run)
    assert opdef or restart_run
    flag_vals, batch_files = _state_split_flag_args(args.flags)
    stage = bool(args.stage or args.restage)
    return State(args, restart_run, opdef, flag_vals, batch_files, stage)

def _state_restart_run(restart):
    if not restart:
        return None
    return _run_for_spec(restart)

def _run_for_spec(spec):
    return util.find_apply([
        run_util.run_for_run_dir,
        run_util.marked_or_latest_run_for_opspec,
        one_run,
    ], spec)

def _state_opdef(args, restart_run):
    if args.opspec and restart_run:
        _opspec_and_restart_error()
    if restart_run:
        return op_util.run_opdef(restart_run)
    else:
        return _opdef_for_opspec(args.opspec)

def _opdef_for_opspec(opspec):
    try:
        return op_util.opdef_for_opspec(opspec)
    except op_util.InvalidOpSpec:
        _invalid_opspec_error(opspec)
    except op_util.CwdGuildfileError as e:
        _guildfile_error(e.path, str(e))
    except op_util.NoSuchModel as e:
        _no_such_model_op_error(opspec)
    except op_util.MultipleMatchingModels as e:
        _multiple_models_error(e.model_ref, e.matches)
    except op_util.NoSuchOperation as e:
        _no_such_opdef_error(e.model, e.op_name)

def _state_split_flag_args(flag_args):
    batch_files, rest_args = op_util.split_batch_files(flag_args)
    assigns = _parse_assigns(rest_args)
    return assigns, batch_files

def _parse_assigns(assign_args):
    try:
        return op_util.parse_flag_assigns(assign_args)
    except op_util.ArgValueError as e:
        _invalid_flag_arg_error(e.arg)

###################################################################
# Main
###################################################################

def main(args):
    S = _init_state(args)
    op = _init_op(S)
    _dispatch_op(op, S)

def _init_state(args):
    _maybe_shift_opspec(args)
    _validate_args(args)
    return _state_for_args(args)

def _maybe_shift_opspec(args):
    """Moves opspec to flags if it looks like a flag assignment.
    """
    if args.opspec and "=" in args.opspec:
        args.flags = (args.opspec,) + args.flags
        args.opspec = None

def _validate_args(args):
    _check_incompatible_options(args)
    _check_opspec_and_restart(args)

def _check_incompatible_options(args):
    incompatible = [
        ("minimize", "maximize"),
        ("no_gpus", "gpus"),
        ("optimize", "optimizer"),
        ("print_trials", "init_trials"),
        ("remote", "background"),
        ("remote", "pidfile"),
        ("rerun", "restart"),
        ("rerun", "start"),
        ("run_dir", "restage"),
        ("run_dir", "restart"),
        ("run_dir", "start"),
        ("start", "restart"),
        ("stage", "background"),
        ("stage", "pidfile"),
        ("stage", "restage"),
    ]
    for a, b in incompatible:
        if getattr(args, a) and getattr(args, b):
            _incompatible_options_error(a, b)

def _check_opspec_and_restart(args):
    if args.opspec and args.restart:
        _opspec_and_restart_error()
    elif args.opspec and args.start:
        _opspec_and_restart_error("start")

###################################################################
# Init op
###################################################################

def _init_op(S):
    if S.opdef:
        return _op_from_opdef(S)
    else:
        assert S.restart_run
        return oplib.from_run(S.restart_run)

def _op_from_opdef(S):
    try:
        op = oplib.from_opdef(
            S.opdef,
            S.flag_vals,
            stage=S.stage,
            gpus=S.args.gpus,
        )
        _apply_op_label(S, op)
        return op
    except oplib.InvalidOpDef as e:
        _invalid_opdef_error(S.opdef, str(e))

def _apply_op_label(S, op):
    label_template = _label_template(S.args, S.opdef, S.flag_vals)
    if label_template is None:
        return None
    op.label = op_util.format_label(label_template, op.flag_vals)

def _label_template(args, opdef, flag_vals):
    return util.find_apply([
        lambda: args.label,
        lambda: opdef and opdef.label,
        lambda: _default_label(flag_vals),
    ])

def _default_label(flag_vals):
    if not flag_vals:
        return None
    return op_util.flags_desc(flag_vals, truncate_floats=True, delim=" ")

###################################################################
# Dispatch op
###################################################################

def _dispatch_op(op, S):
    if S.args.help_model:
        _print_model_help(S)
    elif S.args.help_op:
        _print_op_help(S)
    elif S.args.test_output_scalars:
        _test_output_scalars(S)
    elif S.args.test_sourcecode:
        _test_sourcecode(S)
    else:
        _dispatch_op_cmd(op, S)

###################################################################
# Model / op help
###################################################################

def _print_model_help(S):
    if not S.opdef:
        assert S.restart_run
        _restart_run_help_error(S.opdef.full_name, S.restart_run)
    helplib.print_model_help(S.opdef.modeldef)

def _print_op_help(S):
    if not S.opdef:
        assert S.restart_run
        _restart_run_help_error(S.opdef.full_name, S.restart_run)
    helplib.print_op_help(S.opdef)

###################################################################
# Test output scalars
###################################################################

class TestOutputLogger(summary.TestOutputLogger):

    @staticmethod
    def line(line):
        cli.out(line)

    def pattern_no_matches(self, pattern):
        msg = self._format_pattern_no_matches(pattern)
        cli.out(cli.style(msg, dim=True))

    def pattern_matches(self, pattern, matches, vals):
        msg = self._format_pattern_matches(pattern, matches, vals)
        cli.out(cli.style(msg, fg="yellow"))

def _test_output_scalars(S):
    output_scalars = S.opdef.output_scalars or oplib.DEFAULT_OUTPUT_SCALARS
    input_path = S.args.test_output_scalars
    logger = TestOutputLogger()
    if input_path == "-" and sys.stdin.isatty():
        cli.note(
            "Type patterns and press Enter to test. "
            "Use Ctrl-c or empty line to exit.")
    with _open_output(input_path) as f:
        summary.test_output(f, output_scalars, logger)

def _open_output(path):
    if path == "-":
        return util.StdinReader()
    try:
        return open(path, "r")
    except (IOError, OSError) as e:
        if e.errno == 2:
            cli.error("%s does not exist" % path)
        else:
            cli.error("error opening %s: %s" % (path, e))

###################################################################
# Test source code
###################################################################

def _test_sourcecode(S):
    if not S.opdef:
        _missing_opdef_error("cannot test source code copy")
    logger = _CopyLogger()
    sourcecode_src = S.opdef.guildfile.dir
    sourcecode_select = op_util.sourcecode_select_for_opdef(S.opdef)
    op_util.copy_sourcecode(
        sourcecode_src,
        sourcecode_select,
        None,
        handler_cls=logger.handler_cls)
    cli.out("Copying from %s" % cmd_impl_support.cwd_desc(logger.root))
    cli.out("Rules:")
    for rule in logger.select.rules:
        cli.out("  %s" % _format_file_select_rule(rule))
    if logger.select.disabled:
        assert not logger.selected, logger.selected
        assert not logger.skipped, logger.skipped
        cli.out("Source code copy disabled")
    else:
        cli.out("Selected for copy:")
        for path in logger.selected:
            cli.out(cli.style("  %s" % path, fg="yellow"))
        cli.out("Skipped:")
        for path in logger.skipped:
            cli.out(cli.style("  %s" % path, dim=True))

def _format_file_select_rule(rule):
    parts = ["include" if rule.result else "exclude"]
    if rule.type:
        parts.append(rule.type)
    parts.append(", ".join([repr(p) for p in rule.patterns]))
    extras = _format_file_select_rule_extras(rule)
    if extras:
        parts.append("(%s)" % extras)
    return " ".join(parts)

def _format_file_select_rule_extras(rule):
    parts = []
    if rule.regex:
        parts.append("regex")
    if rule.sentinel:
        parts.append("with %r" % rule.sentinel)
    if rule.size_gt:
        parts.append("size > %s" % rule.size_gt)
    if rule.size_lt:
        parts.append("size < %s" % rule.size_lt)
    if rule.max_matches:
        parts.append("max match %s" % rule.max_matches)
    return ", ".join(parts)

class _CopyLogger(object):

    root = None
    select = None

    def __init__(self):
        self.selected = []
        self.skipped = []

    def handler_cls(self, src_root, dest_root, select):
        assert dest_root is None, dest_root
        self.root = os.path.relpath(src_root)
        self.select = select
        return self

    def copy(self, path, _results):
        self.selected.append(os.path.join(self.root, path))

    def ignore(self, path, _results):
        self.skipped.append(os.path.join(self.root, path))

###################################################################
# Dispatch op command
###################################################################

def _dispatch_op_cmd(op, S):
    if S.args.print_cmd or S.args.print_env:
        _print_op_cmd_env(op, S)
    elif S.args.print_trials or S.args.save_trials:
        assert False, "TODO"
        #_print_or_save_trials(op, args)
    else:
        _confirm_and_run_op(op, S)

def _print_op_cmd_env(op, S):
    if S.args.print_cmd:
        _print_op_cmd(op)
    if S.args.print_env:
        _print_op_env(op)

###################################################################
# Print op info
###################################################################

def _print_op_cmd(op):
    formatted = " ".join(_preview_cmd(op))
    cli.out(formatted)

def _preview_cmd(op):
    return [util.shlex_quote(arg) for arg in op.cmd_args]

def _print_op_env(op):
    for name, val in sorted((op.cmd_env or {}).items()):
        cli.out("export %s=%s" % (name, val))

###################################################################
# Run op
###################################################################

def _confirm_and_run_op(op, S):
    if S.args.yes or _confirm_run(op):
        _run_op(op)

def _confirm_run(op):
    prompt = (
        "You are about to {action} {op}\n"
        "{flags}"
        "Continue?"
        .format(**op_util.preview_op_kw(op))
    )
    return cli.confirm(prompt, default=True)

def _run_op(op):
    _run, exit_status = oplib.run(op)
    if exit_status != 0:
        cli.error(exit_status=exit_status)

###################################################################
# Error handlers
###################################################################

def _incompatible_options_error(a, b):
    cli.error(
        "--%s and --%s cannot both be used\n"
        "Try 'guild run --help' for more information."
        % (a.replace("_", "-"), b.replace("_", "-")))

def _opspec_and_restart_error(option="restart"):
    cli.error(
        "OPERATION cannot be used with --%s\n"
        "Try 'guild run --help' for more information." % option)

def _invalid_opspec_error(opspec):
    cli.error(
        "invalid operation spec '%s'\n"
        "Try 'guild operations' for a list of available operations."
        % opspec)

def _no_such_opspec_error(opspec):
    if opspec:
        if ":" in opspec:
            cli.error(
                "cannot find operation %s\n"
                "Try 'guild operations' for a list of available operations."
                % opspec)
        else:
            cli.error(
                "cannot find operation %s\n"
                "You may need to include a model in the form MODEL:OPERATION. "
                "Try 'guild operations' for a list of available operations."
                % opspec)
    else:
        cli.error(
            "cannot find a default operation\n"
            "Try 'guild operations' for a list.")

def _guildfile_error(gf_path, msg):
    log.error(msg)
    cli.error(
        "guildfile in %s contains an error (see above for details)"
        % cmd_impl_support.cwd_desc(os.path.dirname(gf_path)))

def _no_such_model_op_error(opspec):
    if opspec:
        if ":" in opspec:
            cli.error(
                "cannot find operation %s\n"
                "Try 'guild operations' for a list of available operations."
                % opspec)
        else:
            cli.error(
                "cannot find operation %s\n"
                "You may need to include a model in the form MODEL:OPERATION. "
                "Try 'guild operations' for a list of available operations."
                % opspec)
    else:
        cli.error(
            "cannot find a default operation\n"
            "Try 'guild operations' for a list.")

def _multiple_models_error(model_ref, models):
    models_list = "\n".join([
        "  %s" % name
        for name in sorted([m.fullname for m in models])
    ])
    cli.error(
        "there are multiple models that match '%s'\n"
        "Try specifying one of the following:\n"
        "%s"
        % (model_ref, models_list))

def _no_such_opdef_error(model, op_name):
    if model.name:
        cli.error(
            "operation '{op}' is not defined for model '{model}'\n"
            "Try 'guild operations {model}' for a list of available "
            "operations."
            .format(op=op_name, model=model.name))
    else:
        cli.error(
            "operation '{op}' is not defined\n"
            "Try 'guild operations' for a list of available operations."
            .format(op=op_name))

def _invalid_flag_arg_error(arg):
    cli.error("invalid argument '%s' - expected NAME=VAL" % arg)

def _invalid_opdef_error(opdef, msg):
    cli.error(
        "invalid setting for operation '%s': %s"
        % (opdef.fullname, msg))

def _restart_run_help_error(op_name, restart_run):
    cli.error(
        "help is not available for '%s' (run %s)"
        % (op_name, restart_run.id))

def _missing_opdef_error(msg):
    cli.error("%s - missing operation definition" % msg)

###################################################################
# Cmd impl API
###################################################################

def one_run(run_id_prefix):
    runs = [
        runlib.Run(id, path)
        for id, path in var.find_runs(run_id_prefix)
    ]
    return cmd_impl_support.one_run(runs, run_id_prefix)
