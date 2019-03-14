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

import os

from guild import cli
from guild import remote as remotelib

from . import remote_support

class op_handler(object):

    def __init__(self, remote):
        self.remote = remote

    def __enter__(self):
        return self

    def __exit__(self, etype, e, _tb):
        if etype is not None:
            self._handle_error(etype, e)
        return False

    def _handle_error(self, etype, e):
        if etype is remotelib.OperationError:
            _handle_op_error(e, self.remote)
        elif etype is remotelib.RemoteProcessError:
            _handle_remote_process_error(e)
        elif etype is remotelib.OperationNotSupported:
            _handle_not_supported(self.remote)

def list_runs(args):
    assert args.remote
    if args.archive:
        cli.error("--archive and --remote cannot both be used")
    remote = remote_support.remote_for_args(args)
    with op_handler(remote):
        remote.list_runs(**_list_runs_kw(args))

def _list_runs_kw(args):
    names = _runs_filter_names() + [
        "all",
        "deleted",
        "more",
        "verbose",
    ]
    ignore = [
        "archive",
        "json",
        "remote",
    ]
    return _arg_kw(args, names, ignore)

def _runs_filter_names():
    return [
        "completed",
        "error",
        "labels",
        "marked",
        "ops",
        "pending",
        "running",
        "terminated",
        "unlabeled",
        "unmarked",
    ]

def _runs_select_names():
    return _runs_filter_names() + ["runs"]

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
        run_id = remote.run_op(**_run_kw(args))
    except remotelib.RunFailed as e:
        _handle_run_failed(e, remote)
    except remotelib.RemoteProcessError as e:
        _handle_remote_process_error(e)
    except remotelib.RemoteProcessDetached as e:
        run_id = e.args[0]
        cli.out(
            "\nDetached from remote run {run_id} (still running)\n"
            "To re-attach use 'guild watch {run_id} -r {remote}'"
            .format(run_id=run_id[:8], remote=args.remote))
    except remotelib.OperationError as e:
        _handle_op_error(e, remote)
    except remotelib.OperationNotSupported:
        _handle_not_supported(remote)
    else:
        if args.no_wait:
            cli.out(
                "{run_id} is running remotely on {remote}\n"
                "To watch use 'guild watch {run_id} -r {remote}'"
                .format(run_id=run_id[:8], remote=args.remote))

def _handle_run_failed(e, remote):
    run_id = os.path.basename(e.remote_run_dir)
    cli.out(
        "Try 'guild runs info %s -O -r %s' to view its output."
        % (run_id[:8], remote.name), err=True)
    cli.error()

def _handle_op_error(e, remote):
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
        "disable_plugins",
        "flags",
        "force_flags",
        "gpus",
        "init_trials",
        "label",
        "max_trials",
        "maximize",
        "minimize",
        "needed",
        "no_gpus",
        "no_wait",
        "opt_flags",
        "optimize",
        "optimizer",
        "opspec",
        "random_seed",
        "restart",
        "stop_after",
    ]
    ignore = [
        "background",
        "pidfile",
        "help_model",
        "help_op",
        "print_cmd",
        "print_env",
        "print_trials",
        "quiet",
        "remote",
        "rerun",
        "run_dir",
        "save_trials",
        "set_trace",
        "stage",
        "yes",
    ]
    return _arg_kw(args, names, ignore)

def one_run(run_id_prefix, args):
    assert args.remote
    remote = remote_support.remote_for_args(args)
    cli.note("Getting remote run info")
    try:
        return remote.one_run(run_id_prefix, ["flags"])
    except remotelib.RemoteProcessError as e:
        _handle_remote_process_error(e)
    except remotelib.OperationNotSupported:
        _handle_not_supported(remote)

def watch_run(args):
    assert args.remote
    remote = remote_support.remote_for_args(args)
    with op_handler(remote):
        remote.watch_run(**_watch_run_kw(args))

def _watch_run_kw(args):
    names = [
        "ops",
        "pid",
        "labels",
        "marked",
        "run",
        "unlabeled",
        "unmarked",
    ]
    ignore = [
        "remote",
    ]
    return _arg_kw(args, names, ignore)

def delete_runs(args):
    assert args.remote
    remote = remote_support.remote_for_args(args)
    with op_handler(remote):
        remote.delete_runs(**_delete_runs_kw(args))

def _delete_runs_kw(args):
    names = _runs_select_names() + ["permanent", "yes"]
    ignore = ["remote"]
    return _arg_kw(args, names, ignore)

def run_info(args):
    assert args.remote
    remote = remote_support.remote_for_args(args)
    with op_handler(remote):
        remote.run_info(**_run_info_kw(args))

def _run_info_kw(args):
    names = _runs_filter_names() + [
        "all_files",
        "deps",
        "env",
        "files",
        "follow_links",
        "output",
        "page_output",
        "run",
        "scalars",
        "source",
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
    with op_handler(remote):
        remote.check(**_check_kw(args))

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

def stop_runs(args):
    assert args.remote
    remote = remote_support.remote_for_args(args)
    with op_handler(remote):
        remote.stop_runs(**_stop_runs_kw(args))

def _stop_runs_kw(args):
    names = [
        "labels",
        "marked",
        "no_wait",
        "ops",
        "runs",
        "unlabeled",
        "unmarked",
        "yes",
    ]
    ignore = [
        "remote"
    ]
    return _arg_kw(args, names, ignore)

def restore_runs(args):
    assert args.remote
    remote = remote_support.remote_for_args(args)
    with op_handler(remote):
        remote.restore_runs(**_restore_runs_kw(args))

def _restore_runs_kw(args):
    names = _runs_select_names() + ["yes"]
    ignore = ["remote"]
    return _arg_kw(args, names, ignore)

def purge_runs(args):
    assert args.remote
    remote = remote_support.remote_for_args(args)
    with op_handler(remote):
        remote.purge_runs(**_restore_runs_kw(args))

def _purge_runs_kw(args):
    names = _runs_select_names() + ["yes"]
    ignore = ["remote"]
    return _arg_kw(args, names, ignore)

def label_runs(args):
    assert args.remote
    remote = remote_support.remote_for_args(args)
    with op_handler(remote):
        remote.label_runs(**_label_runs_kw(args))

def _label_runs_kw(args):
    names = _runs_select_names() + [
        "label",
        "clear",
        "yes"
    ]
    ignore = ["remote"]
    return _arg_kw(args, names, ignore)

def _handle_remote_process_error(e):
    cli.error(exit_status=e.exit_status)

def _handle_not_supported(remote):
    cli.error("%s does not support this operation" % remote.name)

def filtered_runs_for_pull(remote, args):
    cli.note("Getting remote run info")
    with op_handler(remote):
        return remote.filtered_runs(**_filtered_runs_for_pull_kw(args))

def _filtered_runs_for_pull_kw(args):
    names = _runs_filter_names()
    ignore = [
        "delete",
        "remote",
        "runs",
        "yes",
    ]
    return _arg_kw(args, names, ignore)

def push_runs(remote, runs, args):
    with op_handler(remote):
        remote.push(runs, args.delete)

def pull_runs(remote, runs, args):
    with op_handler(remote):
        remote.pull(runs, args.delete)
