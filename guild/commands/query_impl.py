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

from . import runs_impl

def compare(args):
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
        import random
        runs = runs_impl.runs_for_args(args)
        runs_arg = args.runs or runs_impl.ALL_RUNS_ARG
        selected = runs_impl.selected_runs(runs, runs_arg)
        vals = [_run_data(run, index) for run in selected]
        return [header] + vals
    return get_runs

def _run_data(run, index):
    indexed = index.get_run(run.id)
    return [
        indexed.short_id,
        indexed.model_name,
        indexed.op_name,
        indexed.started,
        indexed.status,
        indexed.label,
        indexed.scalar(["validate/accuracy", "val_acc"], ""),
    ]
