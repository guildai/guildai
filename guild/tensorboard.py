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
from guild import query
from guild import summary
from guild import tfevent
from guild import util

log = logging.getLogger("guild")

DEFAULT_RELOAD_INTERVAL = 5

TFEVENTS_P = re.compile(r"\.tfevents")
TFEVENT_TIMESTAMP_P = re.compile(r"tfevents\.([0-9]+)\.")

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

class _RunsMonitorState(object):

    def __init__(self, logdir, logspec):
        self.logdir = logdir
        self.log_images = not logspec or "images" in logspec
        self.log_hparams = not logspec or "hparams" in logspec
        self.hparam_experiment = None
        self.hparam_experiment_runs_digest = None

def RunsMonitor(logdir, list_runs_cb, interval=None, logspec=None):
    state = _RunsMonitorState(logdir, logspec)
    if state.log_hparams:
        list_runs_cb = _hparam_init_support(list_runs_cb, state)
    return run_util.RunsMonitor(
        logdir,
        list_runs_cb,
        _refresh_run_cb(state),
        interval)

def _hparam_init_support(list_runs_cb, state):
    def f():
        runs = list_runs_cb()
        _refresh_hparam_experiment(runs, state)
        return runs
    return f

def _refresh_hparam_experiment(runs, state):
    if runs:
        runs_digest = _runs_digest(runs)
        if runs_digest == state.hparam_experiment_runs_digest:
            return
        hparams = _experiment_hparams(runs)
        metrics = _experiment_metrics(runs)
        state.hparam_experiment = hparams, metrics
        state.hparam_experiment_runs_digest = runs_digest
    else:
        state.hparam_experiment = None
        state.hparam_experiment_runs_digest = None

def _runs_digest(runs):
    digest = hashlib.md5()
    for run_id in sorted([run.id for run in runs]):
        digest.update(run_id.encode())
    return digest.hexdigest()

def _experiment_hparams(runs):
    hparams = {}
    for run in runs:
        for name, val in (run.get("flags") or {}).items():
            hparams.setdefault(name, set()).add(val)
    return hparams

def _experiment_metrics(runs):
    metrics = set()
    for run in runs:
        metrics.update(_run_metric_tags(run))
    return metrics

def _run_metric_tags(run):
    return _run_compare_metrics(run) or _run_root_scalars(run)

def _run_compare_metrics(run):
    compare_specs = run_util.latest_compare(run)
    if not compare_specs:
        return None
    metrics = set()
    for spec in compare_specs:
        try:
            select = query.parse_colspec(spec)
        except query.ParseError:
            pass
        else:
            metrics.update([
                col.key for col in select.cols
                if _is_last_scalar(col)])
    return metrics

def _is_last_scalar(select_col):
    return (
        isinstance(select_col, query.Scalar) and
        select_col.qualifier in (None, "last"))

def _run_root_scalars(run):
    return [tag for tag in _iter_scalar_tags(run.dir) if "/" not in tag]

def _iter_scalar_tags(dir):
    for _path, _digest, scalars in tfevent.scalar_readers(dir):
        for s in scalars:
            yield s[0]

def _refresh_run_cb(state):
    def f(run, run_logdir):
        return _refresh_run(run, run_logdir, state)
    return f

def _refresh_run(run, run_logdir, state):
    _refresh_tfevent_links(run, run_logdir, state)
    _refresh_image_summaries(run, run_logdir, state)

def _refresh_tfevent_links(run, run_logdir, state):
    for tfevent_path in _iter_tfevents(run.dir):
        tfevent_relpath = os.path.relpath(tfevent_path, run.dir)
        link = _tfevent_link_path(run_logdir, tfevent_relpath)
        if not os.path.exists(link):
            _init_tfevent_link(tfevent_path, link, run, state)

def _iter_tfevents(top):
    for root, _dirs, files in os.walk(top):
        for name in files:
            if TFEVENTS_P.search(name):
                yield os.path.join(root, name)

def _tfevent_link_path(root, tfevent_relpath):
    return os.path.join(root, tfevent_relpath)

def _init_tfevent_link(tfevent_src, tfevent_link, run, state):
    link_dir = os.path.dirname(tfevent_link)
    util.ensure_dir(link_dir)
    if state.log_hparams:
        _init_hparam_session(run, link_dir, state)
    util.symlink(tfevent_src, tfevent_link)

def _init_hparam_session(run, run_logdir, state):
    with _hparams_writer(run_logdir) as writer:
        if state.hparam_experiment:
            _add_hparam_experiment(state.hparam_experiment, writer)
        _add_hparam_session(run, writer)

def _hparams_writer(logdir):
    return summary.SummaryWriter(logdir, filename_base="0000000000.hparams")

def _add_hparam_experiment(hparam_experiment, writer):
    hparams, metrics = hparam_experiment
    writer.add_hparam_experiment(hparams, metrics)

def _add_hparam_session(run, writer):
    session_name = _hparam_session_name(run)
    hparams = run.get("flags") or {}
    writer.add_hparam_session(session_name, hparams, run.status)

def _hparam_session_name(run):
    operation = run_util.format_operation(run)
    return "%s %s" % (run.short_id, operation)

def _refresh_image_summaries(run, run_logdir, state):
    if not state.log_images:
        return
    images_logdir = os.path.join(run_logdir, ".images")
    for path, relpath in _iter_images(run.dir):
        if _count_images(images_logdir) >= MAX_IMAGE_SUMMARIES:
            break
        img_path_digest = _path_digest(relpath)
        tfevent_path = _image_tfevent_path(images_logdir, img_path_digest)
        if _image_updated_since_summary(path, tfevent_path):
            util.ensure_dir(images_logdir)
            with _image_writer(images_logdir, img_path_digest) as writer:
                writer.add_image(relpath, path)

def _iter_images(top):
    for root, _dir, names in os.walk(top):
        for name in sorted(names):
            _, ext = os.path.splitext(name)
            if ext.lower() not in IMG_EXT:
                continue
            path = os.path.join(root, name)
            if not os.path.islink(path):
                yield path, os.path.relpath(path, top)

def _count_images(dir):
    return len(_unique_digests(dir))

def _unique_digests(dir):
    if not os.path.exists(dir):
        return []
    return set([os.path.splitext(name)[1] for name in os.listdir(dir)])

def _path_digest(path):
    return hashlib.md5(path.encode()).hexdigest()

def _image_tfevent_path(logdir, digest):
    if not os.path.exists(logdir):
        return None
    latest = None
    for name in os.listdir(logdir):
        if name.endswith(digest):
            latest = max(name, latest) if latest else name
    if not latest:
        return None
    return os.path.join(logdir, latest)

def _image_updated_since_summary(img_path, tfevent_path):
    if not tfevent_path:
        return True
    return util.safe_mtime(img_path) > util.safe_mtime(tfevent_path)

def _image_writer(logdir, digest):
    timestamp = _next_tfevent_timestamp(logdir)
    return summary.SummaryWriter(
        logdir,
        filename_base="%0.10d.image" % timestamp,
        filename_suffix="." + digest)

def _next_tfevent_timestamp(dir):
    assert os.path.exists(dir), dir
    cur = -1
    for name in os.listdir(dir):
        m = TFEVENT_TIMESTAMP_P.search(name)
        if m:
            cur = max(cur, int(m.group(1)))
    return cur + 1

def create_app(logdir, reload_interval, path_prefix=""):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", Warning)
        from tensorboard.backend import application
        from tensorboard import program
    try:
        tb_f = program.TensorBoard
    except AttributeError:
        raise TensorboardError("tensorboard>=1.10 required")
    else:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", Warning)
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
