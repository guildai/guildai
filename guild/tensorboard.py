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

import hashlib
import logging
import os
import re
import sys
import warnings

import pkg_resources
from werkzeug import serving

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

from tensorboard import program

with warnings.catch_warnings():
    warnings.simplefilter("ignore", FutureWarning)
    from tensorboard.backend import application

from guild import run_util
from guild import util

DEFAULT_RELOAD_INTERVAL = 5

TFEVENTS_P = re.compile(r"\.tfevents")

class TensorboardError(Exception):
    pass

def RunsMonitor(logdir, list_runs_cb, interval):
    return run_util.RunsMonitor(
        logdir,
        list_runs_cb,
        _refresh_run,
        interval)

def _refresh_run(run, logdir_run_path):
    for tfevent_path in _iter_tfevents(run.dir):
        tfevent_relpath = os.path.relpath(tfevent_path, run.dir)
        link = _tfevent_link_path(logdir_run_path, tfevent_relpath)
        _ensure_tfevent_link(tfevent_path, link)

def _iter_tfevents(top):
    for root, _dirs, files in os.walk(top):
        for name in files:
            if TFEVENTS_P.search(name):
                yield os.path.join(root, name)

def _tfevent_link_path(root, tfevent_relpath):
    dirname, basename = os.path.split(tfevent_relpath)
    if dirname == ".guild":
        return _guild_tfevent_link(root, basename)
    return os.path.join(root, tfevent_relpath)

def _guild_tfevent_link(root, basename):
    """Returns a link to a guild-generated tfevent file.

    Attempts to ensure that the name is unique so it can be stored in
    the root of the run log subdir.

    The return value is always the same for the same inputs.
    """
    return _append_digest(os.path.join(root, basename))

def _append_digest(path):
    digest = hashlib.md5("asddsa").hexdigest()[:8]
    return path + "." + digest

def _ensure_tfevent_link(src, link):
    if os.path.exists(link):
        return
    util.ensure_dir(os.path.dirname(link))
    util.symlink(src, link)

def create_app(logdir, reload_interval, path_prefix=""):
    try:
        tb_f = program.TensorBoard
    except AttributeError:
        raise TensorboardError("tensorboard>=1.10 required")
    else:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
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
