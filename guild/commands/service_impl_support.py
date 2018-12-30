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

from guild import cli
from guild import service

def start(name, f, args, title=None, status_cmd=None, stop_cmd=None,
          log_max_size=service.DEFAULT_LOG_MAX_SIZE,
          log_backups=service.DEFAULT_LOG_BACKUPS):
    title = title or name
    status_cmd = status_cmd or "guild sys %s status" % name
    stop_cmd = stop_cmd or "guild sys %s stop" % name
    if not args.foreground:
        cli.out("Starting %s (use '%s' to stop)" % (title, stop_cmd))
    try:
        service.start(name, f, args.foreground, log_max_size, log_backups)
    except service.Running:
        cli.error(
            "%s is already running (use '%s' to verify)"
            % (title, status_cmd))

def stop(name, title):
    try:
        service.stop(name, title)
    except service.NotRunning:
        cli.out("%s is not running" % title)

def status(name, title, stop_cmd=None):
    stop_cmd = stop_cmd or "guild sys %s stop" % name
    try:
        status = service.status(name)
    except service.PidfileError as e:
        cli.error("error reading pid in %s: %s" % (e.pidfile, e.error))
    except service.OrphanedProcess as e:
        cli.out(
            "Shutdown timer is NOT running (orphaned pid in "
            "%s - use '%s' to cleanup)"
            % (e.pidfile, stop_cmd))
    else:
        if status.running:
            cli.out("%s is running (pid %i)" % (title, status.pid))
        else:
            cli.out("%s is not running" % title)
