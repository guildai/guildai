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

from werkzeug import serving

from guild import run_util
from guild import summary
from guild import util

log = logging.getLogger("guild")

DEFAULT_RELOAD_INTERVAL = 5

TFEVENTS_P = re.compile(r"\.tfevents")

IMG_EXT = (
    ".gif",
    ".jpeg",
    ".jpg",
    ".png",
    ".tif",
    ".tiff",
)

MAX_IMAGE_SUMMARIES = 100

class TensorboardError(Exception):
    pass

class _RunsMonitorOpts(object):

    def __init__(self, logspec):
        self.images = not logspec or "images" in logspec
        self.hparams = not logspec or "hparams" in logspec

def RunsMonitor(logdir, list_runs_cb, interval=None, logspec=None):
    return run_util.RunsMonitor(
        logdir,
        list_runs_cb,
        _refresh_run_cb(logspec),
        interval)

def _refresh_run_cb(logspec):
    opts = _RunsMonitorOpts(logspec)
    def f(run, logdir_run_path):
        return _refresh_run(run, logdir_run_path, opts)
    return f

def _refresh_run(run, logdir_run_path, opts):
    _refresh_tfevent_links(run, logdir_run_path)
    with summary.SummaryWriter(logdir_run_path) as writer:
        _refresh_summaries(run, logdir_run_path, writer, opts)

def _refresh_tfevent_links(run, logdir_run_path):
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
    digest = _tfevent_link_digest(root, tfevent_relpath)
    dirname, basename = os.path.split(tfevent_relpath)
    if dirname == ".guild":
        tfevent_relpath = basename
    return os.path.join(root, tfevent_relpath) + "." + digest

def _tfevent_link_digest(root, relpath):
    content = os.path.join(root, relpath).encode()
    return hashlib.md5(content).hexdigest()[:8]

def _ensure_tfevent_link(src, link):
    if os.path.exists(link):
        return
    util.ensure_dir(os.path.dirname(link))
    util.symlink(src, link)

def _refresh_summaries(run, logdir_run_path, writer, opts):
    if opts.hparams:
        _refresh_hparam_summaries(run, logdir_run_path, writer)
    if opts.images:
        _refresh_image_summaries(run, logdir_run_path, writer)

def _refresh_hparam_summaries(_run, _logdir_run_path, _writer):
    pass

def _metric_scalar_tags(run):
    from guild import index2
    return [
        tag for tag in [
            s["tag"] for s in index2.iter_run_scalars(run)
        ]
        if "/" not in tag
    ]

def _refresh_image_summaries(run, logdir_run_path, writer):
    n = 0
    for path, relpath in _iter_images(run.dir):
        if n >= MAX_IMAGE_SUMMARIES:
            break
        n += 1
        digest = _image_digest_path(logdir_run_path, relpath)
        if _image_added(digest):
            continue
        pending = _image_pending(digest)
        if run.status == "running" and _image_newer(path, pending):
            _set_image_pending(pending)
        else:
            _add_image_summary(writer, relpath, path)
            _set_image_added(pending)

def _iter_images(top):
    for root, _dir, names in os.walk(top):
        for name in names:
            _, ext = os.path.splitext(name)
            if ext.lower() in IMG_EXT:
                path = os.path.join(root, name)
                if not os.path.islink(path):
                    yield path, os.path.relpath(path, top)

def _image_digest_path(root, path):
    digest = hashlib.md5(path.encode()).hexdigest()
    return os.path.join(root, ".guild", "images", digest)

def _image_added(digest):
    return os.path.exists(digest)

def _image_pending(digest):
    return digest + ".pending"

def _image_newer(path, pending):
    if not os.path.exists(pending):
        return True
    return util.safe_mtime(path) > util.safe_mtime(pending)

def _set_image_pending(pending):
    util.ensure_dir(os.path.dirname(pending))
    util.touch(pending)

def _add_image_summary(writer, tag, path):
    writer.add_image(tag, path)

def _set_image_added(pending):
    assert pending.endswith(".pending"), pending
    added = pending[:-8]
    if os.path.exists(pending):
        os.rename(pending, added)
    else:
        util.ensure_dir(os.path.dirname(added))
        util.touch(added)

def create_app(logdir, reload_interval, path_prefix=""):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FutureWarning)
        from tensorboard.backend import application
        from tensorboard import program
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
    from tensorboard import version
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
