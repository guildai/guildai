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

import errno
import functools
import logging
import os
import shutil
import tempfile

from guild import config
from guild import run as runlib
from guild import util

log = logging.getLogger("guild")


def path(*names):
    names = [name for name in names if name]
    return os.path.join(config.guild_home(), *names)


def runs_dir(deleted=False):
    if deleted:
        return trash_dir("runs")
    else:
        return path("runs")


def trash_dir(name=None):
    return path("trash", name)


def cache_dir(name=None):
    return path("cache", name)


def pidfile(name):
    return path("proc", name)


def logfile(name):
    return path("log", name)


def remote_dir(name=None):
    # Use directory containing user config to store remote info.
    rest_path = [name] if name else []
    config_path = config.user_config_path()
    if config_path:
        return os.path.join(os.path.dirname(config_path), "remotes", *rest_path)
    return path("remotes", name)


def runs(root=None, sort=None, filter=None, force_root=False):
    filter = filter or (lambda _: True)
    all_runs = _all_runs_f(root, force_root)
    runs = [run for run in all_runs() if filter(run)]
    if sort:
        runs = sorted(runs, key=_run_sort_key(sort))
    return runs


def _all_runs_f(root, force_root):
    root = root or runs_dir()
    if force_root:
        return _default_all_runs_f(root)

    return util.find_apply(
        [
            _zipfile_all_runs_f,
            _runs_under_parent_f,
            _default_all_runs_f,
        ],
        root,
    )


def _default_all_runs_f(root):
    return lambda: _all_runs(root)


def _zipfile_all_runs_f(root):
    if root and root.lower().endswith(".zip"):
        from . import run_zip_proxy

        def f():
            try:
                return run_zip_proxy.all_runs(root)
            except Exception as e:
                if log.getEffectiveLevel() <= logging.DEBUG:
                    log.exception("getting runs for zip file %s", root)
                log.error("cannot read from %s: %s", root, e)
                return []

        return f


def _runs_under_parent_f(root):
    runs_parent = os.getenv("GUILD_RUNS_PARENT")
    if not runs_parent:
        return None
    log.debug("limitting to runs under parent %s", runs_parent)
    return lambda: _runs_for_parent(runs_parent, root)


def _runs_for_parent(parent, root):
    parent_path = os.path.join(root, parent)
    try:
        names = os.listdir(parent_path)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise
        return []
    else:
        return _runs_for_parent_links(parent_path, names, root)


def _runs_for_parent_links(parent_path, names, runs_dir):
    real_paths = [util.realpath(os.path.join(parent_path, name)) for name in names]
    return [
        runlib.for_dir(path)
        for path in real_paths
        if _is_parent_run_path(path, runs_dir)
    ]


def _is_parent_run_path(path, runs_dir):
    return util.compare_paths(os.path.dirname(path), runs_dir)


def run_filter(name, *args):
    # Disabling undefined-variable check to work around
    # https://github.com/PyCQA/pylint/issues/760
    # pylint: disable=undefined-variable
    if name.startswith("!"):
        name = name[1:]
        maybe_negate = lambda f: lambda r: not f(r)
    else:
        maybe_negate = lambda f: lambda r: f(r)
    if name == "true":
        filter = lambda _: True
    elif name == "attr":
        name, expected = args
        filter = lambda r: _run_attr(r, name) == expected
    elif name == "all":
        (filters,) = args
        filter = lambda r: all((f(r) for f in filters))
    elif name == "any":
        (filters,) = args
        filter = lambda r: any((f(r) for f in filters))
    else:
        raise ValueError(name)
    return maybe_negate(filter)


def _all_runs(root):
    return [runlib.Run(name, path) for name, path in _iter_dirs(root)]


def iter_run_dirs(root=None):
    return _iter_dirs(root or runs_dir())


def _iter_dirs(root):
    try:
        names = os.listdir(root)
    except OSError:
        names = []
    for name in names:
        path = os.path.join(root, name)
        if _opref_exists(path):
            yield name, path


def _opref_exists(run_dir):
    opref_path = os.path.join(run_dir, ".guild", "opref")
    return os.path.exists(opref_path)


def _run_sort_key(sort):
    return functools.cmp_to_key(lambda x, y: _run_cmp(x, y, sort))


def _run_cmp(x, y, sort):
    for attr in sort:
        attr_cmp = _run_attr_cmp(x, y, attr)
        if attr_cmp != 0:
            return attr_cmp
    return 0


def _run_attr_cmp(x, y, attr):
    if attr.startswith("-"):
        attr = attr[1:]
        rev = -1
    else:
        rev = 1
    x_val = _run_attr(x, attr)
    if x_val is None:
        return -rev
    y_val = _run_attr(y, attr)
    if y_val is None:
        return rev
    return rev * ((x_val > y_val) - (x_val < y_val))


def _run_attr(run, name):
    if name in runlib.Run.__properties__:
        return getattr(run, name)
    else:
        return run.get(name)


def delete_runs(runs, permanent=False):
    for run in runs:
        src = os.path.join(runs_dir(), run.id)
        if permanent:
            _delete_run(src)
        else:
            dest = os.path.join(runs_dir(deleted=True), run.id)
            _move(src, dest)


def purge_runs(runs):
    for run in runs:
        src = os.path.join(runs_dir(deleted=True), run.id)
        _delete_run(src)


def _delete_run(src):
    assert src and src != os.path.sep, src
    assert src.startswith(runs_dir()) or src.startswith(runs_dir(deleted=True)), src
    log.debug("deleting %s", src)
    shutil.rmtree(src)


def _move(src, dest):
    util.ensure_dir(os.path.dirname(dest))
    log.debug("moving %s to %s", src, dest)
    if os.path.exists(dest):
        _move_to_backup(dest)
    shutil.move(src, dest)


def _move_to_backup(path):
    dir = os.path.dirname(path)
    prefix = "%s_" % os.path.basename(path)
    backup = tempfile.NamedTemporaryFile(prefix=prefix, dir=dir, delete=True)
    log.warning("%s exists, moving to %s", path, backup.name)
    backup.close()
    shutil.move(path, backup.name)


def restore_runs(runs):
    for run in runs:
        src = os.path.join(runs_dir(deleted=True), run.id)
        dest = os.path.join(runs_dir(), run.id)
        _move(src, dest)


def find_runs(run_id_prefix, root=None):
    root = root or runs_dir()
    return (
        (name, path)
        for name, path in _iter_dirs(root)
        if name.startswith(run_id_prefix)
    )


def get_run(run_id, root=None):
    root = root or runs_dir()
    path = os.path.join(root, run_id)
    if os.path.exists(path):
        return runlib.Run(run_id, path)
    raise LookupError(run_id)
