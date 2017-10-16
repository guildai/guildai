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

from __future__ import absolute_import
from __future__ import division

import logging
import os
import socket
import sys

import pkg_resources
from werkzeug import serving

# Proactively check imports for tensorflow and tensorboard. Check
# tensorflow first because import problems with tensorboard are likely
# a result of TensorFlow not being installed.

# pylint: disable=unused-import,wrong-import-order

import tensorflow as _dummy
from tensorboard import version

# Check tensorboard version against our requirements. Indicate error
# as ImportError with the current version and unmet requirement as
# additional arguments.

_req = pkg_resources.Requirement("tensorflow-tensorboard >= 0.1.5, < 0.5.0")
if version.VERSION not in _req:
    logging.warning(
        "installed version of tensorboard (%s) does not meet the "
        "requirement %s", version.VERSION, _req)

# pylint: disable=wrong-import-position

from tensorboard import util
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

DEFAULT_RELOAD_INTERVAL = 5

def create_app(plugins, logdir, reload_interval):
    return application.standard_tensorboard_wsgi(
        assets_zip_provider=None,
        db_uri="",
        logdir=os.path.expanduser(logdir),
        purge_orphaned_data=False,
        reload_interval=reload_interval,
        plugins=plugins)

def make_simple_server(app, host, port):
    server = serving.make_server(host, port, app, threaded=True)
    final_host = socket.gethostname()
    server.daemon_threads = True
    server.handle_error = _handle_error
    final_port = server.socket.getsockname()[1]
    tensorboard_url = "http://%s:%d" % (final_host, final_port)
    return server, tensorboard_url

def run_simple_server(tb_app, host, port, ready_cb):
    server, url = make_simple_server(tb_app, host, port)
    sys.stderr.write(
        "TensorBoard %s at %s (Press CTRL+C to quit)\n"
        % (version.VERSION, url))
    sys.stderr.flush()
    if ready_cb:
        ready_cb(url)
    server.serve_forever()

def _handle_error(request, _client_address):
    logging.exception("HTTP serving error: %s", request)

def main(logdir, host, port,
         reload_interval=DEFAULT_RELOAD_INTERVAL,
         ready_cb=None):
    util.setup_logging()
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
    app = create_app(plugins, logdir, reload_interval)
    run_simple_server(app, host, port, ready_cb)
