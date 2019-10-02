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

from guild import cli
from guild import cmd_impl_support
from guild import help as helplib
from guild import op2 as oplib
from guild import op_util2 as op_util
from guild import run as runlib
from guild import run_util
from guild import util
from guild import var

log = logging.getLogger("guild")

###################################################################
# State
###################################################################

class State(object):

    def __init__(self, args):
        self.args = args
        self.restart_run = _state_restart_run(args.restart)
        self.opdef = _state_opdef(args, self.restart_run)
        assert self.opdef or self.restart_run
        (self.flag_vals,
         self.batch_files) = _state_split_flag_args(args.flags)

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
    _apply_start_alias(args)
    return State(args)

def _maybe_shift_opspec(args):
    """Moves opspec to flags if it looks like a flag assignment.
    """
    if args.opspec and "=" in args.opspec:
        args.flags = (args.opspec,) + args.flags
        args.opspec = None

def _apply_start_alias(args):
    if args.start:
        args.restart = args.start

def _validate_args(args):
    _check_incompatible_options(args)
    _check_opspec_and_restart(args)

def _check_incompatible_options(args):
    incompatible = [
        ("rerun", "restart"),
        ("rerun", "start"),
        ("run_dir", "restart"),
        ("run_dir", "start"),
        ("run_dir", "restage"),
        ("no_gpus", "gpus"),
        ("print_trials", "init_trials"),
        ("minimize", "maximize"),
        ("optimize", "optimizer"),
        ("remote", "background"),
        ("remote", "pidfile"),
        ("stage", "background"),
        ("stage", "pidfile"),
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
        return oplib.from_opdef(S.opdef, S.flag_vals)
    except oplib.InvalidOpDef as e:
        _invalid_opdef_error(S.opdef, str(e))

###################################################################
# Dispatch op
###################################################################

def _dispatch_op(op, S):
    if S.args.help_model:
        _print_model_help(S)
    elif S.args.help_op:
        _print_op_help(S)
    elif S.args.test_output_scalars:
        _test_output_scalars(opdef, args)
    elif S.args.test_sourcecode:
        _test_sourcecode(opdef)
    else:
        _dispatch_op_cmd(opdef, args)

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
    cli.error(
        "operation '{op}' is not defined for model '{model}'\n"
        "Try 'guild operations {model}' for a list of available operations."
        .format(op=op_name, model=model.name))

def _invalid_flag_arg_error(arg):
    cli.error("invalid argument '%s' - expected NAME=VAL" % arg)

def _invalid_opdef_error(opdef, msg):
    cli.error(
        "invalid setting for operation '%s': %s"
        % (opdef.fullname, msg))

def _restart_run_help_error(op_name, restart_run):
    cli.error(
        "help is not available for '%s' (run %s)"
        % (opspec, restart_run.id))

###################################################################
# Cmd impl API
###################################################################

def one_run(run_id_prefix):
    runs = [
        runlib.Run(id, path)
        for id, path in var.find_runs(run_id_prefix)
    ]
    return cmd_impl_support.one_run(runs, run_id_prefix)
