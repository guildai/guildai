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
from guild import click_util
from guild import cmd_impl_support
from guild import config
from guild import flag_util
from guild import guildfile
from guild import help as helplib
from guild import op2 as oplib
from guild import op_cmd as op_cmd_lib
from guild import op_dep
from guild import op_util2 as op_util
from guild import run as runlib
from guild import run_util
from guild import summary
from guild import util
from guild import var

log = logging.getLogger("guild")

# Use Bayesian with gaussian process as default optimizer when opdef
# does not contain any optimizers.
#
DEFAULT_OPTIMIZER = "gp"

###################################################################
# State
###################################################################

class State(object):

    def __init__(self, args):
        self.args = args
        self.restart_run = None
        self.user_op = Operation()
        self.batch_op = None

class Operation(oplib.Operation):

    def __init__(self):
        super(Operation, self).__init__()
        self._run = None
        self._opdef = None
        self._user_flag_vals = {}
        self._batch_trials = None
        self._op_flag_vals = {}
        self._flag_null_labels = {}
        self._op_cmd = None
        self._op_cmd_run_attrs = None
        self._python_requires = None
        self._random_seed = None
        self._label_template = None
        self._label = None
        self._output_scalars = None

def _state_for_args(args):
    S = State(args)
    _state_init_restart_run(S)
    _state_init_user_op(S)
    _state_init_batch_op(S)
    return S

def _op_config_data(op):
    return {
        "flag-null-labels": op._flag_null_labels,
        "op-cmd": op_cmd_lib.as_data(op._op_cmd),
        "python-requires": op._python_requires,
        "label-template": op._label_template,
        "output-scalars": op._output_scalars,
        "deps": op_util.op_deps_as_data(op.deps),
    }

def _apply_op_config_data(data, op):
    op._flag_null_labels = data.get("flag-null-labels")
    op._op_cmd = op_cmd_lib.for_data(data.get("op-cmd"))
    op._python_requires = data.get("python-requires")
    op._label_template = data.get("label-template")
    op._output_scalars = data.get("output-scalars")
    op.deps = op_util.op_deps_for_data(data.get("deps"))

# =================================================================
# State - restart run
# =================================================================

def _state_init_restart_run(S):
    restart = S.args.restart or S.args.start
    if restart:
        S.restart_run = _run_for_spec(restart)

def _run_for_spec(spec):
    return util.find_apply([
        run_util.run_for_run_dir,
        run_util.marked_or_latest_run_for_opspec,
        one_run,
    ], spec)

# =================================================================
# State - user op
# =================================================================

def _state_init_user_op(S):
    _user_op_init_run(S)
    _op_init_user_flags(S.args.flags, S.user_op)
    _op_init_opdef(S.args.opspec, S.user_op)
    _op_init_op_flags(S.args, S.user_op)
    _op_init_config(S.args.label, S.user_op)
    _op_init_core(S.args, S.user_op)

def _user_op_init_run(S):
    if S.restart_run:
        if S.restart_run.batch_proto:
            S.user_op._run = S.restart_run.batch_proto
        else:
            S.user_op._run = S.restart_run

# =================================================================
# Op - user flags
# =================================================================

def _op_init_user_flags(flag_args, op):
    op._user_flag_vals, batch_files = _split_flag_args(flag_args)
    if batch_files:
        op._batch_trials = _trials_for_batch_files(batch_files)

def _split_flag_args(flag_args):
    batch_files, rest_args = op_util.split_batch_files(flag_args)
    assigns = _parse_assigns(rest_args)
    return assigns, batch_files

def _parse_assigns(assign_args):
    try:
        return op_util.parse_flag_assigns(assign_args)
    except op_util.ArgValueError as e:
        _invalid_flag_arg_error(e.arg)

def _trials_for_batch_files(batch_files):
    batch_files = [_resolve_batch_file(path) for path in batch_files]
    try:
        return op_util.trials_for_batch_files(batch_files)
    except op_util.BatchFileError as e:
        _batch_file_error(e)

def _resolve_batch_file(path):
    resolved = os.path.join(config.cwd(), path)
    if not os.path.exists(resolved):
        _no_such_batch_file_error(resolved)
    return resolved

# =================================================================
# Op - opdef
# =================================================================

def _op_init_opdef(opspec, op):
    if op._run:
        assert not opspec
        # We want opdef for restart only when user specifies flag
        # values. Otherwise we want isolation from config.
        if op._user_flag_vals:
            op._opdef = _opdef_for_run(op._run)
    else:
        op._opdef = _opdef_for_opspec(opspec)

def _opdef_for_run(run):
    opspec = run.opref.to_opspec()
    return _opdef_for_opspec(opspec)

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
# Op - op flags
# =================================================================

def _op_init_op_flags(args, op):
    if op._run:
        _apply_run_flags(op._run, op._op_flag_vals)
    if op._opdef:
        _apply_op_flags_for_opdef(
            op._opdef,
            op._user_flag_vals,
            args.force_flags or op._batch_trials,
            op._op_flag_vals)

def _apply_run_flags(run, target):
    target.update(run.get("flags") or {})

def _apply_op_flags_for_opdef(opdef, user_flag_vals, force_flags, target):
    """Applies opdef and user-provided flags to target flag vals.

    Opdef is used to provide missing default values, coerce flag vals,
    and validate vals. Opdef-provided flag vals are added to target
    only if they are not already in target, or if they are in
    user-provided flags. This maintains existing values (e.g. from a
    restart) unless a user explicitly provides a flag value.
    """
    op_flag_vals = _flag_vals_for_opdef(opdef, user_flag_vals, force_flags)
    _apply_default_resolved_runs(opdef, op_flag_vals)
    for name, val in op_flag_vals.items():
        if name in user_flag_vals or name not in target:
            target[name] = val

def _flag_vals_for_opdef(opdef, user_flag_vals, force_flags):
    try:
        return op_util.flag_vals_for_opdef(opdef, user_flag_vals, force_flags)
    except op_util.MissingRequiredFlags as e:
        _missing_required_flags_error(e)
    except op_util.InvalidFlagChoice as e:
        _invalid_flag_choice_error(e)
    except op_util.InvalidFlagValue as e:
        _invalid_flag_value_error(e)
    except op_util.NoSuchFlagError as e:
        _no_such_flag_error(e.flag_name, opdef)

def _apply_default_resolved_runs(opdef, flag_vals):
    for run, dep in op_dep.resolved_op_runs_for_opdef(opdef, flag_vals):
        if dep.resdef.name in flag_vals:
            flag_vals[dep.resdef.name] = run.short_id

# =================================================================
# Op - config
# =================================================================

def _op_init_config(label_arg, op):
    if op._run:
        _op_init_config_for_run(op._run, label_arg, op)
    else:
        assert op._opdef
        _op_init_config_for_opdef(op._opdef, label_arg, op)

def _op_init_config_for_run(run, label_arg, op):
    config = run.get("op")
    if not config:
        _missing_op_config_for_restart_error(run)
    if not config.get("op-cmd"):
        _invalid_op_config_for_restart_error(run)
    _apply_op_config_data(config, op)
    if label_arg:
        op._label_template = label_arg

def _op_init_config_for_opdef(opdef, label_arg, op):
    op._op_cmd, op._op_cmd_run_attrs = _op_cmd_for_opdef(opdef)
    op._flag_null_labels = _flag_null_labels_for_opdef(opdef)
    op._python_requires = _python_requires_for_opdef(opdef)
    op._label_template = label_arg or opdef.label
    op._output_scalars = opdef.output_scalars

def _op_cmd_for_opdef(opdef):
    try:
        return op_util.op_cmd_for_opdef(opdef)
    except op_util.InvalidOpDef as e:
        _invalid_opdef_error(opdef, e.msg)

def _flag_null_labels_for_opdef(opdef):
    return {
        f.name: f.null_label
        for f in opdef.flags
        if f.null_label is not None
    }

def _python_requires_for_opdef(opdef):
    return opdef.python_requires or opdef.modeldef.python_requires

# =================================================================
# Op - core
# =================================================================

def _op_init_core(args, op):
    _op_init_opref(op)
    _op_init_cmd(args, op)
    _op_init_run_dir(args, op)
    _op_init_run_label(op)
    _op_init_random_seed(args.random_seed, op)
    _op_init_deps(op)
    _op_init_run_attrs(args, op)
    _op_init_callbacks(op)

# =================================================================
# Op - opref
# =================================================================

def _op_init_opref(op):
    if op._run:
        op.opref = op._run.opref
    else:
        assert op._opdef
        op.opref = op._opdef.opref

# =================================================================
# Op - cmd args / env
# =================================================================

def _op_init_cmd(args, op):
    assert op._op_cmd
    op.cmd_args, op.cmd_env = _generate_op_cmd(
        op._op_cmd,
        op._op_flag_vals,
        op._python_requires)
    _apply_gpu_arg_env(args, op.cmd_env)

def _generate_op_cmd(op_cmd, flag_vals, python_requires):
    resolve_params = _op_cmd_resolve_params(flag_vals, python_requires)
    try:
        return op_cmd_lib.generate(op_cmd, flag_vals, resolve_params)
    except util.UndefinedReferenceError as e:
        _op_cmd_error(
            "invalid setting for operation: command contains "
            "invalid reference '%s'" % e.args[0])

def _op_cmd_resolve_params(flag_vals, python_requires):
    params = dict(flag_vals)
    params["python_exe"] = _proc_python_exe(python_requires)
    return params

def _proc_python_exe(python_requires):
    if not python_requires:
        return sys.executable
    matching = util.find_python_interpreter(python_requires)
    if not matching:
        _op_cmd_error(
            "cannot find a python interpreter for "
            "requirement %r" % python_requires)
    path, _ver = matching
    return path

def _apply_gpu_arg_env(args, env):
    if args.no_gpus:
        env["CUDA_VISIBLE_DEVICES"] = ""
    elif args.gpus is not None:
        env["CUDA_VISIBLE_DEVICES"] = args.gpus

# =================================================================
# Op - run dir
# =================================================================

def _op_init_run_dir(args, op):
    if op._run:
        op.run_dir = op._run.dir
    else:
        op.run_dir = _op_run_dir_for_args(args)

def _op_run_dir_for_args(args):
    if not args.run_dir:
        return None
    run_dir = os.path.abspath(args.run_dir)
    if not args.stage and os.getenv("NO_WARN_RUNDIR") != "1":
        cli.note(
            "Run directory is '%s' (results will not be "
            "visible to Guild)" % run_dir)
    return run_dir

# =================================================================
# Op - run label
# =================================================================

def _op_init_run_label(op):
    op._label = op_util.run_label(
        op._label_template,
        op._user_flag_vals,
        op._op_flag_vals)

# =================================================================
# Op - random seed
# =================================================================

def _op_init_random_seed(random_seed_arg, op):
    if random_seed_arg:
        op._random_seed = random_seed_arg
    elif op._run:
        op._random_seed = _random_seed_for_run(op._run)
    else:
        op._random_seed = runlib.random_seed()

def _random_seed_for_run(run):
    return run.get("random_seed") or runlib.random_seed()

# =================================================================
# Op - run deps
# =================================================================

def _op_init_deps(op):
    if op._run:
        _check_flags_for_resolved_deps(op._user_flag_vals, op._run)
    if op._opdef:
        op.deps = _op_deps_for_opdef(op._opdef, op._op_flag_vals)

def _check_flags_for_resolved_deps(flag_vals, run):
    resolved_deps = run.get("resolved_deps") or {}
    for name in flag_vals:
        if name in resolved_deps:
            _flag_for_resolved_dep_error(name, run)

def _op_deps_for_opdef(opdef, flag_vals):
    try:
        return op_dep.deps_for_opdef(opdef, flag_vals)
    except op_dep.OpDependencyError as e:
        _invalid_opdef_error(opdef, e)

# =================================================================
# Op - run attrs
# =================================================================

def _op_init_run_attrs(args, op):
    attrs = op.run_attrs
    if op._label:
        attrs["label"] = op._label
    attrs["flags"] = op._op_flag_vals
    if op._batch_trials:
        attrs["trials"] = op._batch_trials
    attrs["run_params"] = args.as_kw()
    attrs["random_seed"] = op._random_seed
    if args.max_trials:
        attrs["max_trials"] = args.max_trials
    attrs["host"] = util.hostname()
    attrs["user"] = util.user()
    attrs["platform"] = util.platform_info()
    attrs["op"] = _op_config_data(op)
    if op._op_cmd_run_attrs:
        attrs.update(op._op_cmd_run_attrs)

# =================================================================
# Op - run callbacks
# =================================================================

def _op_init_callbacks(op):
    if op._run:
        _op_init_callbacks_for_restart(op)
    else:
        assert op._opdef
        _op_init_callbacks_for_opdef(op._opdef, op)

def _op_init_callbacks_for_restart(op):
    op.callbacks = oplib.OperationCallbacks(
        init_output_summary=_init_output_summary
    )

def _init_output_summary(op, run):
    if _output_scalars_disabled(op):
        return None
    if _summary_disabled():
        return None
    return _output_scalars_summary(
        op._output_scalars,
        op._op_flag_vals,
        run)

def _output_scalars_disabled(output_scalars):
    return output_scalars is not None and not output_scalars

def _summary_disabled():
    try:
        summary.check_enabled()
    except summary.Disabled as e:
        log.warning(e)
        return True
    else:
        return False

def _output_scalars_summary(output_scalars, flag_vals, run):
    if output_scalars is None:
        output_scalars = summary.DEFAULT_OUTPUT_SCALARS
        ignore = flag_vals.keys()
    else:
        ignore = None
    summary_path = run.guild_path()
    return summary.OutputScalars(output_scalars, summary_path, ignore)

def _op_init_callbacks_for_opdef(opdef, op):
    op.callbacks = oplib.OperationCallbacks(
        init_output_summary=_init_output_summary,
        run_initialized=_copy_sourcecode_cb_for_opdef(opdef)
    )

def _copy_sourcecode_cb_for_opdef(opdef):
    sourcecode_src = opdef.guildfile.dir
    sourcecode_select = op_util.sourcecode_select_for_opdef(opdef)
    def f(op, run):
        _copy_run_sourcecode(sourcecode_src, sourcecode_select, run)
        _write_run_sourcecode_digest(run)
    return f

def _copy_run_sourcecode(sourcecode_src, sourcecode_select, run):
    if os.getenv("NO_SOURCECODE") == "1":
        log.debug("NO_SOURCECODE=1, skipping sourcecode copy")
        return
    if not sourcecode_src:
        log.debug("no sourcecode source, skipping sourcecode copy")
        return
    if not sourcecode_select:
        log.debug("no sourcecode rules, skipping sourcecode copy")
        return
    dest = run.guild_path("sourcecode")
    log.debug(
        "copying source code files for run %s from %s to %s",
        run.id, sourcecode_src, dest)
    op_util.copy_sourcecode(sourcecode_src, sourcecode_select, dest)

def _write_run_sourcecode_digest(run):
    op_util.write_sourcecode_digest(run)

# =================================================================
# State - batch op
# =================================================================

def _state_init_batch_op(S):
    _batch_op_init_run(S)
    _batch_op_init_opdef(S)
    _check_opt_flags_for_missing_batch_opdef(S)
    if S.batch_op:
        _op_init_user_flags(S.args.opt_flags, S.batch_op)
        _op_init_op_flags(S.args, S.batch_op)
        _op_init_config(S.args.batch_label, S.batch_op)
        _op_init_core(S.args, S.batch_op)

def _batch_op_init_run(S):
    if S.restart_run and S.restart_run.batch_proto:
        if S.batch_op is None:
            S.batch_op = Operation()
        S.batch_op._run = S.restart_run

def _batch_op_init_opdef(S):
    if S.batch_op and S.batch_op._run:
        assert not S.args.optimizer and not S.args.optimize, S.args
        # As with user op, we only want opdef when user specifies
        # flags for a batch restart. We check args here rather than
        # S.batch_op._user_flag_vals because we can't process batch
        # user flags until we know we have a batch op, which is
        # determined in part by this function.
        if S.args.opt_flags:
            op.batch_op._opdef = _opdef_for_run(op._run)
    elif S.user_op._opdef:
        _batch_op_init_for_opdef(S.user_op._opdef, S)

def _batch_op_init_for_opdef(opdef, S):
    if S.args.optimizer:
        _batch_op_init_for_named_optimizer(S.args.optimizer, opdef, S)
    elif S.args.optimize:
        _batch_op_init_for_opdef_default_optimizer(opdef, S)
    else:
        _try_implied_batch_op_init(S.user_op, S)

def _batch_op_init_for_named_optimizer(name, opdef, S):
    assert not S.batch_op
    optdef = opdef.get_optimizer(name)
    S.batch_op = Operation()
    if optdef:
        _op_init_for_optimizer(optdef, S.batch_op)
    else:
        _op_init_for_optimizer_opspec(name, S.batch_op)

def _op_init_for_optimizer(optdef, op):
    op._opdef = _opdef_for_opspec(optdef.opspec)
    if optdef.flags:
        op._op_flag_vals.update(optdef.flags)

def _op_init_for_optimizer_opspec(opspec, op):
    op._opdef = _opdef_for_opspec(opspec)

def _batch_op_init_for_opdef_default_optimizer(opdef, S):
    assert not S.batch_op
    S.batch_op = Operation()
    optdef = util.find_apply([
        lambda: opdef.default_optimizer,
        lambda: _default_optimizer(opdef),
    ])
    _op_init_for_optimizer(optdef, S.batch_op)

def _default_optimizer(opdef):
    return guildfile.OptimizerDef.for_name(DEFAULT_OPTIMIZER, opdef)

def _try_implied_batch_op_init(user_op, S):
    batch_opspec = util.find_apply([
        lambda: _batch_opspec_for_flags(user_op._op_flag_vals),
        lambda: _batch_opspec_for_trials(user_op._batch_trials),
    ])
    if batch_opspec:
        assert not S.batch_op
        S.batch_op = Operation()
        S.batch_op._opdef = _opdef_for_opspec(batch_opspec)

def _batch_opspec_for_flags(flag_vals):
    has_list = False
    for val in flag_vals.values():
        if _is_flag_function(val):
            return "random"
        has_list = has_list or isinstance(val, list)
    if has_list:
        return "+"
    return None

def _is_flag_function(val):
    if not isinstance(val, six.string_types):
        return False
    try:
        flag_util.decode_flag_function(val)
    except ValueError:
        return False
    else:
        return True

def _batch_opspec_for_trials(trials):
    return "+" if trials else None

def _check_opt_flags_for_missing_batch_opdef(S):
    if S.args.opt_flags and not (S.batch_op and S.batch_op._opdef):
        _opt_flags_for_missing_batch_opdef_error(S.args.opt_flags)

###################################################################
# Main
###################################################################

def main(args):
    S = _init_state(args)
    _dispatch_op(S)

def _init_state(args):
    _maybe_shift_opspec(args)
    _validate_args(args)
    return _state_for_args(args)

def _maybe_shift_opspec(args):
    # Moves opspec to flags if it looks like a flag assignment
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
        ("print_cmd", "print_env"),
        ("print_trials", "init_trials"),
        ("remote", "background"),
        ("remote", "pidfile"),
        ("stage", "background"),
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
        ("help_model", "--help-model"),
        ("help_op", "--help-op"),
        ("opspec", "OPERATION"),
        ("optimize", "--optimize"),
        ("optimizer", "--optimizer"),
        ("rerun", "--rerun"),
        ("run_dir", "--run-dir"),
        ("test_output_scalars", "--test-output-scalars"),
        ("test_sourcecode", "--test-sourcecode"),
    ]
    for name, desc in incompatible:
        if getattr(args, name):
            restart_option = "restart" if args.restart else "start"
            _incompatible_with_restart_error(desc, restart_option)

###################################################################
# Dispatch op
###################################################################

def _dispatch_op(S):
    if S.args.help_model:
        _print_model_help(S)
    elif S.args.help_op:
        _print_op_help(S)
    elif S.args.test_output_scalars:
        _test_output_scalars(S)
    elif S.args.test_sourcecode:
        _test_sourcecode(S)
    else:
        _dispatch_op_cmd(S)

###################################################################
# Model / op help
###################################################################

def _print_model_help(S):
    assert S.user_op._opdef
    helplib.print_model_help(S.user_op._opdef.modeldef)

def _print_op_help(S):
    assert S.user_op._opdef
    helplib.print_op_help(S.user_op._opdef)

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
    output_scalars = S.user_op._output_scalars or summary.DEFAULT_OUTPUT_SCALARS
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
    opdef = S.user_op._opdef
    assert opdef
    logger = _CopyLogger()
    sourcecode_src = opdef.guildfile.dir
    sourcecode_select = op_util.sourcecode_select_for_opdef(opdef)
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

def _dispatch_op_cmd(S):
    if S.args.print_cmd:
        _print_cmd(S)
    elif S.args.print_env:
        _print_env(S)
    elif S.args.print_trials:
        _print_trials(S)
    elif S.args.save_trials:
        _save_trials(S)
    else:
        _confirm_and_run(S)

###################################################################
# Print op info / save trials
###################################################################

def _print_cmd(S):
    if S.batch_op:
        _print_op_cmd_args(S.batch_op.cmd_args)
        _print_batch_trials_cmd_args(S)
    else:
        _print_op_cmd_args(S.user_op.cmd_args)

def _print_op_cmd_args(args):
    cli.out(" ".join([util.shlex_quote(arg) for arg in args]))

def _print_batch_trials_cmd_args(S):
    _run_tmp_batch(S, {"PRINT_TRIALS_CMD": "1"})

def _run_tmp_batch(S, extra_env):
    assert S.batch_op
    with util.TempDir() as tmp:
        _init_batch_run(S, tmp.path)
        _run_op(S.batch_op, S.args, extra_env)

def _print_env(S):
    _print_op_cmd_env(S.user_op.cmd_env)

def _print_op_cmd_env(env):
    for name, val in sorted(env.items()):
        cli.out("%s=%s" % (name, util.env_var_quote(val)))

def _print_trials(S):
    if not S.batch_op:
        _print_trials_for_non_batch_error()
    _run_tmp_batch(S, {"PRINT_TRIALS": "1"})

def _save_trials(S):
    path = os.path.join(config.cwd(), S.args.save_trials)
    cli.out("Saving trials to %s" % path)
    _run_tmp_batch(S, {"SAVE_TRIALS": path})

###################################################################
# Run
###################################################################

def _confirm_and_run(S):
    if S.args.yes or _confirm_run(S):
        _run(S)

# =================================================================
# Confirm op
# =================================================================

def _confirm_run(S):
    prompt = (
        "You are about to {action} {subject}{batch_suffix}{flags_note}\n"
        "{flags}"
        "Continue?"
        .format(
            action=_preview_op_action(S),
            subject=_preview_op_subject(S),
            batch_suffix=_preview_batch_suffix(S),
            flags_note=_preview_flags_note(S),
            flags=_preview_flags(S),
        )
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

def _preview_op_subject(S):
    op_desc = _fmt_opref(S.user_op.opref)
    if S.restart_run:
        return "%s (%s)" % (S.restart_run.id, op_desc)
    else:
        return op_desc

def _fmt_opref(opref):
    return opref.to_opspec(config.cwd())

def _preview_batch_suffix(S):
    # TODO include info about max trials
    if not S.batch_op:
        return ""
    opt_name = S.batch_op.opref.to_opspec(config.cwd())
    if opt_name == "+":
        return " as a batch"
    elif opt_name == "random":
        return " with random search"
    else:
        return " with '%s' optimizer" % opt_name

def _preview_flags_note(S):
    if S.user_op._op_flag_vals and S.user_op._batch_trials:
        return " (flags below used unless specified in batch trial)"
    return ""

def _preview_flags(S, indent=2):
    flag_vals = S.user_op._op_flag_vals
    if not flag_vals:
        return ""
    null_labels = S.user_op._flag_null_labels
    return "\n".join([
        " " * indent +_format_flag(name, val, null_labels)
        for name, val in sorted(flag_vals.items())
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

# =================================================================
# Run / stage
# =================================================================

def _run(S):
    _check_run_needed(S)
    op = _init_op_for_run(S)
    if S.args.stage:
        _stage_op(op, S.args)
    else:
        _run_op(op, S.args)

def _check_run_needed(S):
    if not S.args.needed:
        return
    matching = _find_matching_runs(S)
    if matching:
        if _restarting_match(matching, S):
            _skip_needed_unchanged_flags_info()
        else:
            _skip_needed_matches_info(matching)
        raise SystemExit(0)

def _find_matching_runs(S):
    if S.batch_op:
        matching = op_util.find_matching_runs(
            S.batch_op.opref,
            S.batch_op._op_flag_vals)
        return _filter_matching_batch_runs(matching, S.user_op)
    else:
        return op_util.find_matching_runs(
            S.user_op.opref,
            S.user_op._op_flag_vals)

def _filter_matching_batch_runs(batch_runs, user_op):
    return [
        run for run in batch_runs
        if (run.batch_proto and
            op_util.is_matching_run(
                run.batch_proto,
                user_op.opref,
                user_op._op_flag_vals,
                include_pending=True))
    ]

def _restarting_match(matches, S):
    restart_run = S.batch_op._run if S.batch_op else S.user_op._run
    return restart_run and restart_run.id in (run.id for run in matches)

def _init_op_for_run(S):
    if S.batch_op:
        _init_batch_run(S)
        return S.batch_op
    return S.user_op

def _init_batch_run(S, run_dir=None):
    batch_run = oplib.init_run(S.batch_op, run_dir)
    S.batch_op.run_dir = batch_run.dir
    oplib.init_run(S.user_op, batch_run.guild_path("proto"))

def _stage_op(op, args):
    try:
        run = oplib.stage(op)
    except op_dep.OpDependencyError as e:
        _op_dependency_error(e)
    else:
        if not args.quiet:
            _print_staged_info(run, args)

def _print_staged_info(run, args):
    if args.run_dir:
        _print_staged_dir_instructions(run)
    else:
        _print_stage_pending_instructions(run)

def _print_staged_dir_instructions(run):
    cmd_args = run.get("cmd") or []
    cmd = " ".join([util.shlex_quote(arg) for arg in cmd_args])
    cli.out(
        "{op} staged in '{dir}'\n"
        "To start the operation, use "
        "\"(cd '{dir}' && source .guild/ENV && {cmd})\""
        .format(
            op=run_util.format_operation(run),
            dir=run.dir,
            cmd=cmd))

def _print_stage_pending_instructions(run):
    cli.out(
        "{op} staged as {run_id}\n"
        "To start the operation, use 'guild run --start {run_id}'"
        .format(
            op=run_util.format_operation(run),
            run_id=run.id))

def _run_op(op, args, extra_env=None):
    try:
        run, exit_status = oplib.run(
            op,
            quiet=args.quiet,
            extra_env=extra_env)
    except op_dep.OpDependencyError as e:
        _op_dependency_error(e)
    except oplib.ProcessError as e:
        _op_process_error(op, e)
    else:
        _handle_run_exit(run, exit_status)

def _handle_run_exit(run, exit_status):
    if exit_status != 0:
        cli.error(exit_status=exit_status)

###################################################################
# Error handlers / user messages
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

def _coerce_flag_val_error(e):
    cli.error(
        "cannot apply %r to flag '%s': %s"
        % (e.value, e.flag_name, e.error))

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
        "invalid definition for operation '%s': %s"
        % (opdef.fullname, msg))

def _model_op_proxy_error(e):
    cli.error("cannot run '%s': %s" % (e.opspec, e.msg))

def _op_cmd_error(msg):
    cli.error(msg)

def _op_dependency_error(e):
    cli.error("run failed because a dependency was not met: %s" % e)

def _op_process_error(op, e):
    cli.error("error running %s: %s" % (_fmt_opref(op.opref), e))

def _opt_flags_for_missing_batch_opdef_error(args):
    assert args
    cli.error("invalid optimizer flag %s: no optimizer specified" % args[0])

def _missing_op_config_for_restart_error(run):
    cli.error(
        "cannot restart run in %s: missing op configuration\n"
        "The run may not have been initialized correctly. Try starting "
        "the operation without the --start/--restart flag." % run.dir)

def _invalid_op_config_for_restart_error(run):
    cli.error(
        "cannot restart run in %s: invalid op configuration\n"
        "This may be an internal error. Please open an issue "
        "https://github.com/guildai/guildai/issues." % run.dir)

def _no_such_batch_file_error(path):
    cli.error("batch file %s does not exist" % path)

def _batch_file_error(e):
    cli.error(e)

def _flag_for_resolved_dep_error(flag_name, run):
    cli.error(
        "cannot specify a value for '%s' when restarting %s - "
        "resource has already been resolved" % (flag_name, run.short_id))

def _print_trials_for_non_batch_error():
    cli.error("cannot print trials for a non-batch operation")

def _skip_needed_unchanged_flags_info():
    cli.out(
        "Skipping run because flags have not changed "
        "(--needed specified)")

def _skip_needed_matches_info(matching_runs):
    cli.out(
        "Skipping because the following runs match "
        "this operation (--needed specified):")
    formatted = [run_util.format_run(run) for run in matching_runs]
    cols = [
        "index", "operation", "started",
        "status_with_remote", "label"
    ]
    cli.table(formatted, cols=cols, indent=2)

###################################################################
# Cmd impl API
###################################################################

def run(**kw):
    from guild.commands import run
    ctx = run.run.make_context("", [])
    ctx.params.update(kw)
    ctx.params["yes"] = True
    args = click_util.Args(**ctx.params)
    main(args)

def one_run(run_id_prefix):
    runs = [
        runlib.Run(id, path)
        for id, path in var.find_runs(run_id_prefix)
    ]
    return cmd_impl_support.one_run(runs, run_id_prefix)
