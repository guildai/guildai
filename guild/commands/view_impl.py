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

import os

from guild import config
from guild import util
from guild import view

from guild.commands import runs_impl

class ViewDataImpl(view.ViewData):

    def __init__(self, args):
        self._args = args
        self._config = {
            "cwd": os.path.abspath(config.cwd())
        }

    def runs(self):
        return [_run_data(run) for run in runs_impl.runs_for_args(self._args)]

    def config(self):
        return self._config

def _run_data(run):
    formatted = runs_impl.format_run(run)
    return {
        "shortId": run.short_id,
        "operation": formatted["operation"],
        "opModel": run.opref.model_name,
        "opName": run.opref.op_name,
        "started": formatted["started"],
        "stopped": formatted["stopped"],
        "status": run.status,
        "exitStatus": formatted["exit_status"] or None,
        "command": formatted["command"],
        "flags": run.get("flags", {}),
        "env": run.get("env", {}),
        "deps": [],
        "files": [],
    }

def main(args):
    data = ViewDataImpl(args)
    host = args.host or ""
    port = args.port or util.free_port()
    view.serve_forever(data, host, port, args.no_open, args.dev)
