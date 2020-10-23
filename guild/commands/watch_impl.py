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
import os
import re
import sys
import time

import psutil

from guild import cli
from guild import run as runlib
from guild import util
from guild import var

from . import remote_impl_support
from . import runs_impl

log = logging.getLogger("guild")

TAIL_BUFFER = 4096


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
    if args.run or args.filter_ops or args.filter_labels or args.filter_unlabeled:
        cli.error("--pid may not be used with other options")


def _watch_pid(args):
    run = _run_for_pid_arg(args.pid)
    _watch_run(run)


def _run_for_pid_arg(pid):
    return util.find_apply(
        [
            _run_for_job_pidfile,
            _run_for_pidfile,
            _run_for_pid,
            _handle_no_run_for_pid_arg,
        ],
        pid,
    )


def _run_for_job_pidfile(pid_arg):
    m = re.search(r"(.+)/\.guild/JOB$", pid_arg)
    if not m:
        return None
    run_dir = m.group(1)
    return runlib.for_dir(run_dir)


def _run_for_pidfile(pid_arg):
    pid = _read_pid(pid_arg)
    if pid is None:
        return None
    return _run_for_pid(pid)


def _read_pid(path):
    try:
        f = open(path, "r")
    except IOError as e:
        if e.errno != 2:
            raise
        return None
    else:
        raw = f.readline().strip()
        try:
            return int(raw)
        except ValueError:
            cli.error("pidfile %s does not contain a valid pid" % path)


def _run_for_pid(pid):
    pid = _try_int(pid)
    if pid is None:
        return None
    for run_id, run_dir in var.iter_run_dirs():
        run = runlib.Run(run_id, run_dir)
        if run.pid and (run.pid == pid or _parent_pid(run.pid) == pid):
            return run
    cli.error("cannot find run for pid %i" % pid)


def _try_int(pid):
    try:
        return int(pid)
    except ValueError:
        return None


def _parent_pid(pid):
    try:
        p = psutil.Process(pid)
    except psutil.NoSuchProcess:
        return None
    else:
        return p.parent().pid


def _handle_no_run_for_pid_arg(pid_arg):
    # Assume pid_arg is a pidfile path.
    cli.error("%s does not exist" % pid_arg)


def _watch_run(run):
    try:
        _tail(run)
        _print_run_status(run)
    except KeyboardInterrupt:
        _stopped_msg(run)


def _stopped_msg(run):
    msg = "\nStopped watching %s" % run.id
    if run.pid and psutil.Process(run.pid).is_running():
        msg += " (still running)"
    cli.out(msg)


def _tail(run):
    if os.getenv("NO_WATCHING_MSG") != "1":
        cli.out("Watching run %s" % run.id, err=True)
    out = _stream_buffer(sys.stdout)
    if run.pid is None:
        _print_run_output(run, out)
        return
    proc = psutil.Process(run.pid)
    output_path = run.guild_path("output")
    f = _wait_for_output(proc, output_path)
    if not f:
        return
    read = 0
    with f:
        while True:
            f.seek(read)
            tail = f.read(TAIL_BUFFER)
            if tail:
                read += len(tail)
                out.write(tail)
                out.flush()
            elif proc.is_running():
                time.sleep(0.1)
            else:
                break


def _stream_buffer(f):
    try:
        return f.buffer
    except AttributeError:
        return f


def _print_run_output(run, out):
    output_path = run.guild_path("output")
    f = _try_open(output_path)
    if not f:
        return
    while True:
        tail = f.read(TAIL_BUFFER)
        if not tail:
            break
        out.write(tail)
        out.flush()


def _try_open(path):
    try:
        return open(path, "rb")
    except (IOError, OSError) as e:
        if e.errno != 2:
            raise
        return None


def _wait_for_output(proc, output_path):
    while proc.is_running():
        f = _try_open(output_path)
        if f:
            return f
        time.sleep(1.0)
    return _try_open(output_path)


def _print_run_status(run):
    cli.out("Run %s stopped with a status of '%s'" % (run.id, run.status), err=True)


def _watch_default_running(args):
    args.status_running = True
    runs = runs_impl.filtered_runs(args)
    if not runs:
        cli.error(
            "nothing to watch\n"
            "You can view the output of a specific run using "
            "'guild watch RUN'."
        )
    _watch_run(runs[0])


def _watch_remote(args):
    try:
        remote_impl_support.watch_run(args)
    except KeyboardInterrupt:
        cli.out("\nStopped watching remote run")
