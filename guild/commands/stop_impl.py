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

import os
import signal

from guild import cli
from guild import cmd_impl_support
from guild import remote_run_support
from guild import util
from guild import var

def main(args):
    for spec in args.runs:
        matches = list(var.find_runs(spec))
        run_id, _ = cmd_impl_support.one_run(matches, spec)
        run = var.get_run(run_id)
        if run.status != "running":
            cli.out("run %s is already stopped" % run.short_id)
            continue
        _stop_run(run)

def _stop_run(run):
    remote_lock = remote_run_support.lock_for_run(run)
    if remote_lock:
        _try_stop_remote_run(run, remote_lock)
    _try_stop_local_run(run)

def _try_stop_remote_run(run, lock):
    print("############ remote info", lock.plugin_name, lock.config)

def _try_stop_local_run(run):
    pid = run.pid
    if pid and util.pid_exists(pid):
        cli.out("stopping %s (pid %i)" % (run.short_id, run.pid))
        os.kill(pid, signal.SIGTERM)
