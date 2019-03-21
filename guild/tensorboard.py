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

import logging
import os
import re
import sys
import warnings

import pkg_resources
from werkzeug import serving

# Proactively check imports for tensorflow and tensorboard. Check
# tensorflow first because import problems with tensorboard are likely
# a result of TensorFlow not being installed.

# pylint: disable=unused-import,wrong-import-order

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    import tensorflow as tf

from tensorboard import version
from tensorboard import util as tb_util

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

from tensorboard import program
from tensorboard.backend import application

from guild import util

DEFAULT_RELOAD_INTERVAL = 5

class TensorboardError(Exception):
    pass

class RunsMonitor(util.RunsMonitor):

    tfevent_pattern = re.compile(r"\.tfevents")

    def _refresh_run_link(self, link, run_dir):
        to_delete = [
            os.path.relpath(p, link)
            for p in self._iter_tfevent_paths(link)]
        for tfevent_path in self._iter_tfevent_paths(run_dir):
            tfevent_relpath = os.path.relpath(tfevent_path, run_dir)
            util.remove(tfevent_relpath, to_delete)
            tfevent_link = os.path.join(link, tfevent_relpath)
            if not os.path.exists(tfevent_link):
                log.debug("Creating link %s", tfevent_link)
                util.ensure_dir(os.path.dirname(tfevent_link))
                util.symlink(tfevent_path, tfevent_link)
        for path in to_delete:
            tfevent_link = os.path.join(link, path)
            log.debug("Removing %s", tfevent_link)
            os.remove(tfevent_link)

    def _iter_tfevent_paths(self, run_dir):
        for root, _dirs, files in os.walk(run_dir):
            for name in files:
                if self.tfevent_pattern.search(name):
                    yield os.path.join(root, name)

    @staticmethod
    def _remove_run_link(link):
        os.remove(link)

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
    if hasattr(tb_util, "setup_logging"):
        _setup_logging_legacy()
    else:
        _setup_logging()

def _setup_logging_legacy():
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

def _setup_logging():
    _setup_tensorboard_logging()
    _setup_werkzeug_logging()

def _setup_tensorboard_logging():
    from tensorboard.util import tb_logging
    tb_logging.get_logger().info = lambda *_args, **_kw: None

def _setup_werkzeug_logging():
    from werkzeug._internal import _log as log0
    serving._log = _silent_logger(log0)

def _silent_logger(log0):
    def f(type, msg, *args):
        if type == "info":
            return
        log0(type, msg, *args)
    return f

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
