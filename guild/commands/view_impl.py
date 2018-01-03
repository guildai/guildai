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
import re

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
            return [_run_data(_run_for_id(full_id))]

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
        args = self._args_for_params(params)
        cwd = self._formatted_cwd(params)
        return {
            "cwd": cwd,
            "titleLabel": self._title_label(params, args, cwd),
        }

    def _title_label(self, params, args, cwd):
        if params.has_key("run"):
            return self._single_run_title_label(params["run"])
        elif args.all:
            return self._all_title_label(args)
        else:
            return self._cwd_title_label(cwd)

    @staticmethod
    def _single_run_title_label(run_id):
        return "[{}]".format(run_id)

    @staticmethod
    def _all_title_label(args):
        if args.ops:
            return "all {}".format(" ".join(args.ops))
        else:
            return "all"

    @staticmethod
    def _cwd_title_label(cwd):
        parts = cwd.split(os.path.sep)
        if len(parts) < 2:
            return cwd
        else:
            return os.path.join(*parts[-2:])

def _run_for_id(run_id):
    return runs_impl.init_run(var.get_run(run_id))

def _run_data(run):
    formatted = runs_impl.format_run(run)
    return {
        "id": run.id,
        "shortId": run.short_id,
        "path": run.path,
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
        "deps": _format_deps(run.get("deps", {})),
        "files": _format_files(run.iter_files(), run.path),
    }

def _format_deps(deps):
    runs_dir = var.runs_dir()
    runs = {}
    for paths in deps.values():
        for path in paths:
            if not path.startswith(runs_dir):
                continue
            subdir = path[len(runs_dir)+1:]
            parts = subdir.split(os.path.sep)
            run_id = parts[0]
            try:
                run, run_paths = runs[run_id]
            except KeyError:
                run = _run_for_id(run_id)
                run_paths = []
                runs[run_id] = run, run_paths
            run_paths.append(os.path.join(*parts[1:]))
    formatted = [_format_dep(run, paths) for run, paths in runs.values()]
    return sorted(formatted, key=lambda x: x["operation"])

def _format_dep(run, paths):
    return {
        "run": run.short_id,
        "operation": runs_impl.format_op_desc(run.opref, nowarn=True),
        "paths": paths
    }

def _format_files(files, root):
    filtered = [
        path for path in files
        if os.path.islink(path) or os.path.isfile(path)
    ]
    formatted = [_format_file(path, root) for path in filtered]
    return sorted(formatted, key=lambda x: x["path"])

def _format_file(path, root):
    size = os.path.getsize(path)
    typeDesc, icon, iconTooltip, viewer = _file_type_info(path)
    opDesc, opRun = _op_source_info(path)
    relpath = path[len(root)+1:]
    return {
        "path": relpath,
        "size": size,
        "type": typeDesc,
        "icon": icon,
        "iconTooltip": iconTooltip,
        "viewer": viewer,
        "operation": opDesc,
        "run": opRun,
    }

def _file_type_info(path):
    typeDesc, icon, iconTooltip, viewer = _base_file_type_info(path)
    if os.path.islink(path):
        target = os.path.realpath(path)
        link_type = "directory" if os.path.isdir(target) else "file"
        if target.startswith(var.runs_dir()):
            typeDesc = "Link to operation output"
        elif target.startswith(var.cache_dir()):
            typeDesc = "Link to resource {}".format(link_type)
        else:
            typeDesc = "Link"
        icon = "folder-move" if link_type == "directory" else "file-send"
        iconTooltip = "Link"
    return typeDesc, icon, iconTooltip, viewer

def _base_file_type_info(path):
    lower_path = path.lower()
    if re.search(r"\.tfevents\.", lower_path):
        return "Event log", "file", "File", None
    elif re.search(r"\.index$", lower_path):
        return "Checkpoint index", "file", "File", None
    elif re.search(r"\.meta$", lower_path):
        return "Checkpoint meta graph", "file", "File", None
    elif re.search(r"[/\\]checkpoint$", lower_path):
        return "Latest checkpoint marker", "file", "File", None
    elif re.search(r"data-\d+-of-\d+$", lower_path):
        return "Checkpoint values", "file", "File", None
    elif re.search(r"\.tfrecord$", lower_path):
        return "Dataset file", "file", "File", None
    elif re.search(r"\.(jpg|jpeg|gif|png|tiff)$", lower_path):
        return "Image", "file-image", "Image", "image"
    elif re.search(r"\.(mid|wav)", lower_path):
        return "Audio", "file-music", "Audio", None
    else:
        if util.is_text_file(path):
            return "Text file", "file-document", "Text file", "text"
        else:
            return "File", "file", "File", None

def _op_source_info(path):
    if not os.path.islink(path):
        return None, None
    path = os.path.realpath(path)
    runs_dir = var.runs_dir()
    if not path.startswith(runs_dir):
        return None, None
    subdir = path[len(runs_dir)+1:]
    parts = subdir.split(os.path.sep, 1)
    run = _run_for_id(parts[0])
    operation = runs_impl.format_op_desc(run.opref, nowarn=True)
    return operation, run.short_id

def main(args):
    data = ViewDataImpl(args)
    host = args.host or ""
    port = args.port or util.free_port()
    view.serve_forever(data, host, port, args.no_open, args.dev)
