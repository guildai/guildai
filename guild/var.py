import os
import shutil

import guild.run
import guild.util

def path(subpath):
    return os.path.join(_root(), subpath)

def _root():
    return os.path.expanduser(os.path.join("~", ".guild"))

def runs_dir(deleted=False):
    if deleted:
        return trash_dir("runs")
    else:
        return path("runs")

def trash_dir(name=None):
    return os.path.join(path("trash"), name) if name else path("trash")

def runs(root=None, sort=None, filter=None):
    root = root or runs_dir()
    filter = filter or (lambda _: True)
    runs = [run for run in _all_runs(root) if filter(run)]
    if sort:
        runs.sort(_runs_cmp(sort))
    return runs

def run_filter(name, *args):
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
        filters, = args
        filter = lambda r: all((f(r) for f in filters))
    elif name == "any":
        filters, = args
        filter = lambda r: any((f(r) for f in filters))
    else:
        raise ValueError(name)
    return maybe_negate(filter)

def _all_runs(root):
    return [
        guild.run.Run(name, path)
        for name, path in _iter_dirs(root)
    ]

def _iter_dirs(root):
    try:
        names = os.listdir(root)
    except OSError:
        names = []
    for name in names:
        path = os.path.join(root, name)
        if os.path.isdir(path):
            yield name, path

def _runs_cmp(sort):
    return lambda x, y: _run_cmp(x, y, sort)

def _run_cmp(x, y, sort):
    for attr in sort:
        attr_cmp = _run_attr_cmp(x, y, attr)
        if attr_cmp != 0:
            return attr_cmp
    return 0

def _run_attr_cmp(x, y, attr):
    if attr.startswith("-"):
        attr = attr[1:]
        return -cmp(_run_attr(x, attr), _run_attr(y, attr))
    else:
        return cmp(_run_attr(x, attr), _run_attr(y, attr))

def _run_attr(run, name):
    if name in guild.run.Run.__properties__:
        return getattr(run, name)
    else:
        return run.get(name)

def delete_runs(runs):
    for run in runs:
        src = os.path.join(runs_dir(), run.id)
        dest = os.path.join(runs_dir(deleted=True), run.id)
        _move_file(src, dest)

def _move_file(src, dest):
    guild.util.ensure_dir(os.path.dirname(dest))
    shutil.move(src, dest)

def restore_runs(runs):
    for run in runs:
        src = os.path.join(runs_dir(deleted=True), run.id)
        dest = os.path.join(runs_dir(), run.id)
        _move_file(src, dest)
