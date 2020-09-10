# Copyright 2017-2020 TensorHub, Inc.
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

import glob
import hashlib
import logging
import os
import re
import sys

from werkzeug import serving

from guild import flag_util
from guild import run_util
from guild import query
from guild import summary
from guild import tfevent
from guild import util

log = logging.getLogger("guild")

DEFAULT_RELOAD_INTERVAL = 5

TFEVENTS_P = re.compile(r"\.tfevents")
TFEVENT_TIMESTAMP_P = re.compile(r"tfevents\.([0-9]+)\.")

PROJECTOR_CONFIG_NAME = "projector_config.pbtxt"

IMG_EXT = (
    ".gif",
    ".jpeg",
    ".jpg",
    ".png",
    ".tif",
    ".tiff",
)

MAX_IMAGE_SUMMARIES = 100

SOURCECODE_HPARAM = "sourcecode"
TIME_METRIC = "time"


class TensorboardError(Exception):
    pass


class _RunsMonitorState(object):
    def __init__(self, logdir, log_images, log_hparams):
        self.logdir = logdir
        self.log_images = log_images
        self.log_hparams = log_hparams
        self.hparam_experiment = None
        self.last_runs_digest = None


def RunsMonitor(
    logdir,
    list_runs_cb,
    interval=None,
    log_images=True,
    log_hparams=True,
    run_name_cb=None,
):
    state = _RunsMonitorState(logdir, log_images, log_hparams)
    if state.log_hparams:
        list_runs_cb = _list_runs_f(list_runs_cb, state)
    return run_util.RunsMonitor(
        logdir,
        list_runs_cb,
        _refresh_run_cb(state),
        interval,
        _safe_run_name_cb(run_name_cb),
    )


def _safe_run_name_cb(base_cb):
    def f(run):
        name = (base_cb or run_util.default_run_name)(run)
        return _remove_invalid_dom_chars(name)

    return f


def _remove_invalid_dom_chars(s):
    """Replaces invalid DOM chars with ?.

    This is a conservative estimate of 'invalid' to avoid stripping
    out unicode chars on systems that support them. We know the
    ellipsis char causes problems and so the current implementation is
    limited to that single unicode char. We can expand this as needed.

    The upstream problem is with TensorBoard UI, which as of issue
    #230 does handle so-called invalid DOM chars gracefully.
    """
    invalid = {u"\u2026"}
    return "".join(x if x not in invalid else "?" for x in s)


def _list_runs_f(list_runs_cb, state):
    def f():
        runs = list_runs_cb()
        runs_digest = _runs_digest(runs)
        if runs and runs_digest != state.last_runs_digest:
            _ensure_hparam_experiment(runs, state)
        state.last_runs_digest = runs_digest
        return runs

    return f


def _runs_digest(runs):
    digest = hashlib.md5()
    for run_id in sorted([run.id for run in runs]):
        digest.update(run_id.encode())
    return digest.hexdigest()


def _ensure_hparam_experiment(runs, state):
    hparams = _experiment_hparams(runs)
    metrics = _experiment_metrics(runs)
    if not state.hparam_experiment:
        state.hparam_experiment = hparams, metrics
    else:
        _maybe_warn_hidden_hparam_data(hparams, metrics, state)


def _experiment_hparams(runs):
    hparams = {}
    for run in runs:
        for name, val in (run.get("flags") or {}).items():
            hparams.setdefault(name, set()).add(val)
        hparams.setdefault(SOURCECODE_HPARAM, set()).add(_run_sourcecode(run))
    return hparams


def _run_sourcecode(run):
    return run.get("sourcecode_digest", "")[:8]


def _experiment_metrics(runs):
    metrics = set([TIME_METRIC])
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
            metrics.update([col.key for col in select.cols if _is_last_scalar(col)])
    return metrics


def _is_last_scalar(select_col):
    return isinstance(select_col, query.Scalar) and select_col.qualifier in (
        None,
        "last",
    )


def _run_root_scalars(run):
    from guild.commands.runs_impl import filter_default_scalar

    return [tag for tag in _iter_scalar_tags(run.dir) if filter_default_scalar(tag)]


def _maybe_warn_hidden_hparam_data(hparams, metrics, state):
    assert state.hparam_experiment
    exp_hparams, exp_metrics = state.hparam_experiment
    _maybe_warn_new_hparams(hparams, exp_hparams)
    _maybe_warn_bad_domain_hparams(hparams, exp_hparams)
    _maybe_warn_new_metrics(metrics, exp_metrics)


def _maybe_warn_new_hparams(hparams, exp_hparams):
    added = set(hparams) - set(exp_hparams)
    if added:
        log.warning(
            "Runs found with new hyperparameters: %s. These hyperparameters will "
            "NOT appear in the HPARAMS plugin. Restart this command to view "
            "them.",
            ", ".join(sorted(added)),
        )


def _maybe_warn_bad_domain_hparams(hparams, exp_hparams):
    bad_domain_hparams = _bad_domain_hparams(hparams, exp_hparams)
    if bad_domain_hparams:
        flag_assigns = [
            flag_util.flag_assign(name, val) for name, val in bad_domain_hparams
        ]
        log.warning(
            "Runs found with hyperparameter values that cannot be displayed in the "
            "HPARAMS plugin: %s. Restart this command to view them.",
            ", ".join(sorted(flag_assigns)),
        )


def _bad_domain_hparams(hparams, exp_hparams):
    bad = []
    for name, vals in hparams.items():
        try:
            exp_vals = exp_hparams[name]
        except KeyError:
            continue
        else:
            bad.extend(_bad_domain_hparam_vals(name, vals, exp_vals))
    return bad


def _bad_domain_hparam_vals(name, vals, exp_vals):
    exp_type = summary.hparam_type(exp_vals)
    if exp_type == summary.HPARAM_TYPE_NONE:
        return []
    return [
        (name, bad_val)
        for bad_val in _incompatible_hparam_vals(vals, exp_type, exp_vals)
    ]


def _incompatible_hparam_vals(vals, exp_type, exp_vals):
    for val in vals:
        val_type = summary.hparam_type([val])
        if val_type != exp_type or (
            val_type == summary.HPARAM_TYPE_STRING and val not in exp_vals
        ):
            yield val


def _maybe_warn_new_metrics(metrics, exp_metrics):
    added = metrics - exp_metrics
    if added:
        log.warning(
            "Runs found with new metrics: %s. These runs will NOT appear in the "
            "HPARAMS plugin. Restart this command to view them.",
            ", ".join(sorted(added)),
        )


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
    _maybe_time_metric(run, run_logdir)
    _sync_run_file_links(run, run_logdir)


def _refresh_tfevent_links(run, run_logdir, state):
    for tfevent_path in _iter_tfevents(run.dir):
        tfevent_relpath = os.path.relpath(tfevent_path, run.dir)
        link = os.path.join(run_logdir, tfevent_relpath)
        if not os.path.exists(link):
            _init_tfevent_link(tfevent_path, link, run, state)


def _iter_tfevents(top):
    for root, _dirs, files in os.walk(top):
        for name in files:
            if TFEVENTS_P.search(name):
                yield os.path.join(root, name)


def _init_tfevent_link(tfevent_src, tfevent_link, run, state):
    link_dir = os.path.dirname(tfevent_link)
    util.ensure_dir(link_dir)
    if state.log_hparams:
        _init_hparam_session(run, link_dir, state)
    log.debug("Creating link from '%s' to '%s'", tfevent_src, tfevent_link)
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
    if log.getEffectiveLevel() <= logging.DEBUG:
        log.debug(
            "hparam experiment: hparams=%r metrics=%r", sorted(hparams), sorted(metrics)
        )
    writer.add_hparam_experiment(hparams, metrics)


def _add_hparam_session(run, writer):
    session_name = _hparam_session_name(run)
    hparams = run.get("flags") or {}
    hparams[SOURCECODE_HPARAM] = _run_sourcecode(run)
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
                try:
                    writer.add_image(relpath, path)
                except Exception as e:
                    if log.getEffectiveLevel() <= logging.DEBUG:
                        log.exception("adding image %s", path)
                    log.error("error adding image %s: %s", path, e)


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
        logdir, filename_base="%0.10d.image" % timestamp, filename_suffix="." + digest
    )


def _next_tfevent_timestamp(dir):
    assert os.path.exists(dir), dir
    cur = -1
    for name in os.listdir(dir):
        m = TFEVENT_TIMESTAMP_P.search(name)
        if m:
            cur = max(cur, int(m.group(1)))
    return cur + 1


def _maybe_time_metric(run, run_logdir):
    time = _run_time(run)
    if time is not None:
        # Write time metric alongside hparams logs
        for logdir in _iter_hparams_logdirs(run_logdir):
            _ensure_time_metric(logdir, time)


def _iter_hparams_logdirs(top):
    for path in _iter_tfevents(top):
        if path.endswith(".hparams"):
            yield os.path.dirname(path)


def _ensure_time_metric(logdir, time):
    if not _time_metric_exists(logdir):
        _init_time_metric(logdir, time)


def _metrics_logdir(run_logdir):
    return os.path.join(run_logdir, ".guild")


def _time_metric_exists(logdir):
    return bool(glob.glob(os.path.join(logdir, "*.time")))


def _init_time_metric(logdir, time):
    with _time_metric_writer(logdir) as writer:
        writer.add_scalar(TIME_METRIC, time)


def _time_metric_writer(logdir):
    return summary.SummaryWriter(logdir, filename_base="9999999999.time")


def _run_time(run):
    stopped = run.get("stopped")
    if stopped is None:
        return None
    started = run.get("started")
    if started is None:
        return None
    return (stopped - started) / 1000000


def _sync_run_file_links(run, run_logdir):
    _add_missing_run_file_links(run, run_logdir)
    _remove_orphaned_run_file_links(run_logdir)


def _add_missing_run_file_links(run, run_logdir):
    for src, link, link_dir in _iter_linkable_run_files(run, run_logdir):
        _ensure_run_file_link(src, link, link_dir)


def _iter_linkable_run_files(run, run_logdir):
    """Yields tuples of src, link, and link_dir for linkable run files.

    The odd interface is for efficiency to avoid re-processing paths
    needed for downstream links. In particular, link_dir is provided
    so downstream doesn't have to re-calculate it when ensuring the
    link parent dir.
    """
    top_level = True
    for root, dirs, files in os.walk(run.dir):
        _maybe_remove_guild_dir(top_level, dirs)
        top_level = False
        rel_root = os.path.relpath(root, run.dir)
        for name in files:
            src = os.path.join(root, name)
            link_dir = os.path.join(run_logdir, rel_root)
            link = os.path.join(link_dir, name)
            yield src, link, link_dir


def _maybe_remove_guild_dir(remove, dirs):
    if remove:
        try:
            dirs.remove(".guild")
        except ValueError:
            pass


def _ensure_run_file_link(src, link, link_dir):
    if not os.path.exists(link):
        log.debug("Creating link from '%s' to '%s'", src, link)
        util.ensure_dir(link_dir)
        util.symlink(src, link)


def _remove_orphaned_run_file_links(run_logdir):
    for root, _dirs, files in os.walk(run_logdir):
        for name in files:
            path = os.path.join(root, name)
            if os.path.islink(path) and not os.path.exists(path):
                log.debug("Deleting orphaned path '%s'" % path)
                try:
                    os.remove(path)
                except OSError as e:
                    log.warning("error deleting orphaned link '%s': %s", path, e)


def create_app(
    logdir,
    reload_interval=None,
    path_prefix="",
    tensorboard_options=None,
    disabled_plugins=None,
):
    from guild.plugins import tensorboard

    plugins = _tensorboard_plugins(disabled_plugins)
    log.debug("TensorBoard plugins: %s", plugins)
    return tensorboard.wsgi_app(
        logdir,
        plugins,
        reload_interval=reload_interval,
        path_prefix=path_prefix,
        tensorboard_options=tensorboard_options,
    )


def _tensorboard_plugins(disabled=None):
    from guild.plugins import tensorboard

    base_plugins = tensorboard.base_plugins()
    return _filter_disabled_plugins(disabled, base_plugins)


def _filter_disabled_plugins(disabled, plugins):
    if not disabled:
        return plugins
    log.debug("TensorBoard disableded plugins: %s", disabled)
    return [plugin for plugin in plugins if not _is_disableded_plugin(plugin, disabled)]


def _is_disableded_plugin(plugin, disabled):
    plugin_name = _plugin_name(plugin)
    plugin_name = str(plugin)
    return any((name in plugin_name for name in disabled))


def _plugin_name(plugin):
    # TB plugins can be classes or loader, or who knows what - this
    # method is a quick-and-dirty way to get a string/name to match
    # against.
    return str(plugin)


def setup_logging():
    _setup_tensorboard_logging()
    _setup_werkzeug_logging()


def _setup_tensorboard_logging():
    from guild.plugins import tensorboard

    tensorboard.silence_info_logging()


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
    from guild.plugins import tensorboard

    server, _ = make_simple_server(tb_app, host, port)
    url = util.local_server_url(host, port)
    sys.stderr.write(
        "Running TensorBoard %s at %s (Type Ctrl+C to quit)\n"
        % (tensorboard.version(), url)
    )
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


def serve_forever(
    logdir,
    host,
    port,
    reload_interval=DEFAULT_RELOAD_INTERVAL,
    tensorboard_options=None,
    ready_cb=None,
):
    app = create_app(logdir, reload_interval, tensorboard_options=tensorboard_options)
    setup_logging()
    run_simple_server(app, host, port, ready_cb)


def test_output(out):
    from guild.plugins import tensorboard

    plugins = _tensorboard_plugins()
    data = {
        "version": tensorboard.version(),
        "plugins": ["%s.%s" % (p.__module__, p.__name__) for p in plugins],
    }
    json.dump(data, out)


if __name__ == "__main__":
    import json

    test_output(sys.stdout)
