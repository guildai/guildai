# Copyright 2017-2020 TensorHub, Inc.
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
import time

from guild import cli
from guild import click_util
from guild import remote as remotelib
from guild import remote_run_support

from . import remote_impl_support
from . import runs_impl

log = logging.getLogger("guild")


class State(object):
    def __init__(self, args):
        self.ran_once = False
        self.watch = args.watch
        self.interval = args.interval

    def loop(self):
        if not self.ran_once:
            self.ran_once = True
            return True
        elif self.watch:
            time.sleep(self.interval)
            return True
        else:
            return False


def main(args):
    state = State(args)
    while state.loop():
        for run in runs_impl.runs_for_args(args):
            _maybe_sync_run(run)


def _maybe_sync_run(run):
    if run.status != "running":
        log.debug("run %s status is '%s', skipping sync", run.id, run.status)
        return
    log.debug("getting remote run %s", run.id)
    remote_run = _remote_run_for_local_run(run)
    log.debug("remote run for %s: %s", run.id, _remote_run_desc(remote_run))
    if remote_run:
        cli.out("Syncing %s" % run.id)
        _sync_remote_run(remote_run)


def _remote_run_desc(remote_run):
    if not remote_run:
        return "not found"
    return "%s (%s)" % (remote_run.id, remote_run.status)


def _remote_run_for_local_run(local_run):
    remote_lock = remote_run_support.lock_for_run(local_run)
    if not remote_lock:
        return None
    remote = _remote_for_lock(remote_lock, local_run)
    if not remote:
        return None
    return _remote_run(remote, local_run.id)


def _remote_for_lock(remote_lock, local_run):
    try:
        return remotelib.for_name(remote_lock.remote_name)
    except LookupError:
        log.warning(
            "Cannot sync run %s: remote '%s' not defined",
            local_run.id,
            remote_lock.remote_name,
        )
        return None


def _remote_run(remote, run_id):
    try:
        remote_run = remote.one_run(run_id)
    except remotelib.RemoteProcessError:
        if log.getEffectiveLevel() <= logging.DEBUG:
            log.exception("getting one run %s from %s", run_id, remote.name)
        return None
    else:
        remote_run.remote = remote
        return remote_run


def _sync_remote_run(remote_run):
    assert remote_run.remote
    remote_name = remote_run.remote.name
    pull_args = click_util.Args(remote=remote_name, delete=False)
    try:
        remote_impl_support.pull_runs([remote_run], pull_args)
    except Exception as e:
        if log.getEffectiveLevel() <= logging.DEBUG:
            log.exception("pull %s from %s", remote_run.id, remote_name)
        else:
            log.error("error pulling %s from %s: %s", remote_run.id, remote_name, e)
