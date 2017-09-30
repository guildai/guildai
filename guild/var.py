import os

import guild.run

def path(subpath):
    return os.path.join(_root(), subpath)

def _root():
    return os.path.expanduser(os.path.join("~", ".guild"))

def runs_dir():
    return path("runs")

def runs(root=None, sort=None, filter=None):
    root = root or runs_dir()
    filter_run = _run_filter(filter)
    runs = [run for run in _all_runs(root) if filter_run(run)]
    if sort:
        runs.sort(_runs_cmp(sort))
    return runs

def _run_filter(f):
    if f is None:
        return _run_filter_true()
    if isinstance(f, list):
        return _run_filter_all(f)
    elif isinstance(f, tuple):
        if len(f) == 2:
            return _run_filter_equals(f)
        elif len(f) == 3:
            return _run_filter_cond(f)
    raise ValueError(f)

def _run_filter_all(l):
    return lambda x: all([_run_filter(f)(x) for f in l])

def _run_filter_equals(f):
    attr, val = f
    return lambda x: _run_attr(x, attr) == val

def _run_filter_cond(f):
    attr, cond, val = f
    if cond == "=":
        return lambda x: _run_attr(x, attr) == val
    elif cond == "!=":
        return lambda x: _run_attr(x, attr) != val
    else:
        raise ValueError(f)

def _run_filter_true():
    return lambda _: True

def _all_runs(root):
    return [
        guild.run.Run(name, path)
        for name, path in _iter_dirs(root)
    ]

def _iter_dirs(root):
    for name in os.listdir(root):
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
