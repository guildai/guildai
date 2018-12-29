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

import subprocess
import time

import psutil

from . import service_impl_support

NAME = "shutdown-timer"
TITLE = "Shutdown timer"

INTERVAL = 5
LOG_HEARTBEAT = 60

def start(args):
    run = lambda log: _run(args, log)
    service_impl_support.start(NAME, run, args, TITLE)

def stop():
    service_impl_support.stop(NAME, TITLE)

def status():
    service_impl_support.status(NAME, TITLE)

def _run(args, log):
    log.info("%s started with timeout = %im", TITLE, args.timeout)
    if args.dont_shutdown:
        log.info(
            "%s WILL NOT SHUTDOWN system because "
            "--dont-shutdown was used", TITLE)
    last_activity = _now()
    while True:
        try:
            last_activity = _check_activity(last_activity, log)
            if _timeout(last_activity, args.timeout):
                _shutdown(args, log)
                break
            time.sleep(INTERVAL)
        except KeyboardInterrupt:
            break
    log.info("Stopping")

def _check_activity(last_activity, log):
    pids = _guild_ops()
    now = _now()
    log_f = _log_function(log, now, pids)
    if pids:
        log_f("Active runs (pids): %s", ",".join(map(str, pids)))
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
        p.pid for p in psutil.process_iter(attrs=["cmdline"])
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
