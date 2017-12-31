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

from guild import click_util
from guild import config
from guild import util
from guild import var
from guild import view

from guild.commands import runs_impl

class ViewDataImpl(view.ViewData):

    def __init__(self, args):
        self._args = args

    def runs(self, params):
        if params.has_key("run"):
            return self._one_run(params["run"])
        else:
            return self._runs(params)

    @staticmethod
    def _one_run(run_id):
        try:
            full_id, _ = next(var.find_runs(run_id))
        except StopIteration:
            return []
        else:
            run = var.get_run(full_id)
            inited_run = runs_impl.init_run(run)
            return [_run_data(inited_run)]

    def _runs(self, params):
        args = self._args_for_params(params)
        with config.SetCwd(self._cwd(params)):
            runs = runs_impl.runs_for_args(args)
        return [_run_data(run) for run in runs]

    def _args_for_params(self, params):
        if not params:
            return self._args
        return click_util.Args({
            "ops": tuple(params.getlist("op")),
            "running": params.has_key("running"),
            "completed": params.has_key("completed"),
            "error": params.has_key("error"),
            "terminated": params.has_key("terminated"),
            "all": params.has_key("all"),
        })

    @staticmethod
    def _cwd(params):
        return params.get("cwd") or config.cwd()

    def _formatted_cwd(self, params):
        cwd = self._cwd(params)
        abs_cwd = os.path.abspath(cwd)
        user_dir = os.getenv("HOME")
        if abs_cwd.startswith(user_dir):
            return os.path.join("~", abs_cwd[len(user_dir)+1:])
        else:
            return abs_cwd

    def config(self, params):
        cwd = self._formatted_cwd(params)
        return {
            "cwd": cwd,
            "titleLabel": self._title_label(params, cwd),
        }

    def _title_label(self, params, cwd):
        if params.has_key("run"):
            return self._single_run_title_label(params["run"])
        else:
            return self._cwd_title_label(cwd)

    @staticmethod
    def _single_run_title_label(run_id):
        return "[{}]".format(run_id)

    @staticmethod
    def _cwd_title_label(cwd):
        parts = cwd.split(os.path.sep)
        if len(parts) < 2:
            return cwd
        else:
            return os.path.join(*parts[-2:])

def _run_data(run):
    formatted = runs_impl.format_run(run)
    return {
        "id": run.id,
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
