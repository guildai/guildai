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

_req = pkg_resources.Requirement.parse("tensorflow-tensorboard >= 1.10.0")

if version.VERSION not in _req:
    log.warning(
        "installed version of tensorboard (%s) does not meet the "
        "requirement %s", version.VERSION, _req)

# pylint: disable=wrong-import-position

from tensorboard import util as tb_util
from tensorboard import program
from tensorboard.backend import application

from guild import util

DEFAULT_RELOAD_INTERVAL = 5

class TensorboardError(Exception):
    pass

def create_app(logdir, reload_interval, path_prefix=""):
    try:
        tb_f = program.TensorBoard
    except AttributeError:
        raise TensorboardError("tensorboard>=1.10 required")
    else:
        tb = tb_f()
        argv = (
            "",
            "--logdir", logdir,
            "--reload_interval", str(reload_interval),
            "--path_prefix", path_prefix,
        )
        tb.configure(argv)
        return application.standard_tensorboard_wsgi(
            tb.flags,
            tb.plugin_loaders,
            tb.assets_zip_provider)

def setup_logging():
    tb_util.setup_logging()
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
    server, _ = make_simple_server(tb_app, host, port)
    url = util.local_server_url(host, port)
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

def serve_forever(logdir, host, port,
         reload_interval=DEFAULT_RELOAD_INTERVAL,
         ready_cb=None):
    app = create_app(logdir, reload_interval)
    setup_logging()
    run_simple_server(app, host, port, ready_cb)
