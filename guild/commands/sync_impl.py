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

from . import runs_impl

log = logging.getLogger("core")

def main(args):
    for run in runs_impl.runs_for_args(args):
        _maybe_sync_run(run)

def _maybe_sync_run(run):
    remote_lock = _remote_lock_for_run(run)
    if remote_lock:
        plugin_name, lock_config = _parse_remote_lock(remote_lock)
        _try_sync(run, plugin_name, lock_config)

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

def _try_sync(run, plugin_name, lock_config):
    try:
        plugin = guild.plugin.for_name(plugin_name)
    except LookupError:
        log.warn(
            "error syncing run '%s': plugin '%s' not available",
            run.id, plugin_name)
    else:
        plugin.sync_run(run, lock_config)
