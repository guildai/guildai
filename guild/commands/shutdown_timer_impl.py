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
LOG_HEARTBEAT = 60

def start(args):
    log = _init_log(args)
    log.info("Shutdown timer started with timeout = %im", args.timeout)
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
        logfile = var.logfile("shutdown-timer")
        util.ensure_dir(os.path.dirname(logfile))
        handler = logging.handlers.RotatingFileHandler(
            logfile,
            maxBytes=LOG_MAX_SIZE,
            backupCount=LOG_BACKUPS)
    handler.setFormatter(logging.Formatter(
        "%(asctime)s %(message)s",
        "%Y-%m-%d %H:%M:%S"))
    log = logging.getLogger("guild.shutdown_timer")
    log.propagate = False
    log.addHandler(handler)
    return log

def _run(args, log, log_level=None):
    # When daemonized, log.level is 10 for some reason - reset to
    # log_level if provided.
    if log_level is not None:
        log.setLevel(log_level)
    last_activity = _now()
    while True:
        last_activity = _check_activity(last_activity, log)
        if _timeout(last_activity, args.timeout):
            _shutdown(args, log)
            break
        time.sleep(INTERVAL)
    log.info("Quitting")

def _check_activity(last_activity, log):
    pids = _guild_ops()
    now = _now()
    log_f = _log_function(log, now, pids)
    if pids:
        log_f("Active runs: %s", ",".join(map(str, pids)))
        return now
    else:
        log_f("No runs for %s", _format_duration(now - last_activity))
        return last_activity

def _format_duration(seconds):
    if seconds < 60:
        return "%i second(s)" % seconds
    else:
        return "%i minute(s)" % (seconds // 60)

def _log_function(log, now, pids):
    # Tricky function that decides whether to log as info or debug.
    # Uses lazily assigned log state to determine whether pids have
    # changed or LOG_HEARTBEAT seconds have ellapsed since the last
    # info msg.
    try:
        last_pids = sorted(log.last_pids)
    except AttributeError:
        last_pids = []
    if last_pids != pids:
        log.last_pids = pids
        log.last_log = now
        return log.info
    try:
        last_log = log.last_log
    except AttributeError:
        log.last_log = last_log = now
    if now >= last_log + LOG_HEARTBEAT:
        log.last_log = now
        return log.info
    else:
        return log.debug

def _guild_ops():
    return [
        p.pid for p in psutil.process_iter(attrs=['cmdline'])\
        if "guild.op_main" in p.info["cmdline"]]

def _timeout(last, timeout):
    return _now() >= (last + (timeout * 60))

def _now():
    return int(time.time())

def _shutdown(args, log):
    log.info("RUN ACTIVITY TIMEOUT - SHUTTING DOWN SYSTEM")
    cmd = ["shutdown", "+%s" % args.grace_period]
    if args.su:
        cmd.insert(0, "sudo")
    log.debug("shutdown cmd: %r", cmd)
    if args.dont_shutdown:
        log.info("SHUTDOWN would occur but --dont-shutdown was used")
        return
    try:
        subprocess.check_call(cmd)
    except Exception:
        log.exception("shutdown")

def _start(args, log):
    pidfile = var.pidfile("shutdown-timer")
    if os.path.exists(pidfile):
        cli.error(
            "shutdown timer is already running "
            "(use 'guild sys shutdown-timer status' to verify)")
    util.ensure_dir(os.path.dirname(pidfile))
    # Save original log level to workaround issue with daemonization
    # (see note in _run).
    log_level = log.getEffectiveLevel()
    daemon = daemonize.Daemonize(
        app="guild",
        action=lambda: _run(args, log, log_level),
        pid=pidfile,
        keep_fds=_log_fds(log))
    cli.out(
        "Starting shutdown timer "
        "(use 'guild sys shutdown-timer stop' to stop)")
    daemon.start()

def _log_fds(log):
    return [h.stream.fileno() for h in log.handlers if hasattr(h, "stream")]

def stop():
    pidfile = var.pidfile("shutdown-timer")
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
    pidfile = var.pidfile("shutdown-timer")
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
