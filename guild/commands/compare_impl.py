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

import csv
import sys

import guild.index

from guild import cli
from guild import config
from guild import tabview
from guild import util
from guild import var
from guild import view

from . import runs_impl

def main(args):
    if args.format == "csv":
        _print_csv(args)
    elif args.format == "table":
        _print_table(args)
    else:
        _tabview(args)

def _print_csv(args):
    index = guild.index.RunIndex()
    runs, _logs = _get_runs_cb(args, index)()
    writer = csv.writer(sys.stdout)
    for row in runs:
        writer.writerow(row)

def _print_table(args):
    index = guild.index.RunIndex()
    runs, _logs = _get_runs_cb(args, index)()
    cols = runs[0]
    col_indexes = list(zip(cols, range(len(cols))))
    def format_row(row):
        return {
            col_name: row[i]
            for col_name, i in col_indexes
        }
    heading = {
        col_name: col_name
        for col_name in cols
    }
    data = [heading] + [format_row(row) for row in runs[1:]]
    cli.table(data, cols)

def _tabview(args):
    config.set_log_output(True)
    index = guild.index.RunIndex()
    tabview.view_runs(
        _get_runs_cb(args, index),
        _get_run_detail_cb(index))

def _get_runs_cb(args, index):
    def get_runs():
        _try_init_tf_logging()
        log_capture = util.LogCapture()
        with log_capture:
            runs = runs_impl.runs_for_args(args)
            flags = _compare_flags(runs)
            header = _runs_header(flags)
            data = _runs_data(runs, flags, index)
            log = log_capture.get_all()
        return [header] + data, log
    return get_runs

def _try_init_tf_logging():
    """Load TensorFlow, forcing init of TF logging.

    This is part of our handing of logging, which can interfere with
    the curses display used by tabview. By forcing an init of TF logs,
    we can patch loggers with LogCapture (see guild.tabview module)
    for display in a curses window.
    """
    try:
        import tensorflow as _
    except ImportError:
        pass

def _compare_flags(runs):
    flags = set()
    for run in runs:
        flags.update(run.get("_extra_compare", {}).get("flags", []))
    return sorted(flags)

def _runs_header(flags):
    base = [
        "run",
        "model",
        "operation",
        "started",
        "time",
        "status",
        "label",
        "step",
        "accuracy",
        "loss",
    ]
    return base + flags

def _runs_data(selected, flags, index):
    ids = [run.id for run in selected]
    return [_run_data(run, flags) for run in index.runs(ids)]

def _run_data(run, flags):
    flag_vals = dict(run.iter_flags())
    base_data = [
        run.short_id,
        run.model_name,
        run.op_name,
        util.format_timestamp(run.started),
        _run_duration(run),
        run.status,
        run.label,
        _scalar_step(run),
        _run_accuracy(run),
        _run_loss(run),
    ]
    flag_data = [flag_vals.get(name, "") for name in flags]
    return base_data + flag_data

def _run_duration(run):
    if run.status == "running":
        return util.format_duration(run.started)
    elif run.stopped:
        return util.format_duration(run.started, run.stopped)
    else:
        return ""

def _scalar_step(run):
    search_keys = view.SCALAR_KEYS[0][1]
    return _format_int(run.scalar(search_keys))

def _run_accuracy(run):
    search_keys = view.SCALAR_KEYS[2][1]
    return _format_float(run.scalar(search_keys))

def _run_loss(run):
    search_keys = view.SCALAR_KEYS[1][1]
    return _format_float(run.scalar(search_keys))

def _format_float(x):
    return ("%0.6f" % x) if x is not None else ""

def _format_int(x):
    return ("%i" % x) if x is not None else ""

def _get_run_detail_cb(index):
    def get_detail(data, y, _x):
        run_short_id = data[y][0]
        title = "Run {}".format(run_short_id)
        try:
            run_id, _ = next(var.find_runs(run_short_id))
        except StopIteration:
            return "This run no longer exists", title
        else:
            hits = index.runs([run_id])
            if not hits:
                return "Detail not available", title
            else:
                return _format_run_detail(hits[0]), title
    return get_detail

def _format_run_detail(run):
    lines = [
        "Id: {}".format(run.id),
        "Model: {}".format(run.model_name),
        "Operation: {}".format(run.op_name),
        "Status: {}".format(run.status),
        "Started: {}".format(util.format_timestamp(run.started)),
        "Stopped: {}".format(util.format_timestamp(run.stopped)),
        "Label: {}".format(run.label),
    ]
    flags = sorted(run.iter_flags())
    if flags:
        lines.append("Flags:")
        for name, val in flags:
            val = val if val is not None else ""
            lines.append("  {}: {}".format(name.decode(), val))
    scalars = sorted(run.iter_scalars())
    if scalars:
        lines.append("Scalars (last recorded value):")
        for key, val in scalars:
            lines.append("  {}: {}".format(key.decode(), val))
    return "\n".join(lines)
