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

###################################################################
# State
###################################################################

""" ############################ OLD
class State(object):

    def __init__(self, args, restart_run, opdef, user_flag_vals,
                 op_flag_vals, label, batch_files, run_dir,
                 extra_run_attrs, extra_cmd_env, batch_opdef,
                 batch_flag_vals):
        self.args = args
        self.restart_run = restart_run
        self.opdef = opdef
        self.user_flag_vals = user_flag_vals
        self.op_flag_vals = op_flag_vals
        self.label = label
        self.batch_files = batch_files
        self.run_dir = run_dir
        self.extra_run_attrs = extra_run_attrs
        self.extra_cmd_env = extra_cmd_env
        self.batch_opdef = batch_opdef
        self.batch_flag_vals = batch_flag_vals

    batch_opdef = _state_batch_opdef(args, op_flag_vals, restart_run)

    batch_flag_vals = _state_batch_flag_vals(
        args.opt_flags, batch_opdef, args.force_flags)

    return State(args, restart_run, opdef, user_flag_vals,
                 op_flag_vals, label, batch_files, run_dir,
                 extra_run_attrs, extra_cmd_env, batch_opdef,
                 batch_flag_vals)

    return Operation(
        opdef.opref,
        _op_cmd_for_opdef(opdef, extra_cmd_env),
        flag_vals=flag_vals,
        flag_null_labels=_flag_null_labels_for_opdef(opdef),
        sourcecode_src=opdef.guildfile.dir,
        sourcecode_select=_sourcecode_select_for_opdef(opdef),
        deps=_op_deps_for_opdef(opdef, flag_vals),
        output_scalars=opdef.output_scalars,
        stoppable=opdef.stoppable,
        python_requires=_python_requires_for_opdef(opdef),
        **kw)

################################ """

"""
class State(object):

    def __init__(self, args, opdef, restart_run, flag_vals,
                 flag_null_labels, op, batch_op):
        self.args = args
        self.opdef = opdef
        self.restart_run = restart_run
        self.flag_vals = flag_vals
        self.flag_null_labels = flag_null_labels
        self.op = op
        self.batch_op = batch_op
"""

class State(object):

    def __init__(self, args):
        self.args = args
        self.restart_run = None
        self.user_flag_vals = {}
        self.op_flag_vals = {}
        self.flag_null_labels = {}
        self.op = oplib.Operation()
        #self.batch_user_flag_vals = None
        #self.batch_op_flag_vals = None

def _state_for_args(args):
    S = State(args)
    _state_init_user_flags(S)
    _state_init_restart_run(S)
    _state_init_opdef(S)
    _state_init_flag_null_labels(S)
    _state_init_op_flags(S)
    _state_init_op(S)
    return S

    """
    opdef = _state_opdef(args, restart_run)
    user_flag_vals, _batch_files = _state_split_flag_args(args.flags)
    op_flag_vals = _state_op_flag_vals(opdef, user_flag_vals, args.force_flags)
    if restart_run:
        _apply_restart_run_flags(restart_run, user_flag_vals, op_flag_vals)
    flag_null_labels = _flag_null_labels_for_opdef(opdef)

    op = _state_op(opdef, restart_run, user_flag_vals, op_flag_vals, args)

    batch_opdef = _state_batch_opdef(restart_run, op_flag_vals, args)
    batch_user_flag_vals = _parse_assigns(args.opt_flags)
    batch_op_flag_vals = _state_op_flag_vals(batch_opdef,
                                             batch_user_flag_vals,
                                             args.force_flags)
    batch_op = _state_op(batch_opdef, restart_run,
                         batch_user_flag_vals, batch_op_flag_vals, etc)
    """

# =================================================================
# State - user flags
# =================================================================

def _state_init_user_flags(S):
    S.user_flag_vals, _TODO_batch_files = _state_split_flag_args(S.args.flags)

def _state_split_flag_args(flag_args):
    batch_files, rest_args = op_util.split_batch_files(flag_args)
    assigns = _parse_assigns(rest_args)
    return assigns, batch_files

def _parse_assigns(assign_args):
    try:
        return op_util.parse_flag_assigns(assign_args)
    except op_util.ArgValueError as e:
        _invalid_flag_arg_error(e.arg)

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
# State - opdef
# =================================================================

def _state_init_opdef(S):
    if S.restart_run:
        S.opdef = _opdef_for_run(S.restart_run)
        _check_restart_args_for_missing_opdef(S)
    else:
        S.opdef = _opdef_for_opspec(S.args.opspec)

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

def _check_restart_args_for_missing_opdef(S):
    if S.restart_run and S.args.flags and not S.opdef:
        _restart_flags_with_missing_opdef_error(S.restart_run)

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
# State - op flags
# =================================================================

def _state_init_op_flags(S):
    if S.restart_run:
        _apply_run_flags(S.restart_run, S.op_flag_vals)
    if S.opdef:
        _apply_opdef_flags(
            S.opdef,
            S.user_flag_vals,
            S.args.force_flags,
            S.op_flag_vals)

def _apply_run_flags(run, target):
    target.update(run.get("flags") or {})

def _apply_opdef_flags(opdef, user_flag_vals, force_flags, target):
    """Applies opdef and user-provided flags to target flag vals.

    Opdef is used to provide missing default values, coerce flag vals,
    and validate vals. Opdef-provided flag vals are added to target
    only if they are not already in target, or if they are in
    user-provided flags. This maintains existing values (e.g. from a
    restart) unless a user explicitly provides a flag value.
    """
    op_flag_vals = _flag_vals_for_opdef(opdef, user_flag_vals, force_flags)
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

# =================================================================
# State - op
# =================================================================

def _state_init_flag_null_labels(S):
    if S.opdef:
        S.flag_null_labels = _flag_null_labels_for_opdef(S.opdef)
    else:
        assert S.restart_run
        S.flag_null_labels = S.restart_run.get("_flag_null_labels")

def _flag_null_labels_for_opdef(opdef):
    return {
        f.name: f.null_label
        for f in opdef.flags
        if f.null_label is not None
    }

# =================================================================
# State - op
# =================================================================

def _state_init_op(S):
    if S.restart_run:
        _state_init_op_for_restart(S.restart_run, S, S.op)
    else:
        assert S.opdef
        _state_init_op_for_opdef(S.opdef, S, S.op)

def _state_init_op_for_restart(run, S, op):
    op.opref = run.opref
    op_config = run.get("op")
    if not op_config:
        _missing_op_config_for_restart_error(run)
    op_cmd = _op_cmd_for_data(op_config.get("op_cmd"), run)
    python_requires = op_config.get("python_requires")
    op.cmd_args, op.cmd_env = _generate_op_cmd(
        op_cmd, S.op_flag_vals, python_requires)
    op.run_dir = run.dir
    op.run_attrs = _op_run_attrs_for_restart(op_config, S)
    # TODO: what to do with deps???
    op.callbacks = _op_callbacks_for_restart(op_config, S.op_flag_vals)

def _op_cmd_for_data(data, run):
    if not data:
        _invalid_op_config_for_restart_error(run)
    return op_cmd_lib.for_data(data)

def _generate_op_cmd(op_cmd, flag_vals, python_requires):
    resolve_params = _op_cmd_resolve_params(flag_vals, python_requires)
    try:
        return op_cmd_lib.generate(op_cmd, flag_vals, resolve_params)
    except util.UndefinedReferenceError as e:
        _op_cmd_error(
            "invalid setting for operation: command contains "
            "invalid reference '%s'" % e.args[0])

def _op_run_attrs_for_restart(op_config, S):
    attrs = {}
    label_template = S.args.label or op_config.get("label")
    attrs["label"] = _op_label(label_template, S.user_flag_vals, S.op_flag_vals)
    attrs["flags"] = S.op_flag_vals
    attrs["run_params"] = S.args.as_kw()
    if S.args.random_seed:
        attrs["random_seed"] = S.args.random_seed
    if S.args.max_trials:
        attrs["max_trials"] = S.args.max_trials
    attrs["host"] = util.hostname()
    attrs["user"] = util.user()
    attrs["platform"] = util.platform_info()
    return attrs

def _op_callbacks_for_restart(op_config, flag_vals):
    def init_output_summary(_op, run):
        output_scalars = op_config.get("output_scalars")
        return _output_scalars_summary(output_scalars, flag_vals, run)

    return oplib.OperationCallbacks(
        init_output_summary=init_output_summary,
    )

def _output_scalars_summary(output_scalars, flag_vals, run):
    try:
        summary.check_enabled()
    except summary.Disabled as e:
        log.warning(e)
        return None
    else:
        return _output_scalars_summary_(output_scalars, flag_vals, run)

def _output_scalars_summary_(output_scalars, flag_vals, run):
    if output_scalars is None:
        output_scalars = summary.DEFAULT_OUTPUT_SCALARS
        ignore = flag_vals.keys()
    else:
        ignore = None
    summary_path = run.guild_path()
    return summary.OutputScalars(output_scalars, summary_path, ignore)

def _state_init_op_for_opdef(opdef, S, op):
    op.opref = opdef.opref
    args_cmd_env = _cmd_env_for_args(S.args)
    op_cmd = op_util.op_cmd_for_opdef(opdef, args_cmd_env)
    python_requires = _python_requires_for_opdef(opdef)
    op.cmd_args, op.cmd_env = _generate_op_cmd(
        op_cmd, S.op_flag_vals, python_requires)
    op.run_dir = _op_run_dir_for_args(S.args)
    op.run_attrs = _op_run_attrs_for_opdef(opdef, op_cmd, python_requires, S)
    op.deps = _op_deps_for_opdef(opdef, S.op_flag_vals)
    op.callbacks = _op_callbacks_for_opdef(opdef, S.op_flag_vals)

def _cmd_env_for_args(args):
    env = {}
    if args.no_gpus:
        env["CUDA_VISIBLE_DEVICES"] = ""
    elif args.gpus is not None:
        env["CUDA_VISIBLE_DEVICES"] = args.gpus
    return env

def _python_requires_for_opdef(opdef):
    return opdef.python_requires or opdef.modeldef.python_requires

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

def _op_run_dir_for_args(args):
    if not args.run_dir:
        return None
    run_dir = os.path.abspath(args.run_dir)
    if not args.stage and os.getenv("NO_WARN_RUNDIR") != "1":
        cli.note(
            "Run directory is '%s' (results will not be "
            "visible to Guild)" % run_dir)
    return run_dir

def _op_run_attrs_for_opdef(opdef, op_cmd, python_requires, S):
    attrs = {}
    label_template = S.args.label or opdef.label
    attrs["op"] = {
        "flag_null_labels": S.flag_null_labels,
        "op_cmd": op_cmd_lib.as_data(op_cmd),
        "python_requires": python_requires,
        "label": label_template,
        "output_scalars": opdef.output_scalars,
    }
    attrs["label"] = _op_label(label_template, S.user_flag_vals, S.op_flag_vals)
    attrs["flags"] = S.op_flag_vals
    attrs["run_params"] = S.args.as_kw()
    attrs["random_seed"] = _random_seed(S.args.random_seed)
    if S.args.max_trials:
        attrs["max_trials"] = S.args.max_trials
    attrs["host"] = util.hostname()
    attrs["user"] = util.user()
    attrs["platform"] = util.platform_info()
    return attrs

def _op_label(label_template, user_flag_vals, op_flag_vals):
    if label_template:
        resolve_vals = {
            name: flag_util.encode_flag_val(val)
            for name, val in op_flag_vals.items()
        }
        return util.resolve_refs(label_template, resolve_vals, "")
    return _default_op_label(user_flag_vals)

def _default_op_label(flag_vals):
    return " ".join(flag_util.format_flags(flag_vals, truncate_floats=True))

def _random_seed(random_seed_arg):
    if random_seed_arg is not None:
        return random_seed_arg
    return runlib.random_seed()

def _op_deps_for_opdef(opdef, flag_vals):
    try:
        return op_dep.deps_for_opdef(opdef, flag_vals)
    except op_dep.OpDependencyError as e:
        _invalid_opdef_error(opdef, e)

def _op_callbacks_for_opdef(opdef, flag_vals):
    def init_output_summary(_op, run):
        return _output_scalars_summary(opdef.output_scalars, flag_vals, run)

    def run_initialized(op, run):
        sourcecode_src = opdef.guildfile.dir
        sourcecode_select = op_util.sourcecode_select_for_opdef(opdef)
        _copy_run_sourcecode(sourcecode_src, sourcecode_select, run)
        _write_run_sourcecode_digest(run)

    return oplib.OperationCallbacks(
        init_output_summary=init_output_summary,
        run_initialized=run_initialized,
    )

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

"""

# =================================================================
# XXXXXXXXXXXXXXXX batch opdef and stuff XXXXXXXXXXXXXXXXXXXX
# =================================================================

def _state_batch_opdef(restart_run, flag_vals, args):
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

def _batch_opdef_for_args(args, flag_vals):
    optimizer_opspec = _optimizer_opspec_for_args(args, flag_vals)
    if optimizer_opspec:
        return _opdef_for_opspec(optimizer_opspec)
    return None

def _optimizer_opspec_for_args(args, flag_vals):
    if args.optimizer:
        return args.optimizer
    return _implied_optimizer_for_flags(flag_vals)

def _implied_optimizer_for_flags(flag_vals):
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

"""

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

"""
def _init_op(S):
    if S.opdef:
        return _op_for_opdef(S)
    else:
        assert S.restart_run
        return _op_for_restart_run(S)

def _op_for_opdef(S):
    assert S.opdef
    if S.batch_opdef:
        return _batch_op(S)
    else:
        return _default_op_for_opdef(S)

def _batch_op(S):
    return _gen_op_for_opdef(S, callbacks=_batch_op_callbacks(S))

def _batch_op_callbacks(S):
    return oplib.OperationCallbacks(
        run_initialized=_batch_run_init_cb(S),
    )

def _batch_run_init_cb(S):
    proto_op = _default_op_for_opdef(S)
    def f(_batch_op, batch_run):
        proto_dir = batch_run.guild_path("proto")
        oplib.init_run(proto_op, proto_dir)
    return f

def _default_op_for_opdef(S):
    return _gen_op_for_opdef(S)

def _gen_op_for_opdef(S, callbacks=None):






    try:
        op = oplib.for_opdef(
            S.opdef,
            S.op_flag_vals,
            extra_cmd_env=S.extra_cmd_env,
            label=S.label,
            extra_run_attrs=S.extra_run_attrs,
            run_dir=S.run_dir,
            callbacks=callbacks,
        )
        if S.restart_run:
            _disable_sourcecode_copy_for_restart_op(op)
        return op
    except oplib.InvalidOpDef as e:
        _invalid_opdef_error(S.opdef, str(e))

def _apply_op_label(label_arg, opdef, flag_vals, op):
    label_template = _label_template(label_arg, opdef, flag_vals)
    if label_template is not None:
        op.label = op_util.format_label(label_template, op.flag_vals)

def _label_template(label_arg, opdef, flag_vals):
    return util.find_apply([
        lambda: label_arg,
        lambda: opdef and opdef.label,
        lambda: _default_label(flag_vals),
    ])

def _default_label(flag_vals):
    if not flag_vals:
        return None
    return op_util.flags_desc(flag_vals, delim=" ")

def _disable_sourcecode_copy_for_restart_op(op):
    # Disable source code copy if restarting. Restarted runs must
    # always use their original source code.
    op.sourcecode_src = None
    op.sourcecode_select = None

def _op_for_restart_run(S):
    return oplib.for_run(
        S.restart_run,
        label=S.args.label,
        extra_run_attrs=S.extra_run_attrs,
        gpus=S.args.gpus)

def _apply_opdef_to_restart_op(S, restart_op):
    opdef_op = _op_for_opdef(S)
    op_util.apply_flags_to_restart_op(opdef_op, restart_op)


def _validate_op(op, S):
    if S.restart_run:
        _validate_restart_op(op, S)

def _validate_restart_op(op, S):
    assert op.opref.to_opspec() == S.restart_run.opref.to_opspec()
    assert op.run_dir == S.restart_run.dir
    # Important that we NOT modify sourcecode for a restart.
    assert op.sourcecode_src is None
    assert op.sourcecode_select is None
"""

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
    output_scalars = S.opdef.output_scalars or summary.DEFAULT_OUTPUT_SCALARS
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

def _dispatch_op_cmd(S):
    if S.args.print_cmd or S.args.print_env:
        _print_op_cmd(S)
    elif S.args.print_trials or S.args.save_trials:
        assert False, "TODO"
        #_print_or_save_trials(op, args)
    else:
        _confirm_and_run_op(S)

###################################################################
# Print op info
###################################################################

def _print_op_cmd(S):
    if S.args.print_cmd:
        _print_op_cmd_args(S.op.cmd_args)
    if S.args.print_env:
        _print_op_cmd_env(S.op.cmd_env)

def _print_op_cmd_args(args):
    cli.out(" ".join([util.shlex_quote(arg) for arg in args]))

def _print_op_cmd_env(env):
    for name, val in sorted(env.items()):
        cli.out("%s=%s" % (name, util.env_var_quote(val)))

###################################################################
# Run op
###################################################################

def _confirm_and_run_op(S):
    if S.args.yes or _confirm_run(S):
        _run_op(S)

# =================================================================
# Confirm op
# =================================================================

def _confirm_run(S):
    prompt = (
        "You are about to {action} {subject}{batch_suffix}\n"
        "{flags}"
        "Continue?"
        .format(
            action=_preview_op_action(S),
            subject=_preview_op_subject(S),
            batch_suffix=_preview_batch_suffix(S),
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
    op_desc = _fmt_opspec(S.op.opref)
    if S.restart_run:
        return "%s (%s)" % (S.restart_run.id, op_desc)
    else:
        return op_desc

def _fmt_opspec(opref):
    return opref.to_opspec(config.cwd())

def _preview_batch_suffix(S):
    return ""
    """ TODO ################
    if not S.batch_op:
        return ""
    else:
        return " TODO: some batch desc for %s" % S.batch_op.opref
    ############ """

def _preview_flags(S, indent=2):
    if not S.op_flag_vals:
        return ""
    return "\n".join([
        " " * indent +_format_flag(name, val, S.flag_null_labels)
        for name, val in sorted(S.op_flag_vals.items())
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

def _run_op(S):
    if S.args.stage:
        _stage_op(S)
    else:
        _run_op_(S)

def _stage_op(S):
    run = oplib.stage(S.op)
    if not S.args.quiet:
        _print_staged_info(run, S)

def _print_staged_info(run, S):
    if S.args.run_dir:
        _print_staged_dir_instructions(run, S)
    else:
        _print_stage_pending_instructions(run, S)

def _print_staged_dir_instructions(run, S):
    cmd = " ".join([util.shlex_quote(arg) for arg in S.op.cmd_args])
    cli.out(
        "{op} staged in '{dir}'\n"
        "To start the operation, use "
        "\"(cd '{dir}' && source .guild/ENV && {cmd})\""
        .format(
            op=_fmt_opspec(S.op.opref),
            dir=run.dir,
            cmd=cmd))

def _print_stage_pending_instructions(run, S):
    cli.out(
        "{op} staged as {run_id}\n"
        "To start the operation, use 'guild run --start {run_id}'"
        .format(
            op=_fmt_opspec(S.op.opref),
            run_id=run.id))

def _run_op_(S):
    try:
        run, exit_status = oplib.run(S.op, quiet=S.args.quiet)
    except op_dep.OpDependencyError as e:
        _op_dependency_error(e)
    except oplib.ProcessError as e:
        _op_process_error(S.op, e)
    else:
        _handle_run_exit(run, exit_status, S)

def _handle_run_exit(run, exit_status, S):
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
        "invalid setting for operation '%s': %s"
        % (opdef.fullname, msg))

def _model_op_proxy_error(e):
    cli.error("cannot run '%s': %s" % (e.opspec, e.msg))

def _op_cmd_error(msg):
    cli.error(msg)

def _op_dependency_error(e):
    cli.error(
        "run failed because a dependency was not met: %s" % e)

def _op_process_error(op, e):
    cli.error("error running %s: %s" % (_fmt_opspec(op.opref), e))

def _restart_flags_with_missing_opdef_error(restart_run):
    cli.error(
        "cannot set flags when restarting %s: configuration "
        "for operation '%s' is not available"
        % (restart_run.id, restart_run.opref.to_opspec()))

def _batch_flags_for_missing_batch_opdef_error(args):
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

###################################################################
# Cmd impl API
###################################################################

def one_run(run_id_prefix):
    runs = [
        runlib.Run(id, path)
        for id, path in var.find_runs(run_id_prefix)
    ]
    return cmd_impl_support.one_run(runs, run_id_prefix)
