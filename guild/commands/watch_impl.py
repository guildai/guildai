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

import logging
import sys
import time

import psutil

from guild import cli
from guild import run as runlib
from guild import var

log = logging.getLogger("guild")

def main(args):
    assert args.pid
    pid = _pid_arg(args.pid)
    run = _run_for_pid(pid)
    _tail(run)
    _print_run_status(run)

def _pid_arg(pid):
    try:
        return int(pid)
    except ValueError:
        return _read_pid(pid)

def _read_pid(path):
    try:
        f = open(path, "r")
    except OSError as e:
        cli.error(e)
    else:
        raw = f.readline().strip()
        try:
            return int(raw)
        except ValueError:
            cli.error("pidfile %s does not contain a valid pid" % path)

def _run_for_pid(pid):
    for run_id, run_dir in var.iter_run_dirs():
        run = runlib.Run(run_id, run_dir)
        if run.pid and (run.pid == pid or _parent_pid(run.pid) == pid):
            return run
    cli.error("cannot find run for pid %i" % pid)

def _parent_pid(pid):
    return psutil.Process(pid).parent().pid

def _tail(run):
    cli.out("Watching run %s" % run.id, err=True)
    proc = psutil.Process(run.pid)
    output_path = run.guild_path("output")
    f = None
    while proc.is_running():
        f = f or _try_open(output_path)
        if not f:
            time.sleep(1.0)
            continue
        line = f.readline()
        if not line:
            time.sleep(0.1)
            continue
        sys.stdout.write(line)

def _try_open(path):
    try:
        return open(path, "r")
    except OSError as e:
        if e.errno != 2:
            raise
        return None

def _print_run_status(run):
    cli.out(
        "Run %s stopped with a status of '%s'"
        % (run.short_id, run.status), err=True)
