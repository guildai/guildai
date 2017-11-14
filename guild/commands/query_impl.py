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

from guild import tabview

from . import runs_impl

def compare(args):
    tabview.view_runs(get_runs_cb(args))

def get_runs_cb(args):
    header = [
        "Run",
        "Model",
        "Operation",
        "Started",
        "Status",
        "Label",
        "Accuracy",
    ]
    def get_runs():
        import random
        runs = runs_impl.runs_for_args(args)
        runs_arg = args.runs or runs_impl.ALL_RUNS_ARG
        selected = runs_impl.selected_runs(runs, runs_arg)
        vals = [
            [
                run.short_id,
                run.opref.model_name,
                run.opref.op_name,
                runs_impl._format_timestamp(run.get("started")),
                run.status,
                run.get("label") or "",
                "%0.6f" % random.uniform(0, 1),
            ] for run in selected
        ]
        return [header] + vals
    return get_runs
