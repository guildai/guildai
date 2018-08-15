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

def _run_kw(args):
    names = [
        "args",
        "disable_plugins",
        "gpus",
        "label",
        "no_gpus",
        "opspec",
        "rerun",
        "restart",
    ]
    ignore = [
        "background",
        "help_model",
        "help_op",
        "no_wait",
        "print_cmd",
        "print_env",
        "quiet",
        "remote",
        "run_dir",
        "set_trace",
        "stage",
        "workflow",
        "yes",
    ]
    return _arg_kw(args, names, ignore)
