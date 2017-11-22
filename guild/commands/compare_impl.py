# Copyright 2017 TensorHub, Inc.
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

from guild import config
from guild import tabview
from guild import util
from guild import var

from . import runs_impl

def main(args):
    if args.format == "csv":
        _print_csv(args)
    else:
        _tabview(args)

def _print_csv(args):
    index = guild.index.RunIndex()
    runs, _logs = _get_runs_cb(args, index)()
    writer = csv.writer(sys.stdout)
    for row in runs:
        writer.writerow(row)

def _tabview(args):
    config.set_log_output(True)
    index = guild.index.RunIndex()
    tabview.view_runs(
        _get_runs_cb(args, index),
        _get_run_detail_cb(index))

def _get_runs_cb(args, index):
    header = [
        "Run",
        "Model",
        "Operation",
        "Started",
        "Status",
        "Label",
        "Accuracy",
        "Loss",
    ]
    def get_runs():
        _init_tf_logging()
        log_capture = util.LogCapture()
        with log_capture:
            runs = runs_impl.runs_for_args(args)
            filtered = _filter_runs(runs, args.filters)
            vals = _runs_data(filtered, index)
        return [header] + vals, log_capture.get_all()
    return get_runs

def _filter_runs(runs, filters):
    return [run for run in runs if _filter_run(run, filters)]

def _filter_run(run, filters):
    opref = guild.opref.OpRef.from_run(run)
    filter_vals = [
        opref.model_name,
        opref.op_name,
        run.get("label", ""),
    ]
    return util.match_filters(filters, filter_vals)

def _init_tf_logging():
    """Load TensorFlow, forcing init of TF logging.

    This is part of our handing of logging, which can interfere with
    the curses display used by tabview. By forcing an init of TF logs,
    we can patch loggers with LogCapture (see guild.tabview module)
    for display in a curses window.
    """
    import tensorflow

def _runs_data(selected, index):
    ids = [run.id for run in selected]
    return [_run_data(run) for run in index.runs(ids)]

def _run_data(run):
    return [
        run.short_id,
        run.model_name,
        run.op_name,
        util.format_timestamp(run.started),
        run.status,
        run.label,
        _run_accuracy(run),
        _run_loss(run),
    ]

def _run_accuracy(run):
    search_keys = [
        "val_acc",
        "validate/accuracy",
        "eval/accuracy",
    ]
    return _format_float(run.scalar(search_keys))

def _run_loss(run):
    search_keys = [
        "loss",
        "train/loss",
        "total_loss_1" # slim models
    ]
    return _format_float(run.scalar(search_keys))

def _format_float(x):
    return ("%0.6f" % x) if x is not None else ""

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
            lines.append("  {}: {}".format(name, val))
    scalars = sorted(run.iter_scalars())
    if scalars:
        lines.append("Scalars (last recorded value):")
        for key, val in scalars:
            lines.append("  {}: {}".format(key, val))
    return "\n".join(lines)
