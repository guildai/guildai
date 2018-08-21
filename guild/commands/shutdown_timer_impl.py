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
import os
import subprocess
import time

import daemonize
import psutil

from guild import cli
from guild import util
from guild import var

INTERVAL = 5
LOG_MAX_SIZE = 102400
LOG_BACKUPS = 1

def start(args):
    log = _init_log(args)
    cli.out("Running shutdown timer with timeout of %i minutes" % args.timeout)
    if args.dont_shutdown:
        cli.out(
            cli.style(
                "Shutdown timer WILL NOT SHUTDOWN system because "
                "--dont-shutdown was used",
                bold=True))
    if args.foreground:
        _run(args, log)
    else:
        _start(args, log)

def _init_log(args):
    if args.foreground:
        handler = logging.StreamHandler()
    else:
        logfile = var.logfile("SHUTDOWN-TIMER")
        util.ensure_dir(os.path.dirname(logfile))
        handler = logging.handlers.RotatingFileHandler(
            logfile,
            maxBytes=LOG_MAX_SIZE,
            backupCount=LOG_BACKUPS)
    handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
    log = logging.getLogger("guild.shutdown_timer")
    log.propagate = False
    log.addHandler(handler)
    return log

def _run(args, log):
    last = _now()
    while True:
        last = _check_activity(last, log)
        if _timeout(last, args.timeout):
            _shutdown(args, last, log)
            break
        time.sleep(INTERVAL)
    log.info("Quitting")

def _check_activity(last, log):
    pids = _guild_ops()
    if pids:
        log.info("Runs: %s", ",".join(map(str, pids)))
        return _now()
    else:
        log.debug("No runs for %i seconds", (_now() - last))
        return last

def _guild_ops():
    return [
        p.pid for p in psutil.process_iter(attrs=['cmdline'])\
        if "guild.op_main" in p.info["cmdline"]]

def _timeout(last, timeout):
    return _now() >= (last + (timeout * 60))

def _now():
    return int(time.time())

def _shutdown(args, last, log):
    if args.dont_shutdown:
        log.info("SHUTDOWN would occur but --dont-shutdown was used")
        return
    log.info(
        "NO RUNS FOR %i SECONDS - SHUTTING DOWN SYSTEM",
        (_now() - last))
    try:
        subprocess.check_call(["shutdown", "+%s" % args.grace_period])
    except Exception:
        log.exception("shutting down")

def _start(args, log):
    pidfile = var.pidfile("SHUTDOWN-TIMER")
    if os.path.exists(pidfile):
        cli.error(
            "shutdown timer is already running "
            "(use 'guild sys shutdown-timer status' to verify)")
    util.ensure_dir(os.path.dirname(pidfile))
    daemon = daemonize.Daemonize(
        app="guild",
        action=lambda: _run(args, log),
        pid=pidfile,
        keep_fds=_log_fds(log))
    cli.out(
        "Starting shutdown timer "
        "(use 'guild sys shutdown-timer stop' to stop)")
    daemon.start()

def _log_fds(log):
    return [h.stream.fileno() for h in log.handlers if hasattr(h, "stream")]

def stop():
    pidfile = var.pidfile("SHUTDOWN-TIMER")
    if not os.path.exists(pidfile):
        cli.out("Shutdown timer is not running")
        return
    try:
        pid = _read_pid(pidfile)
    except Exception:
        cli.out(
            "Shutdown timer has an invalid pidfile (%s) - deleting"
            % pidfile)
        _delete_pidfile(pidfile)
    else:
        try:
            proc = psutil.Process(pid)
        except psutil.NoSuchProcess:
            cli.out("Shutdown timer did not shut down cleanly - cleaning up")
            _delete_pidfile(pidfile)
        else:
            cli.out("Stopping shutdown timer (pid %i)" % proc.pid)
            proc.terminate()

def _delete_pidfile(pidfile):
    try:
        os.remove(pidfile)
    except OSError:
        cli.error(
            "Error deleting pidfile %s: %s\n"
            "Try deleting the file manually."
            % pidfile)

def status():
    pidfile = var.pidfile("SHUTDOWN-TIMER")
    if os.path.exists(pidfile):
        try:
            pid = _read_pid(pidfile)
        except Exception as e:
            cli.error("error reading pid in %s: %s" % (pidfile, e))
        else:
            try:
                proc = psutil.Process(pid)
            except psutil.NoSuchProcess:
                cli.out(
                    "Shutdown timer is NOT running "
                    "(orphaned pid in %s - use 'guild sys shutdown-timer stop' "
                    "to cleanup)"
                    % pidfile)
            else:
                cli.out("Shutdown timer is running (pid %i)" % proc.pid)
    else:
        cli.out("Shutdown timer is not running")

def _read_pid(pidfile):
    raw = open(pidfile, "r").read()
    return int(raw.strip())
