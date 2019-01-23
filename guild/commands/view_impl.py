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

import logging
import os
import re
import socket

import click

import guild
import guild.run

from guild import cli
from guild import config
from guild import op_util
from guild import util
from guild import var
from guild import view

from guild.commands import runs_impl

log = logging.getLogger("guild")

VIEW_FILES_REFRESH_INTERVAL = 3

class ViewDataImpl(view.ViewData):

    def __init__(self, args):
        self._args = args

    def runs(self):
        return runs_impl.runs_for_args(self._args)

    def runs_data(self):
        return list(self._runs_data_iter(self.runs()))

    @staticmethod
    def one_run(run_id_prefix):
        try:
            id, path = next(var.find_runs(run_id_prefix))
        except StopIteration:
            return None
        else:
            return guild.run.Run(id, path)

    def one_run_data(self, run_id_prefix):
        run = self.one_run(run_id_prefix)
        if not run:
            return None
        return self._run_data(run)

    def _runs_data_iter(self, runs):
        for run in runs:
            try:
                yield self._run_data(run)
            except Exception as e:
                if log.getEffectiveLevel() <= logging.DEBUG:
                    log.exception("error processing run data for %s", run.id)
                else:
                    log.error("error processing run data for %s: %r", run.id, e)

    def _run_data(self, run):
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
            "time": self._run_duration(run),
            "label": formatted["label"],
            "status": run.status,
            "exitStatus": formatted["exit_status"] or None,
            "command": formatted["command"],
            "otherAttrs": self._other_attrs(run),
            "flags": run.get("flags", {}),
            "env": run.get("env", {}),
            "deps": self._format_deps(run.get("deps", {})),
            "files": self._format_files(run.iter_files(), run.path),
        }

    @staticmethod
    def _run_duration(run):
        started = run.get("started")
        if run.status == "running":
            return util.format_duration(started)
        stopped = run.get("stopped")
        if stopped:
            return util.format_duration(started, stopped)
        return ""

    @staticmethod
    def _other_attrs(run):
        return {
            name: run.get(name)
            for name in runs_impl.other_attr_names(run)
        }

    def _format_deps(self, deps):
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
                    run_paths = []
                    try:
                        run = self._run_for_id(run_id)
                    except LookupError:
                        # Dep run is missing - silently drop it from
                        # the list of deps.
                        pass
                    else:
                        runs[run_id] = run, run_paths
                run_paths.append(os.path.join(*parts[1:]))
        formatted = [
            self._format_dep(run, paths)
            for run, paths in runs.values()
        ]
        return sorted(formatted, key=lambda x: x["operation"])

    @staticmethod
    def _run_for_id(run_id):
        return var.get_run(run_id)

    @staticmethod
    def _format_dep(run, paths):
        return {
            "run": run.short_id,
            "operation": op_util.format_op_desc(run, nowarn=True),
            "paths": paths
        }

    def _format_files(self, files, root):
        filtered = [
            path for path in files
            if os.path.islink(path) or os.path.isfile(path)
        ]
        formatted = [self._format_file(path, root) for path in filtered]
        return sorted(formatted, key=lambda x: x["path"])

    def _format_file(self, path, root):
        typeDesc, icon, iconTooltip, viewer = self._file_type_info(path)
        opDesc, opRun = self._op_source_info(path)
        relpath = path[len(root)+1:]
        mtime = util.safe_mtime(path)
        if mtime:
            mtime = int(mtime * 1000)
        return {
            "path": relpath,
            "size": util.safe_filesize(path),
            "mtime": mtime,
            "type": typeDesc,
            "icon": icon,
            "iconTooltip": iconTooltip,
            "viewer": viewer,
            "operation": opDesc,
            "run": opRun,
        }

    def _file_type_info(self, path):
        typeDesc, icon, iconTooltip, viewer = self._base_file_type_info(path)
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

    @staticmethod
    def _base_file_type_info(path):
        path_lower = path.lower()
        if re.search(r"\.tfevents\.", path_lower):
            return "Event log", "file-chart", "File", None
        elif re.search(r"saved_model\.pb$", path_lower):
            return "SavedModel protocol buffer", "file", "File", None
        elif re.search(r"graph\.pb$", path_lower):
            return "GraphDef protocol buffer", "file", "File", None
        elif re.search(r"saved_model\.pbtxt$", path_lower):
            return (
                "SavedModel protocol buffer", "file-document", "Text file",
                "text")
        elif re.search(r"graph\.pbtxt$", path_lower):
            return (
                "GraphDef protocol buffer", "file-document", "Text file",
                "text")
        elif re.search(r"\.index$", path_lower):
            return "Checkpoint index", "file", "File", None
        elif re.search(r"\.meta$", path_lower):
            return "Checkpoint meta graph", "file", "File", None
        elif re.search(r"[/\\]checkpoint$", path_lower):
            return "Latest checkpoint marker", "file", "File", None
        elif re.search(r"data-\d+-of-\d+$", path_lower):
            return "Checkpoint values", "file", "File", None
        elif re.search(r"\.tfrecord$", path_lower):
            return "Dataset file", "file", "File", None
        elif re.search(r"\.(jpg|jpeg|gif|png|tiff)$", path_lower):
            return "Image", "file-image", "Image", "image"
        elif re.search(r"\.mid", path_lower):
            return "Audio", "file-music", "Audio", "midi"
        elif re.search(r"\.(wav|mp3)", path_lower):
            return "Audio", "file-music", "Audio", None
        elif re.search(r"\.(csv|tsv)", path_lower):
            return "Table", "file-delimited", "Delimited", "table"
        else:
            if util.is_text_file(path):
                return "Text file", "file-document", "Text file", "text"
            else:
                return "File", "file", "File", None

    def _op_source_info(self, path):
        if not os.path.islink(path):
            return None, None
        path = os.path.realpath(path)
        runs_dir = var.runs_dir()
        if not path.startswith(runs_dir):
            return None, None
        subdir = path[len(runs_dir)+1:]
        parts = subdir.split(os.path.sep, 1)
        try:
            run = self._run_for_id(parts[0])
        except LookupError:
            return "%s (deleted)" % parts[0][:8], None
        else:
            operation = op_util.format_op_desc(run, nowarn=True)
            return operation, run.short_id

    def config(self):
        cwd = util.format_dir(config.cwd())
        return {
            "cwd": cwd,
            "titleLabel": self._title_label(cwd),
            "version": guild.version(),
        }

    def _title_label(self, cwd):
        if len(self._args.runs) == 1:
            return self._single_run_title_label(self._args.runs[0])
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

def main(args):
    if args.files:
        _view_files(args)
    else:
        _start_view(args)

def _view_files(args):
    with util.TempDir("guild-view-") as logdir:
        log.debug("Using logdir %s", logdir)
        list_runs_cb = lambda: runs_impl.runs_for_args(args)
        monitor = util.RunsMonitor(
            list_runs_cb, logdir, VIEW_FILES_REFRESH_INTERVAL)
        monitor.start()
        click.launch(logdir)
        print("Monitoring runs at %s (Press CTRL+C to quit)" % logdir)
        try:
            util.wait_forever()
        except KeyboardInterrupt:
            pass
        log.debug("Stopping")
        monitor.stop()
        log.debug("Removing logdir %s", logdir) # Handled by ctx mgr
    if util.PLATFORM != "Windows":
        cli.out()

def _start_view(args):
    data = ViewDataImpl(args)
    host = _host(args)
    port = args.port or util.free_port()
    if args.test:
        _start_tester(host, port)
        args.no_open = True
    try:
        view.serve_forever(
            data,
            host,
            port,
            args.no_open,
            args.dev,
            args.logging)
    except socket.gaierror as e:
        cli.error(str(e))

def _host(args):
    if args.host:
        return args.host
    if args.dev:
        return "localhost"
    return "0.0.0.0"

def _start_tester(host, port):
    from . import view_tester
    view_tester.start_tester(host, port, os._exit)
