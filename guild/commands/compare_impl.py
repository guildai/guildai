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

from guild import tabview
from guild import util

from . import runs_impl

def main(args):
    if args.format == "csv":
        _print_csv(args)
    else:
        _tabview(args)

def _print_csv(args):
    runs = _get_runs_cb(args)()
    writer = csv.writer(sys.stdout)
    for row in runs:
        writer.writerow(row)

def _tabview(args):
    tabview.view_runs(_get_runs_cb(args))

def _get_runs_cb(args):
    header = [
        "Run",
        "Model",
        "Operation",
        "Started",
        "Status",
        "Label",
        "Accuracy",
    ]
    index = guild.index.RunIndex()
    def get_runs():
        _init_tf_logging()
        log_capture = util.LogCapture()
        with log_capture:
            runs = runs_impl.runs_for_args(args)
            runs_arg = args.runs or runs_impl.ALL_RUNS_ARG
            selected = runs_impl.selected_runs(runs, runs_arg)
            vals = _runs_data(selected, index)
        return [header] + vals, log_capture.get_all()
    return get_runs

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
        run.started,
        run.status,
        run.label,
        _run_accuracy(run),
    ]

def _run_accuracy(run):
    return run.scalar(["accuracy", "val_acc", "validate/accuracy"], "")
