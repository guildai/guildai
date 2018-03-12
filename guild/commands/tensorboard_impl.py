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
import socket

from guild import cli
from guild import util

from . import runs_impl

log = logging.getLogger("guild")

MIN_MONITOR_INTERVAL = 5

class RunsMonitor(util.LoopingThread):

    STOP_TIMEOUT = 5

    def __init__(self, logdir, args):
        """Create a RunsMonitor.

        Note that run links are created initially by this
        function. Any errors result from user input will propagate
        during this call. Similar errors occuring after the monitor is
        started will be logged but will not propagate.
        """
        interval = min(args.refresh_interval, MIN_MONITOR_INTERVAL)
        super(RunsMonitor, self).__init__(
            cb=self.run_once,
            interval=interval,
            stop_timeout=self.STOP_TIMEOUT)
        self.logdir = logdir
        self.args = args
        self.run_once(exit_on_error=True)

    def run_once(self, exit_on_error=False):
        log.debug("Refreshing runs")
        try:
            runs = self._runs()
        except SystemExit as e:
            if exit_on_error:
                raise
            log.error(
                "An error occurred while reading runs. "
                "Use --debug for details.")
            log.debug(e)
        else:
            self._refresh_run_links(runs)

    def _runs(self):
        return runs_impl.runs_for_args(self.args)

    def _refresh_run_links(self, runs):
        to_delete = os.listdir(self.logdir)
        for run in runs:
            link_name = _format_run_name(run)
            link_path = os.path.join(self.logdir, link_name)
            if not os.path.exists(link_path):
                log.debug("Linking %s to %s", link_name, run.path)
                util.symlink(run.path, link_path)
            try:
                to_delete.remove(link_name)
            except ValueError:
                pass
        for link_name in to_delete:
            log.debug("Removing %s", link_name)
            os.remove(os.path.join(self.logdir, link_name))

def main(args):
    tensorboard = _load_guild_tensorboard_module()
    _filter_tensorboard_logging()
    with util.TempDir("guild-tensorboard-") as logdir:
        log.debug("Using logdir %s", logdir)
        monitor = RunsMonitor(logdir, args)
        monitor.start()
        tensorboard.main(
            logdir=logdir,
            host=(args.host or socket.gethostname()),
            port=(args.port or util.free_port()),
            reload_interval=args.refresh_interval,
            ready_cb=(_open_url if not args.no_open else None))
        log.debug("Stopping")
        monitor.stop()
        log.debug("Removing logdir %s", logdir) # Handled by ctx mgr
    if util.PLATFORM != "Windows":
        cli.out()

def _load_guild_tensorboard_module():
    try:
        from guild import tensorboard
    except ImportError as e:
        _handle_tensorboard_import_error(e)
    else:
        return tensorboard

def _handle_tensorboard_import_error(e):
    if str(e) in ("No module named tensorflow",
                  "No module named 'tensorflow'"):
        cli.out(
            "TensorBoard cannot not be started because TensorFlow "
            "is not installed.\n"
            "Refer to https://www.tensorflow.org/install/ for help "
            "installing TensorFlow on your system.", err=True)
    else:
        cli.out("TensorBoard could not be started: %s" % e, err=True)
    cli.error()

def _format_run_name(run):
    formatted = runs_impl.format_run(run)
    if util.PLATFORM == "Windows":
        fmt = "{short_id} {model} {op_name} {started}"
        formatted["started"] = formatted["started"].replace(":", "_")
    else:
        fmt = "{short_id} {model}:{op_name} {started}"
    return fmt.format(short_id=run.short_id, **formatted)

def _open_url(url):
    util.open_url(url)

def _filter_tensorboard_logging():
    import tensorflow as tf
    warn0 = tf.logging.warn
    tf.logging.warn = (
        lambda *args, **kw: _filter_warn(warn0, *args, **kw)
    )

def _filter_warn(warn0, msg, *args, **kw):
    skip = [
        "Found more than one graph event per run",
        "Found more than one metagraph event per run",
    ]
    for s in skip:
        if msg.startswith(s):
            return
    warn0(msg, *args, **kw)
