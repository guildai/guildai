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
import os
import re
import sys
import time

import psutil

from guild import cli
from guild import run as runlib
from guild import var

from . import remote_impl_support
from . import runs_impl

log = logging.getLogger("guild")

def main(args, ctx):
    if args.pid:
        _check_non_pid_args(args)
        _watch_pid(args)
    elif args.remote:
        _watch_remote(args)
    elif args.run:
        run = runs_impl.one_run(args, ctx)
        _watch_run(run)
    else:
        _watch_default_running(args)

def _check_non_pid_args(args):
    if (args.run or
        args.ops or
        args.labels or
        args.unlabeled):
        cli.error("--pid may not be used with other options")

def _watch_pid(args):
    pid = _pid_arg(args.pid)
    run = _run_for_pid(pid)
    _watch_run(run)

def _pid_arg(pid):
    try:
        return int(pid)
    except ValueError:
        return _read_pid(pid)

def _read_pid(path):
    try:
        f = open(path, "r")
    except IOError as e:
        if e.errno != 2:
            raise
        _handle_missing_pidfile(path)
    else:
        raw = f.readline().strip()
        try:
            return int(raw)
        except ValueError:
            cli.error("pidfile %s does not contain a valid pid" % path)

def _handle_missing_pidfile(path):
    m = re.search(r"(.+)/\.guild/JOB$", path)
    if m:
        run_dir = m.group(1)
        _handle_run_error(run_dir)
    else:
        cli.error("%s does not exist" % path)

def _handle_run_error(run_dir):
    run_id = os.path.basename(run_dir)
    cli.error(
        "JOB for %s is no longer running" % run_id,
        exit_status=2)

def _run_for_pid(pid):
    for run_id, run_dir in var.iter_run_dirs():
        run = runlib.Run(run_id, run_dir)
        if run.pid and (run.pid == pid or _parent_pid(run.pid) == pid):
            return run
    cli.error("cannot find run for pid %i" % pid)

def _parent_pid(pid):
    try:
        p = psutil.Process(pid)
    except psutil.NoSuchProcess:
        return None
    else:
        return p.parent().pid

def _watch_run(run):
    try:
        _tail(run)
        _print_run_status(run)
    except KeyboardInterrupt:
        if os.getenv("NO_WATCHING_MSG") != "1":
            _stopped_msg(run)

def _stopped_msg(run):
    msg = "\nStopped watching %s" % run.short_id
    if run.pid and psutil.Process(run.pid).is_running():
        msg += " (still running)"
    cli.out(msg)

def _tail(run):
    if os.getenv("NO_WATCHING_MSG") != "1":
        cli.out("Watching run %s" % run.id, err=True)
    if run.pid is None:
        _print_output(run)
        return
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
        sys.stdout.flush()

def _print_output(run):
    output_path = run.guild_path("output")
    f = _try_open(output_path)
    if not f:
        return
    while True:
        line = f.readline()
        if not line:
            break
        sys.stdout.write(line)
        sys.stdout.flush()

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

def _watch_default_running(args):
    args.running = True
    runs = runs_impl.filtered_runs(args)
    if not runs:
        cli.error(
            "nothing to watch\n"
            "You can view the output of a specific run using "
            "'guild watch RUN'.")
    _watch_run(runs[0])

def _watch_remote(args):
    try:
        remote_impl_support.watch_run(args)
    except KeyboardInterrupt:
        cli.out("\nStopped watching remote run")
