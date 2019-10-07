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

import six

from guild import cli
from guild import cmd_impl_support
from guild import config
from guild import flag_util
from guild import guildfile
from guild import help as helplib
from guild import op2 as oplib
from guild import op_dep
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
                 batch_files, stage, run_dir, extra_run_attrs,
                 batch_opdef, batch_flag_vals):
        self.args = args
        self.restart_run = restart_run
        self.opdef = opdef
        self.flag_vals = flag_vals
        self.batch_files = batch_files
        self.stage = stage
        self.run_dir = run_dir
        self.extra_run_attrs = extra_run_attrs
        self.batch_opdef = batch_opdef
        self.batch_flag_vals = batch_flag_vals

def _state_for_args(args):
    restart_run = _state_restart_run(args.restart or args.start)
    opdef = _state_opdef(args, restart_run)
    decoded_flag_args, batch_files = _state_split_flag_args(args.flags)
    flag_vals = _flag_vals_from_decoded(decoded_flag_args, opdef, args)
    if restart_run:
        _apply_restart_run_flags(restart_run, flag_vals)
    stage = args.stage
    run_dir = _state_run_dir(args, restart_run)
    extra_run_attrs = _state_extra_run_attrs(args)
    batch_opdef = _state_batch_opdef(args, flag_vals, restart_run)
    batch_flag_vals = _state_batch_flag_vals(args)
    return State(args, restart_run, opdef, flag_vals, batch_files,
                 stage, run_dir, extra_run_attrs, batch_opdef,
                 batch_flag_vals)

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

# =================================================================
# State - op def
# =================================================================

def _state_opdef(args, restart_run):
    if restart_run:
        opdef = _opdef_for_run(restart_run)
        if not opdef:
            _check_restart_args_for_missing_opdef(args, restart_run)
        return opdef
    else:
        return _opdef_for_opspec(args.opspec)

def _opdef_for_run(run):
    opspec = run.opref.to_opspec()
    try:
        return op_util.opdef_for_opspec(opspec)
    except op_util.OpDefLookupError as e:
        log.debug(
            "error finding definition for '%s' for run %s (%s): %s",
            opspec, run.id, run.dir, e)
        return None
    except Exception as e:
        if log.getEffectiveLevel() <= 20:
            log.exception(
                "getting opdef for '%s' for run %s (%s)",
                opspec, run.id, run.dir)
        log.warning(
            "error loading definition for '%s' for run %s: %s",
            opspec, run.id, e)
        return None

def _check_restart_args_for_missing_opdef(args, restart_run):
    if args.flags:
        _flags_with_missing_opdef_error(restart_run)

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
    except op_util.ModelOpProxyError as e:
        _model_op_proxy_error(e)

# =================================================================
# State - flag vals
# =================================================================

def _state_split_flag_args(flag_args):
    batch_files, rest_args = op_util.split_batch_files(flag_args)
    assigns = _parse_assigns(rest_args)
    return assigns, batch_files

def _parse_assigns(assign_args):
    try:
        return op_util.parse_flag_assigns(assign_args)
    except op_util.ArgValueError as e:
        _invalid_flag_arg_error(e.arg)

def _flag_vals_from_decoded(arg_decoded_flag_vals, opdef, args):
    if not arg_decoded_flag_vals:
        return arg_decoded_flag_vals
    assert opdef, "flag args not allowed without an opdef"
    opdef_coerced_flag_vals = _coerce_flags(
        arg_decoded_flag_vals, opdef.flags)
    resource_flagdef_proxies = _resource_flagdef_proxies(
        opdef, opdef_coerced_flag_vals)
    final_coerced_flag_vals = _coerce_flags(
        opdef_coerced_flag_vals, resource_flagdef_proxies)
    if not args.force_flags:
        _check_no_such_flags(
            final_coerced_flag_vals,
            opdef.flags + resource_flagdef_proxies,
            opdef)
        _validate_flag_vals(final_coerced_flag_vals, opdef)
    return final_coerced_flag_vals

def _coerce_flags(flag_vals, flagdefs):
    flagdef_lookup = {
        flagdef.name: flagdef
        for flagdef in flagdefs
    }
    return {
        name: _coerce_flag_val(name, val, flagdef_lookup)
        for name, val in flag_vals.items()
    }

def _coerce_flag_val(name, val, flagdefs):
    flagdef = flagdefs.get(name)
    if not flagdef:
        return val
    try:
        return op_util.coerce_flag_value(val, flagdef)
    except (ValueError, TypeError) as e:
        _coerce_flag_val_error(val, name, e)

def _resource_flagdef_proxies(opdef, flag_vals):
    return [
        _ResourceFlagDefProxy(resource_spec, opdef)
        for resource_spec in _resource_specs(opdef, flag_vals)
    ]

def _ResourceFlagDefProxy(name, opdef):
    data = {
        "arg-skip": True,
        "type": "string",
    }
    return guildfile.FlagDef(name, data, opdef)

def _resource_specs(opdef, flag_vals):
    return [
        util.resolve_refs(dep.name, flag_vals, undefined=None)
        for dep in opdef.dependencies
    ]

def _check_no_such_flags(flag_vals, flagdefs, opdef):
    flagdef_names = set([flagdef.name for flagdef in flagdefs])
    for name in flag_vals:
        if name not in flagdef_names:
            _no_such_flag_error(name, opdef)

def _validate_flag_vals(flag_vals, opdef):
    try:
        op_util.validate_flag_vals(flag_vals, opdef)
    except op_util.MissingRequiredFlags as e:
        _missing_required_flags_error(e)
    except op_util.InvalidFlagChoice as e:
        _invalid_flag_choice_error(e)
    except op_util.InvalidFlagValue as e:
        _invalid_flag_value_error(e)

def _apply_restart_run_flags(restart_run, flag_vals):
    restart_run_flags = restart_run.get("flags") or {}
    for name in restart_run_flags:
        if name not in flag_vals:
            flag_vals[name] = restart_run_flags[name]

# =================================================================
# State - run dir
# =================================================================

def _state_run_dir(args, restart_run):
    if restart_run:
        return restart_run.dir
    elif args.run_dir:
        run_dir = os.path.abspath(args.run_dir)
        if os.getenv("NO_WARN_RUNDIR") != "1":
            cli.note(
                "Run directory is '%s' (results will not be "
                "visible to Guild)" % run_dir)
        return run_dir
    else:
        return None

# =================================================================
# State - extra run attrs
# =================================================================

def _state_extra_run_attrs(args):
    attrs = {}
    _apply_attr_run_params(args, attrs)
    _apply_attr_random_seed(args, attrs)
    _apply_attr_system_info(attrs)
    _apply_attr_max_trials(args, attrs)
    return attrs

def _apply_attr_run_params(args, attrs):
    params = args.as_kw()
    if args.stage:
        attrs["stage_params"] = params
    else:
        attrs["run_params"] = params

def _apply_attr_random_seed(args, attrs):
    attrs["random_seed"] = _random_seed(args)

def _random_seed(args):
    if args.random_seed is not None:
        return args.random_seed
    return runlib.random_seed()

def _apply_attr_system_info(attrs):
    attrs["host"] = util.hostname()
    attrs["user"] = util.user()
    attrs["platform"] = util.platform_info()

def _apply_attr_max_trials(args, attrs):
    if args.max_trials:
        attrs["max_trials"] = args.max_trials

# =================================================================
# State - batch op def
# =================================================================

def _state_batch_opdef(args, flag_vals, restart_run):
    ##assert False, "TODO: should flag_vals be just decoded or should they be coerced/validated"
    if restart_run:
        opdef = _batch_opdef_for_run(restart_run)
        if not opdef:
            _check_restart_args_for_missing_batch_opdef(args, restart_run)
        return opdef
    else:
        return _batch_opdef_for_args(args, flag_vals)

def _batch_opdef_for_run(_run):
    # TODO
    return None

def _check_restart_args_for_missing_batch_opdef(_args, _restart_run):
    # TODO
    pass

def _batch_opdef_for_args(args, decoded_flag_args):
    optimizer_opspec = _optimizer_opspec_for_args(args, decoded_flag_args)
    if optimizer_opspec:
        return _opdef_for_opspec(optimizer_opspec)
    return None

def _optimizer_opspec_for_args(args, decoded_flag_args):
    if args.optimizer:
        return args.optimizer
    return _implied_optimizer_from_flags(decoded_flag_args)

def _implied_optimizer_from_flags(flag_vals):
    return (
        _any_random_functions(flag_vals) and "random"
        or _any_lists(flag_vals) and "+" or None)

def _any_random_functions(flag_vals):
    return any((_is_random_function(val) for val in flag_vals.values()))

def _is_random_function(val):
    try:
        name, _args = flag_util.decode_flag_function(val)
    except ValueError:
        return False
    else:
        return name in (None, "uniform", "loguniform")

def _any_lists(flag_vals):
    return any((isinstance(val, list) for val in flag_vals.values()))

def _state_batch_flag_vals(args):
    return _parse_assigns(args.opt_flags)

###################################################################
# Main
###################################################################

def main(args):
    S = _init_state(args)
    op = _init_op(S)
    _validate_op(op, S)
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
    _check_incompatible_with_restart(args)

def _check_incompatible_options(args):
    incompatible = [
        ("minimize", "maximize"),
        ("no_gpus", "gpus"),
        ("optimize", "optimizer"),
        ("print_trials", "init_trials"),
        ("remote", "background"),
        ("remote", "pidfile"),
        ("stage", "background"),
        ("stage", "pidfile"),
        ("stage", "restart"),
        ("stage", "start"),
        ("start", "restart"),
    ]
    for a, b in incompatible:
        if getattr(args, a) and getattr(args, b):
            _incompatible_options_error(a, b)

def _check_incompatible_with_restart(args):
    if not (args.start or args.restart):
        return
    incompatible = [
        ("opspec", "OPERATION"),
        ("run_dir", "--run-dir"),
        ("rerun", "--rerun"),
        ("help_model", "--help-model"),
        ("help_op", "--help-op"),
        ("test_sourcecode", "--test-sourcecode"),
        ("test_output_scalars", "--test-output-scalars"),
    ]
    for name, desc in incompatible:
        if getattr(args, name):
            restart_option = "restart" if args.restart else "start"
            _incompatible_with_restart_error(desc, restart_option)

###################################################################
# Init op
###################################################################

def _init_op(S):
    if S.opdef:
        return _op_from_opdef(S)
    else:
        assert S.restart_run
        return _op_from_restart_run(S)

def _op_from_opdef(S):
    assert S.opdef
    try:
        op = oplib.from_opdef(
            S.opdef,
            S.flag_vals,
            run_dir=S.run_dir,
            stage=S.stage,
            extra_run_attrs=S.extra_run_attrs,
            gpus=S.args.gpus,
        )
        _apply_op_label(S, op)
        _apply_op_restart_run(S, op)
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

def _apply_op_restart_run(S, op):
    if S.restart_run:
        # Disable source code copy if restarting. Restarted runs must
        # always use their original source code.
        op.sourcecode_src = None
        op.sourcecode_select = None

def _op_from_restart_run(S):
    return oplib.from_run(
        S.restart_run,
        label=S.args.label,
        extra_run_attrs=S.extra_run_attrs,
        gpus=S.args.gpus)

def _apply_opdef_to_restart_op(S, restart_op):
    opdef_op = _op_from_opdef(S)
    op_util.apply_flags_to_restart_op(opdef_op, restart_op)

def _validate_op(op, S):
    if S.restart_run:
        assert op.opref.to_opspec() == S.restart_run.opref.to_opspec()
        assert op.run_dir == S.restart_run.dir
        # Important that we NOT modify sourcecode for a restart.
        assert op.sourcecode_src is None
        assert op.sourcecode_select is None

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
    assert S.opdef
    helplib.print_model_help(S.opdef.modeldef)

def _print_op_help(S):
    assert S.opdef
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
    assert S.opdef
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
    assert S.opdef
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
        parts.append(extras)
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
    if S.args.yes or _confirm_run(op, S):
        _run_op(op, S)

def _confirm_run(op, S):
    action = _preview_op_action(S)
    subject = _preview_op_subject(op, S)
    flags = _preview_flags(op)
    prompt = (
        "You are about to {action} {subject}\n"
        "{flags}"
        "Continue?"
        .format(action=action,
                subject=subject,
                flags=flags)
    )
    return cli.confirm(prompt, default=True)

def _preview_op_action(S):
    if S.args.stage:
        return "stage"
    elif S.args.start:
        return "start"
    elif S.args.restart:
        return "restart"
    else:
        return "run"

def _preview_op_subject(op, S):
    op_desc = _preview_op_desc(op)
    if S.restart_run:
        return "%s (%s)" % (S.restart_run.id, op_desc)
    else:
        return op_desc

def _preview_op_desc(op):
    opspec = op.opref.to_opspec()
    if os.path.isabs(opspec):
        opspec = os.path.relpath(opspec, config.cwd())
    return opspec

def _preview_flags(op, indent=2):
    if not op.flag_vals:
        return ""
    return "\n".join([
        " " * indent +_format_flag(name, val, op.flag_null_labels)
        for name, val in sorted(op.flag_vals.items())
    ]) + "\n"

def _format_flag(name, val, null_labels):
    if val is None:
        formatted = _null_label(name, null_labels)
    else:
        formatted = util.find_apply([
            _try_format_function,
            flag_util.encode_flag_val], val)
    return "%s: %s" % (name, formatted)

def _try_format_function(val):
    if not isinstance(val, six.string_types):
        return None
    try:
        flag_util.decode_flag_function(val)
    except ValueError:
        return None
    else:
        return val

def _null_label(name, null_labels):
    null_label = null_labels.get(name, "default")
    return flag_util.encode_flag_val(null_label)

def _run_op(op, S):
    try:
        run, exit_status = oplib.run(op)
    except op_dep.OpDependencyError as e:
        _op_dependency_error(e)
    except oplib.ProcessError as e:
        _op_process_error(op, e)
    else:
        _handle_run_exit(run, exit_status, S)

def _handle_run_exit(run, exit_status, S):
    if exit_status != 0:
        cli.error(exit_status=exit_status)
    if S.stage:
        _print_staged_info(run, S)

def _print_staged_info(run, S):
    if S.args.run_dir:
        _print_staged_dir_instructions(run, S)
    else:
        _print_stage_pending_instructions(run, S)

def _print_staged_dir_instructions(run, S):
    cmd = " ".join([util.shlex_quote(arg) for arg in run.get("cmd") or []])
    cli.out(
        "{op} staged in '{dir}'\n"
        "To start the operation, use "
        "\"(cd '{dir}' && source .guild/ENV && {cmd})\""
        .format(
            op=S.opdef.fullname,
            dir=run.dir,
            cmd=cmd))

def _print_stage_pending_instructions(run, S):
    cli.out(
        "{op} staged as {run_id}\n"
        "To start the operation, use 'guild run --start {run_id}'"
        .format(
            op=S.opdef.fullname,
            run_id=run.id))

###################################################################
# Error handlers
###################################################################

def _incompatible_options_error(a, b):
    cli.error(
        "--%s and --%s cannot both be used\n"
        "Try 'guild run --help' for more information."
        % (a.replace("_", "-"), b.replace("_", "-")))

def _incompatible_with_restart_error(option, restart_option):
    cli.error(
        "%s cannot be used with --%s\n"
        "Try 'guild run --help' for more information."
        % (option, restart_option))

def _flags_with_restart_error(option="restart"):
    cli.error(
        "flags cannot be used with --%s\n"
        "Try 'guild run --help' for more information." % option)

def _invalid_opspec_error(opspec):
    cli.error(
        "invalid operation '%s'\n"
        "Try 'guild operations' for a list of available operations."
        % opspec)

def _guildfile_error(gf_path, msg):
    log.error(msg)
    cli.error(
        "guildfile in %s contains an error (see above for details)"
        % cmd_impl_support.cwd_desc(gf_path))

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
    op = (
        "operation '{0}'".format(op_name)
        if op_name else "a default operation")
    if model.name:
        cli.error(
            "{op} is not defined for model '{model}'\n"
            "Try 'guild operations {model}' for a list of available "
            "operations."
            .format(op=op, model=model.name))
    else:
        cli.error(
            "{op} is not defined for this project\n"
            "Try 'guild operations' for a list of available operations."
            .format(op=op))

def _invalid_flag_arg_error(arg):
    cli.error("invalid argument '%s' - expected NAME=VAL" % arg)

def _no_such_flag_error(name, opdef):
    cli.error(
        "unsupported flag '%s'\n"
        "Try 'guild run %s --help-op' for a list of "
        "flags or use --force-flags to skip this check."
        % (name, opdef.fullname))

def _coerce_flag_val_error(val, name, e):
    cli.error("cannot apply %r to flag '%s': %s" % (val, name, e))

def _missing_required_flags_error(e):
    cli.out(
        "Operation requires the following missing flags:\n",
        err=True)
    cli.table(
        [{"name": flag.name, "desc": flag.description}
         for flag in e.missing],
        ["name", "desc"],
        indent=2,
        err=True)
    cli.out(
        "\nRun the command again with these flags specified "
        "as NAME=VAL.", err=True)
    cli.error()

def _invalid_flag_choice_error(e):
    cli.out(
        "Unsupported value for '%s' - supported values are:\n"
        % e.flag.name, err=True)
    cli.table(
        [{"val": choice.value, "desc": choice.description}
         for choice in e.flag.choices],
        ["val", "desc"],
        indent=2,
        err=True)
    cli.out(
        "\nRun the command again using one of these options.",
        err=True)
    cli.error()

def _invalid_flag_value_error(e):
    cli.error("invalid value for %s: %s" % (e.flag.name, e.msg))

def _invalid_opdef_error(opdef, msg):
    cli.error(
        "invalid setting for operation '%s': %s"
        % (opdef.fullname, msg))

def _model_op_proxy_error(e):
    cli.error("cannot run '%s': %s" % (e.opspec, e.msg))

def _op_dependency_error(e):
    cli.error(
        "run failed because a dependency was not met: %s" % e)

def _op_process_error(op, e):
    cli.error("error running %s: %s" % (op.opref.to_opspec(), e))

def _flags_with_missing_opdef_error(restart_run):
    cli.error(
        "cannot set flags when restarting %s: configuration "
        "for operation '%s' is not available"
        % (restart_run.id, restart_run.opref.to_opspec()))

###################################################################
# Cmd impl API
###################################################################

def one_run(run_id_prefix):
    runs = [
        runlib.Run(id, path)
        for id, path in var.find_runs(run_id_prefix)
    ]
    return cmd_impl_support.one_run(runs, run_id_prefix)
