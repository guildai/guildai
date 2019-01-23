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

import os
import logging

import daemonize
import psutil

from guild import var
from guild import util

DEFAULT_LOG_MAX_SIZE = 102400
DEFAULT_LOG_BACKUPS = 1

class ServiceError(Exception):
    pass

class Running(ServiceError):

    def __init__(self, name, pidfile):
        super(Running, self).__init__(name, pidfile)
        self.name = name
        self.pidfile = pidfile

class NotRunning(ServiceError):

    def __init__(self, name):
        super(NotRunning, self).__init__(name)
        self.name = name

class PidfileError(ServiceError):

    def __init__(self, pidfile, error):
        super(PidfileError, self).__init__(pidfile, error)
        self.pidfile = pidfile
        self.error = error

class OrphanedProcess(ServiceError):

    def __init__(self, pid, pidfile):
        super(OrphanedProcess, self).__init__(pid, pidfile)
        self.pid = pid
        self.pidfile = pidfile

class Status(object):

    def __init__(self, running, pid=None):
        self.running = running
        self.pid = pid

def start(name, f, foreground,
          log_max_size=DEFAULT_LOG_MAX_SIZE,
          log_backups=DEFAULT_LOG_BACKUPS):
    log = _init_log(name, log_max_size, log_backups, foreground)
    if foreground:
        _run(f, log)
    else:
        _start(name, f, log)

def _init_log(name, max_size, backups, foreground):
    if foreground:
        handler = logging.StreamHandler()
    else:
        logfile = var.logfile(name)
        util.ensure_dir(os.path.dirname(logfile))
        handler = logging.handlers.RotatingFileHandler(
            logfile,
            maxBytes=max_size,
            backupCount=backups)
    handler.setFormatter(logging.Formatter(
        "%(asctime)s %(message)s",
        "%Y-%m-%d %H:%M:%S"))
    log = logging.getLogger("guild." + name)
    log.propagate = False
    log.addHandler(handler)
    return log

def _run(f, log, log_level=None):
    # When daemonized, log.level is 10 for some reason - reset to
    # log_level if provided.
    if log_level is not None:
        log.setLevel(log_level)
    try:
        f(log)
    except:
        log.exception("service callback")

def _start(name, f, log):
    pidfile = var.pidfile(name)
    if os.path.exists(pidfile):
        raise Running(name, pidfile)
    util.ensure_dir(os.path.dirname(pidfile))
    # Save original log level to workaround issue with daemonization
    # (see note in _run).
    log_level = log.getEffectiveLevel()
    daemon = daemonize.Daemonize(
        app=name,
        action=lambda: _run(f, log, log_level),
        pid=pidfile,
        keep_fds=_log_fds(log))
    daemon.start()

def _log_fds(log):
    return [h.stream.fileno() for h in log.handlers if hasattr(h, "stream")]

def stop(name, title=None):
    log = logging.getLogger("guild")
    title = title or name
    pidfile = var.pidfile(name)
    if not os.path.exists(pidfile):
        raise NotRunning(name)
    try:
        pid = _read_pid(pidfile)
    except Exception:
        if log.getEffectiveLevel() <= logging.DEBUG:
            log.exception("reading %s", pidfile)
        log.info(
            "%s has an invalid pidfile (%s) - deleting",
            title, pidfile)
        util.ensure_deleted(pidfile)
    else:
        try:
            proc = psutil.Process(pid)
        except psutil.NoSuchProcess:
            log.info("%s did not shut down cleanly - cleaning up", title)
            util.ensure_deleted(pidfile)
        else:
            log.info("Stopping %s (pid %i)", title, proc.pid)
            proc.terminate()

def status(name):
    pidfile = var.pidfile(name)
    if os.path.exists(pidfile):
        try:
            pid = _read_pid(pidfile)
        except Exception as e:
            raise PidfileError(pidfile, e)
        else:
            try:
                proc = psutil.Process(pid)
            except psutil.NoSuchProcess:
                raise OrphanedProcess(pid, pidfile)
            else:
                return Status(proc.is_running(), pid)
    else:
        return Status(False)

def _read_pid(pidfile):
    raw = open(pidfile, "r").read()
    return int(raw.strip())
