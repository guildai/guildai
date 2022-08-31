# Copyright 2017-2022 RStudio, PBC
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

from guild import cli
from guild import service


def start(
    name,
    f,
    args,
    title=None,
    status_cmd=None,
    stop_cmd=None,
    log_max_size=service.DEFAULT_LOG_MAX_SIZE,
    log_backups=service.DEFAULT_LOG_BACKUPS,
):
    title = title or name
    status_cmd = status_cmd or f"guild sys {name} status"
    stop_cmd = stop_cmd or f"guild sys {name} stop"
    if not args.foreground:
        cli.out(f"Starting {title} (use '{stop_cmd}' to stop)")
    try:
        service.start(name, f, args.foreground, log_max_size, log_backups)
    except service.Running:
        cli.error(f"{title} is already running (use '{status_cmd}' to verify)")


def stop(name, title):
    try:
        service.stop(name, title)
    except service.NotRunning:
        cli.out(f"{title} is not running")


def status(name, title, stop_cmd=None):
    stop_cmd = stop_cmd or f"guild sys {name} stop"
    try:
        status = service.status(name)
    except service.PidfileError as e:
        cli.error(f"error reading pid in {e.pidfile}: {e.error}")
    except service.OrphanedProcess as e:
        cli.out(
            "Shutdown timer is NOT running (orphaned pid in "
            f"{e.pidfile} - use '{stop_cmd}' to cleanup)"
        )
    else:
        if status.running:
            cli.out(f"{title} is running (pid {status.pid})")
        else:
            cli.out(f"{title} is not running")
