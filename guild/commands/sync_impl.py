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

import guild.plugin

from guild import cli
from . import runs_impl

log = logging.getLogger("core")

def main(args):
    runs = _runs(args)
    if args.watch:
        _watch(runs)
    else:
        for run in runs:
            _maybe_sync_run(run, False)

def _runs(args):
    runs = runs_impl.runs_for_args(args)
    if not args.runs:
        return runs
    return runs_impl.selected_runs(runs, args.runs)

def _watch(runs):
    if not runs:
        cli.error(
            "cannot find any runs to watch\n"
            "Try 'guild runs list' for a list of runs.")
    if len(runs) > 1:
        cli.error(
            "--watch may only be used with one run (found %i)\n"
            "Try 'guild runs list' and specify the ID of the run you want to watch."
            % len(runs))
    assert len(runs) == 1, runs
    _maybe_sync_run(runs[0], True)

def _maybe_sync_run(run, watch):
    remote_lock = _remote_lock_for_run(run)
    if remote_lock:
        plugin_name, lock_config = _parse_remote_lock(remote_lock)
        _try_sync(run, plugin_name, lock_config, watch)

def _remote_lock_for_run(run):
    try:
        f = open(run.guild_path("LOCK.remote"), "r")
    except IOError:
        return None
    else:
        return f.read()

def _parse_remote_lock(raw):
    parts = raw.split(":", 1)
    if len(parts) == 1:
        return parts[0], ""
    else:
        return parts[0], parts[1]

def _try_sync(run, plugin_name, lock_config, watch):
    try:
        plugin = guild.plugin.for_name(plugin_name)
    except LookupError:
        log.warn(
            "error syncing run '%s': plugin '%s' not available",
            run.id, plugin_name)
    else:
        kw = dict(
            lock_config=lock_config,
            watch=watch,
        )
        plugin.sync_run(run, **kw)
