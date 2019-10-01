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
from guild import op2 as oplib
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
        _State_init(self, args)

def _State_init(S, args):
    S.args = args
    S.restart_run = _maybe_restart_run(args)
    S.opdef = _maybe_opdef(args.opspec, S.restart_run)
    assert S.opdef or S.restart_run

def _maybe_restart_run(args):
    restart_run_spec = args.restart or args.start
    if not restart_run_spec:
        return None
    return _run_for_spec(restart_run_spec)

def _run_for_spec(spec):
    return util.find_apply([
        run_util.run_for_run_dir,
        run_util.marked_or_latest_run_for_opspec,
        one_run,
    ], spec)

def _maybe_opdef(opspec, restart_run):
    if restart_run and opspec:
        _opspec_and_restart_error()
    if restart_run:
        return run_util.run_opdef(restart_run)
    try:
        return run_util.opdef_for_opspec(opspec)
    except run_util.CwdGuildfileError as e:
        _guildfile_error(e.path, str(e))
    except run_util.NoSuchModelOp as e:
        _no_such_model_op_error(opspec)
    except run_util.MultipleMatchingModels as e:
        _multiple_models_error(e.model_ref, e.matches)

###################################################################
# Main
###################################################################

def main(args):
    state = _init_state(args)
    op = _init_op(state)
    _dispatch_op(state, op)

def _init_state(args):
    _maybe_shift_opspec(args)
    _validate_args(args)
    return State(args)

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
        return oplib.from_opdef(opdef)
    else:
        assert S.restart_run
        return oplib.from_run(S.restart_run)

###################################################################
# Dispatch op
###################################################################

def _dispatch_op(op, S):
    assert False

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

###################################################################
# Cmd impl API
###################################################################

def one_run(run_id_prefix):
    runs = [
        runlib.Run(id, path)
        for id, path in var.find_runs(run_id_prefix)
    ]
    return cmd_impl_support.one_run(runs, run_id_prefix)
