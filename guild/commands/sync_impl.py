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

import guild.plugin

from guild import cli
from guild import remote_run_support

from . import runs_impl

log = logging.getLogger("guild")

def main(args):
    runs = runs_impl.runs_for_args(args)
    if args.watch:
        _watch(runs)
    else:
        for run in runs:
            _maybe_sync_run(run, False)

def _watch(runs):
    if not runs:
        cli.error(
            "cannot find any runs to watch\n"
            "Try 'guild runs list' for a list of runs.")
    for run in runs:
        if run.status == "running":
            cli.out("Watching %s" % run.id)
            _maybe_sync_run(run, True)
            break
    else:
        cli.error("there are no active runs to watch")

def _maybe_sync_run(run, watch):
    remote_lock = remote_run_support.lock_for_run(run)
    if remote_lock:
        _try_sync(run, remote_lock, watch)

def _try_sync(run, remote_lock, watch):
    try:
        plugin = guild.plugin.for_name(remote_lock.plugin_name)
    except LookupError:
        log.warning(
            "error syncing run '%s': plugin '%s' not available",
            run.id, remote_lock.plugin_name)
    else:
        plugin.sync_run(run, dict(watch=watch))
