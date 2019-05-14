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
from __future__ import print_function

import datetime
import os
import sys
import threading
import warnings

import pandas as pd

from guild import opref as opreflib
from guild import run as runlib
from guild import run_util
from guild import var

RUN_DETAIL = [
    "id",
    "operation",
    "status",
    "started",
    "stopped",
    "label",
    "run_dir",
]

class RunError(Exception):

    def __init__(self, run, e):
        super(RunError, self).__init__(run, e)
        self.run = run
        self.e = e

class OutputTee(object):

    def __init__(self, out1, out2, lock):
        self._out1 = out1
        self._out2 = out2
        self._lock = lock

    def write(self, b):
        with self._lock:
            self._out1.write(b)
            self._out2.write(b)

class RunOutput(object):

    def __init__(self, run):
        self.run = run
        self._f = None
        self._f_lock = None
        self._stdout = None
        self._stderr = None

    def __enter__(self):
        self._f = open(self.run.guild_path("output"), "wb")
        self._f_lock = threading.Lock()
        self._stdout = sys.stdout
        sys.stdout = OutputTee(sys.stdout, self._f, self._f_lock)
        self._stderr = sys.stderr
        sys.stderr = OutputTee(sys.stderr, self._f, self._f_lock)

    def __exit__(self, *exc):
        with self._f_lock:
            self._f.close()
        sys.stdout = self._stdout
        sys.stderr = self._stderr

def run(op, *args, **kw):
    _opts = _pop_opts(kw)
    run = _init_run()
    _init_run_attrs(run, op, kw)
    try:
        with RunOutput(run):
            result = op(*args, **kw)
    except Exception as e:
        exit_status = 1
        raise RunError(run, e)
    else:
        exit_status = 0
        return run, result
    finally:
        _finalize_run_attrs(run, exit_status)

def _pop_opts(kw):
    opts = {}
    for name in list(kw):
        if name[:1] == "_":
            opts[name[1:]] = kw.pop(name)
    return opts

def _init_run():
    run_id = runlib.mkid()
    run_dir = os.path.join(var.runs_dir(), run_id)
    run = runlib.Run(run_id, run_dir)
    run.init_skel()
    return run

def _init_run_attrs(run, op, kw):
    opref = opreflib.OpRef("func", "", "", "", op.__name__)
    run.write_opref(opref)
    run.write_attr("started", runlib.timestamp())
    run.write_attr("flags", kw)

def _finalize_run_attrs(run, exit_status):
    run.write_attr("exit_status", exit_status)
    run.write_attr("stopped", runlib.timestamp())

def runs():
    runs = var.runs(sort=["-timestamp"])
    data, cols = _format_runs(runs)
    return pd.DataFrame(data=data, columns=cols)

def _format_runs(runs):
    cols = (
        "run",
        "operation",
        "started",
        "status",
    )
    data = [_format_run(run, cols) for run in runs]
    return data, cols

def _format_run(run, cols):
    fmt = run_util.format_run(run)
    return [
        _run_attr(run, name, fmt) for name in cols
    ]

class RunIndex(object):

    def __init__(self, run, fmt):
        self.run = run
        self.fmt = fmt

    def __str__(self):
        return self.run.short_id

def _run_attr(run, name, fmt):
    if name == "run":
        return RunIndex(run, fmt)
    elif name in ("operation",):
        return fmt[name]
    elif name in ("started",):
        return _datetime(run.get(name))
    else:
        return getattr(run, name)

def _datetime(ts):
    if ts is None:
        return None
    return datetime.datetime.fromtimestamp(int(ts / 1000000))

@pd.api.extensions.register_dataframe_accessor("delete")
class RunsDelete(object):

    def __init__(self, df):
        self.df = df

    def __call__(self, permanent=False):
        runs = [row[1][0].run for row in self.df.iterrows()]
        var.delete_runs(runs, permanent)
        return [run.id for run in runs]

@pd.api.extensions.register_series_accessor("delete")
class RunDelete(object):

    def __init__(self, s):
        self.s = s

    def __call__(self, permanent=False):
        runs = [self.s[0].run]
        var.delete_runs(runs, permanent)
        return [run.id for run in runs]

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    @pd.api.extensions.register_dataframe_accessor("info")
    class RunsInfo(object):

        def __init__(self, df):
            self.df = df

        def __call__(self, **kw):
            try:
                row = next(self.df.iterrows())
            except StopIteration:
                pass
            else:
                _print_run_info(row[1][0], **kw)

    @pd.api.extensions.register_series_accessor("info")
    class RunInfo(object):

        def __init__(self, s):
            self.s = s

        def __call__(self, **kw):
            _print_run_info(self.s[0], **kw)

def _print_run_info(item, output=False):
    for name in RUN_DETAIL:
        print("%s: %s" % (name, item.fmt.get(name, "")))
    print("flags:", end="")
    print(run_util.format_attr(item.run.get("flags", "")))
    if output:
        print("output:")
        for line in run_util.iter_output(item.run):
            print("  %s" % line, end="")
