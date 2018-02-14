# Copyright 2017 TensorHub, Inc.
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
import signal

import guild.plugin

from guild import cli
from guild import cmd_impl_support
from guild import remote_run_support
from guild import util
from guild import var

from . import runs_impl

log = logging.getLogger("guild")

def main(args):
    runs = _selected_runs(args)
    preview = [runs_impl.format_run(run) for run in runs]
    if not args.yes:
        cli.out("You are about to stop the following runs:")
        cols = ["short_index", "operation", "started", "status", "label"]
        cli.table(preview, cols=cols, indent=2)
    if args.yes or cli.confirm("Stop these runs?"):
        for run in runs:
            _stop_run(run, args)

def _selected_runs(args):
    selected = []
    for spec in args.runs:
        matches = list(var.find_runs(spec))
        run_id, _ = cmd_impl_support.one_run(matches, spec)
        run = runs_impl.init_run(var.get_run(run_id))
        if run.status != "running":
            log.info("run %s is already stopped, skipping", run.short_id)
            continue
        selected.append(run)
    return selected

def _stop_run(run, args):
    remote_lock = remote_run_support.lock_for_run(run)
    if remote_lock:
        _try_stop_remote_run(run, remote_lock, args.no_wait)
    else:
        _try_stop_local_run(run)

def _try_stop_remote_run(run, remote_lock, no_wait):
    try:
        plugin = guild.plugin.for_name(remote_lock.plugin_name)
    except LookupError:
        log.warning(
            "error syncing run '%s': plugin '%s' not available",
            run.id, remote_lock.plugin_name)
    else:
        cli.out("Stopping %s (remote)" % run.short_id)
        plugin.stop_run(run, lock_config=remote_lock.config, no_wait=no_wait)

def _try_stop_local_run(run):
    pid = run.pid
    if pid and util.pid_exists(pid):
        cli.out("Stopping %s (pid %i)" % (run.short_id, run.pid))
        os.kill(pid, signal.SIGTERM)
