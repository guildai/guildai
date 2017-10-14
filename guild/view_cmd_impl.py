# Copyright 2017 TensorHub, Inc.
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

import logging
import os
import shutil
import tempfile
import threading
import time

import guild.cli
import guild.runs_cmd_impl
import guild.tensorboard
import guild.util

MIN_MONITOR_INTERVAL = 5

class RunsMonitor(threading.Thread):

    STOP_TIMEOUT = 5

    def __init__(self, logdir, args, cmd_ctx):
        """Create a RunsMonitor.

        Note that run links are created initially by this
        function. Any errors result from user input will propagate
        during this call. Similar errors occuring after the monitor is
        started will be logged but will not propagate.
        """
        super(RunsMonitor, self).__init__()
        self.logdir = logdir
        self.args = args
        self.cmd_ctx = cmd_ctx
        self.run_once(exit_on_error=True)
        self._stop = threading.Event()
        self._stopped = threading.Event()

    def run(self):
        guild.util.loop(
            cb=self.run_once,
            wait=self._stop.wait,
            interval=min(self.args.refresh_interval,
                         MIN_MONITOR_INTERVAL),
            first_interval=self.args.refresh_interval)
        self._stopped.set()

    def stop(self):
        self._stop.set()
        self._stopped.wait(self.STOP_TIMEOUT)

    def run_once(self, exit_on_error=False):
        logging.debug("Refreshing runs")
        try:
            runs = guild.runs_cmd_impl.runs_for_args(self.args, self.cmd_ctx)
        except SystemExit as e:
            if exit_on_error:
                raise
            logging.error(
                "An error occurred while reading runs. "
                "Use --debug for details.")
            logging.debug(e)
        else:
            self._refresh_run_links(runs)

    def _refresh_run_links(self, runs):
        to_delete = os.listdir(self.logdir)
        for run in runs:
            link_name = _format_run_name(run)
            link_path = os.path.join(self.logdir, link_name)
            if not os.path.exists(link_path):
                logging.debug("Linking %s to %s", link_name, run.path)
                os.symlink(run.path, link_path)
            try:
                to_delete.remove(link_name)
            except ValueError:
                pass
        for link_name in to_delete:
            logging.debug("Removing %s" % link_name)
            os.remove(os.path.join(self.logdir, link_name))

def main(args, ctx):
    logdir = tempfile.mkdtemp(prefix="guild-view-logdir-")
    logging.debug("Using logdir %s", logdir)
    monitor = RunsMonitor(logdir, args, ctx)
    monitor.start()
    guild.tensorboard.main(
        logdir=logdir,
        host=(args.host or ""),
        port=(args.port or guild.util.free_port()),
        reload_interval=args.refresh_interval,
        ready_cb=(_open_url if not args.no_open else None))
    logging.debug("Stopping")
    monitor.stop()
    _cleanup(logdir)
    guild.cli.out()

def _format_run_name(run):
    op = run.get("op", "")
    started = run.get("started", "")
    formatted_started = time.strftime(
        "%Y-%m-%d %H:%M:%S",
        time.localtime(float(started)))
    return "[%s] %s %s" % (run.short_id, op, formatted_started)

def _open_url(url):
    guild.util.open_url(url)

def _cleanup(logdir):
    assert os.path.dirname(logdir) == tempfile.gettempdir()
    logging.debug("Deleting logdir %s", logdir)
    shutil.rmtree(logdir)
