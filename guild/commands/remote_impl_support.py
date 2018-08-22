# Copyright 2017-2018 TensorHub, Inc.
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

from guild import cli
from guild import remote as remotelib

from . import remote_support

def list_runs(args):
    assert args.remote
    if args.archive:
        cli.error("--archive and --remote cannot both be used")
    remote = remote_support.remote_for_args(args)
    try:
        remote.list_runs(**_list_runs_kw(args))
    except remotelib.RemoteProcessError as e:
        cli.error(exit_status=e.exit_status)

def _list_runs_kw(args):
    names = [
        "all",
        "completed",
        "deleted",
        "error",
        "labels",
        "more",
        "ops",
        "running",
        "terminated",
        "unlabeled",
        "verbose",
    ]
    ignore = [
        "archive",
        "remote",
    ]
    return _arg_kw(args, names, ignore)

def _arg_kw(args, names, ignore):
    kw_in = args.as_kw()
    kw = {name: kw_in[name] for name in names}
    for name in names + ignore:
        del kw_in[name]
    assert not kw_in, kw_in
    return kw

def run(args):
    assert args.remote
    remote = remote_support.remote_for_args(args)
    try:
        remote.run_op(**_run_kw(args))
    except remotelib.RemoteProcessError as e:
        cli.error(exit_status=e.exit_status)
    except remotelib.RemoteProcessDetached as e:
        cli.out(
            "\nDetached from remote run {run_id} (still running)\n"
            "To re-attach use 'guild watch {run_id} -r {remote}'"
            .format(run_id=e.args[0], remote=args.remote))
    except remotelib.OperationError as e:
        _handle_run_op_error(e, remote)

def _handle_run_op_error(e, remote):
    if e.args[0] == "running":
        assert len(e.args) == 2, e.args
        msg = (
            "{run_id} is still running\n"
            "Wait for it to stop or try 'guild stop {run_id} -r {remote_name}' "
            "to stop it."
            .format(
                run_id=e.args[1],
                remote_name=remote.name))
    else:
        msg = e.args[0]
    cli.error(msg)

def _run_kw(args):
    names = [
        "args",
        "disable_plugins",
        "gpus",
        "label",
        "no_gpus",
        "no_wait",
        "opspec",
        "restart",
    ]
    ignore = [
        "background",
        "help_model",
        "help_op",
        "print_cmd",
        "print_env",
        "quiet",
        "remote",
        "rerun",
        "run_dir",
        "set_trace",
        "stage",
        "workflow",
        "yes",
    ]
    return _arg_kw(args, names, ignore)

def one_run(run_id_prefix, args):
    assert args.remote
    remote = remote_support.remote_for_args(args)
    cli.out("Getting remote run info")
    try:
        return remote.one_run(run_id_prefix, ["flags"])
    except remotelib.RemoteProcessError as e:
        cli.error(exit_status=e.exit_status)

def watch_run(args):
    assert args.remote
    remote = remote_support.remote_for_args(args)
    try:
        remote.watch_run(**_watch_run_kw(args))
    except remotelib.RemoteProcessError as e:
        cli.error(exit_status=e.exit_status)

def _watch_run_kw(args):
    names = [
        "ops",
        "pid",
        "labels",
        "run",
        "unlabeled",
    ]
    ignore = [
        "remote",
    ]
    return _arg_kw(args, names, ignore)

def delete_runs(args):
    assert args.remote
    remote = remote_support.remote_for_args(args)
    try:
        remote.delete_runs(**_runs_select_kw(args))
    except remotelib.RemoteProcessError as e:
        cli.error(exit_status=e.exit_status)

def _runs_select_kw(args):
    names = [
        "completed",
        "error",
        "labels",
        "ops",
        "permanent",
        "running",
        "runs",
        "terminated",
        "unlabeled",
        "yes",
    ]
    ignore = [
        "remote",
    ]
    return _arg_kw(args, names, ignore)

def run_info(args):
    assert args.remote
    remote = remote_support.remote_for_args(args)
    try:
        remote.run_info(**_run_info_kw(args))
    except remotelib.RemoteProcessError as e:
        cli.error(exit_status=e.exit_status)

def _run_info_kw(args):
    names = [
        "all_files",
        "completed",
        "deps",
        "env",
        "error",
        "files",
        "flags",
        "follow_links",
        "labels",
        "ops",
        "output",
        "page_output",
        "run",
        "running",
        "terminated",
        "unlabeled",
    ]
    ignore = [
        "private_attrs",
        "remote",
    ]
    return _arg_kw(args, names, ignore)

def check(args):
    assert args.remote
    if args.tests or args.all_tests:
        cli.error("tests are not supported for remote check")
    if args.no_info:
        cli.error("--no-info is not supported for remote check")
    remote = remote_support.remote_for_args(args)
    try:
        remote.check(**_check_kw(args))
    except remotelib.RemoteProcessError as e:
        cli.error(exit_status=e.exit_status)

def _check_kw(args):
    names = [
        "verbose",
    ]
    ignore = [
        "all_tests",
        "no_info",
        "remote",
        "skip",
        "tests",
        "uat",
    ]
    return _arg_kw(args, names, ignore)
