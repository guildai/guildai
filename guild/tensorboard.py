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
import sys

import pkg_resources
from werkzeug import serving

# Proactively check imports for tensorflow and tensorboard. Check
# tensorflow first because import problems with tensorboard are likely
# a result of TensorFlow not being installed.

# pylint: disable=unused-import,wrong-import-order

import tensorflow as tf
from tensorboard import version

log = logging.getLogger("guild")

# Check tensorboard version against our requirements. Indicate error
# as ImportError with the current version and unmet requirement as
# additional arguments.

_req = pkg_resources.Requirement.parse("tensorflow-tensorboard >= 1.5.0")

if version.VERSION not in _req:
    log.warning(
        "installed version of tensorboard (%s) does not meet the "
        "requirement %s", version.VERSION, _req)

# pylint: disable=wrong-import-position

from tensorboard import util as tf_util
from tensorboard.backend import application
from tensorboard.plugins.audio import audio_plugin
from tensorboard.plugins.core import core_plugin
from tensorboard.plugins.distribution import distributions_plugin
from tensorboard.plugins.graph import graphs_plugin
from tensorboard.plugins.histogram import histograms_plugin
from tensorboard.plugins.image import images_plugin
from tensorboard.plugins.profile import profile_plugin
from tensorboard.plugins.projector import projector_plugin
from tensorboard.plugins.scalar import scalars_plugin
from tensorboard.plugins.text import text_plugin

from guild import util

DEFAULT_RELOAD_INTERVAL = 5
MIN_MONITOR_INTERVAL = 5

class RunsMonitor(util.LoopingThread):

    STOP_TIMEOUT = 5

    def __init__(self, list_runs_cb, logdir, interval):
        """Create a RunsMonitor.

        Note that run links are created initially by this
        function. Any errors result from user input will propagate
        during this call. Similar errors occuring after the monitor is
        started will be logged but will not propagate.
        """
        interval = min(interval, MIN_MONITOR_INTERVAL)
        super(RunsMonitor, self).__init__(
            cb=self.run_once,
            interval=interval,
            stop_timeout=self.STOP_TIMEOUT)
        self.logdir = logdir
        self.list_runs_cb = list_runs_cb
        self.run_once(exit_on_error=True)

    def run_once(self, exit_on_error=False):
        log.debug("Refreshing runs")
        try:
            runs = self.list_runs_cb()
        except SystemExit as e:
            if exit_on_error:
                raise
            log.error(
                "An error occurred while reading runs. "
                "Use --debug for details.")
            log.debug(e)
        else:
            self._refresh_run_links(runs)

    def _refresh_run_links(self, runs):
        to_delete = os.listdir(self.logdir)
        for run in runs:
            link_name = self._format_run_name(run)
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

    @staticmethod
    def _format_run_name(run):
        model = run.opref.model_name
        op_name = run.opref.op_name
        started = util.format_timestamp(run.get("started"))
        if util.PLATFORM == "Windows":
            fmt = "{short_id} {model} {op_name} {started}"
            started = started.replace(":", "_")
        else:
            fmt = "{short_id} {model}:{op_name} {started}"
        return fmt.format(
            short_id=run.short_id,
            model=model,
            op_name=op_name,
            started=started)

def create_app(logdir, reload_interval, path_prefix=""):
    plugins = [
        core_plugin.CorePlugin,
        scalars_plugin.ScalarsPlugin,
        images_plugin.ImagesPlugin,
        audio_plugin.AudioPlugin,
        graphs_plugin.GraphsPlugin,
        distributions_plugin.DistributionsPlugin,
        histograms_plugin.HistogramsPlugin,
        projector_plugin.ProjectorPlugin,
        text_plugin.TextPlugin,
        profile_plugin.ProfilePlugin,
    ]
    return application.standard_tensorboard_wsgi(
        logdir=os.path.expanduser(logdir),
        purge_orphaned_data=False,
        reload_interval=reload_interval,
        plugins=plugins,
        db_uri="",
        assets_zip_provider=None,
        path_prefix=path_prefix,
        window_title="")

def setup_logging():
    tf_util.setup_logging()
    _filter_logging()

def _filter_logging():
    warn0 = tf.logging.warn
    tf.logging.warn = (
        lambda *args, **kw: _filter_warn(warn0, *args, **kw)
    )
    tf.logging.warning = tf.logging.warn

def _filter_warn(warn0, msg, *args, **kw):
    skip = [
        "Found more than one graph event per run",
        "Found more than one metagraph event per run",
        "Deleting accumulator",
    ]
    for s in skip:
        if msg.startswith(s):
            return
    warn0(msg, *args, **kw)

def run_simple_server(tb_app, host, port, ready_cb):
    server, url = make_simple_server(tb_app, host, port)
    sys.stderr.write(
        "TensorBoard %s at %s (Press CTRL+C to quit)\n"
        % (version.VERSION, url))
    sys.stderr.flush()
    if ready_cb:
        ready_cb(url)
    server.serve_forever()

def make_simple_server(app, host, port):
    server = serving.make_server(host, port, app, threaded=True)
    server.daemon_threads = True
    server.handle_error = _handle_error
    tensorboard_url = "http://%s:%s" % (host, port)
    return server, tensorboard_url

def _handle_error(request, _client_address):
    log.exception("HTTP serving error: %s", request)

def main(logdir, host, port,
         reload_interval=DEFAULT_RELOAD_INTERVAL,
         ready_cb=None):
    app = create_app(logdir, reload_interval)
    setup_logging()
    run_simple_server(app, host, port, ready_cb)
