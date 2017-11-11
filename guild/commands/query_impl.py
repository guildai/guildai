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

from tabview import tabview

from . import runs_impl

ViewerBase = tabview.Viewer

class Viewer(ViewerBase):

    help_args = None

    def __init__(self, *args, **kw):
        assert self.help_args is not None
        args = (args[0], self._init_data()) + args[2:]
        # pylint: disable=non-parent-init-called
        ViewerBase.__init__(self, *args, **kw)

    def _init_data(self):
        runs = runs_impl.runs_for_args(self.help_args)
        runs_arg = self.help_args.runs or runs_impl.ALL_RUNS_ARG
        selected = runs_impl.selected_runs(runs, runs_arg)
        header = [
            "Run",
            "Model",
            "Operation",
            "Started",
            "Status",
            "Label",
            "Accuracy",
        ]
        import random
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
        data = [header] + vals
        return tabview.process_data(data)

    def location_string(self, yp, xp):
        lstr = ViewerBase.location_string(self, yp, xp)
        return lstr.replace("-,", "")

    def define_keys(self):
        ViewerBase.define_keys(self)
        del self.keys["t"]

def compare(args):
    tabview.Viewer = _init_tabview_viewer(args)
    tabview.view(
        [[]],
        column_width="max",
        info="Guild run comparison",
    )

def _init_tabview_viewer(args):
    Viewer.help_args = args
    return Viewer
