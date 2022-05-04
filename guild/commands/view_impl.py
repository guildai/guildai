# Copyright 2017-2022 RStudio, PBC
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

import json
import logging
import os
import re
import socket
import sys

import guild
import guild.run

from guild import batch_util
from guild import cli
from guild import click_util
from guild import config
from guild import index as indexlib
from guild import run_util
from guild import util
from guild import var
from guild import view

from . import compare_impl
from . import runs_impl

log = logging.getLogger("guild")

VIEW_FILES_REFRESH_INTERVAL = 3


class ViewDataImpl(view.ViewData):
    def __init__(self, args):
        self._args = args
        self._compare_args = self._init_compare_args(args)

    @staticmethod
    def _init_compare_args(view_args):
        return click_util.Args(
            extra_cols=False,
            cols=None,
            strict_cols=None,
            top=None,
            min_col=None,
            max_col=None,
            limit=None,
            skip_core=False,
            skip_op_cols=False,
            all_scalars=False,
            skip_unchanged=False,
            **view_args.as_kw()
        )

    def runs(self):
        runs = runs_impl.runs_for_args(self._args)
        if self._args.include_batch:
            return runs
        return [run for run in runs if not batch_util.is_batch(run)]

    def runs_data(self):
        return list(self._runs_data_iter(self.runs()))

    @staticmethod
    def one_run(run_id_prefix, *_):
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
        index = self._init_index([run])
        return self._run_data(run, index)

    def _runs_data_iter(self, runs):
        index = self._init_index(runs)
        for run in runs:
            try:
                yield self._run_data(run, index)
            except Exception as e:
                if log.getEffectiveLevel() <= logging.DEBUG:
                    log.exception("error processing run data for %s", run.id)
                else:
                    log.error("error processing run data for %s: %r", run.id, e)

    @staticmethod
    def _init_index(runs):
        index = indexlib.RunIndex()
        index.refresh(runs, ["scalar"])
        return index

    def _run_data(self, run, index):
        formatted = run_util.format_run(run)
        return {
            "id": run.id,
            "shortId": run.short_id,
            "dir": run.dir,
            "operation": formatted["operation"],
            "opModel": run.opref.model_name,
            "opName": run.opref.op_name,
            "started": formatted["started"],
            "stopped": formatted["stopped"],
            "time": self._run_duration(run),
            "label": formatted["label"],
            "tags": self._format_tags(run.get("tags") or []),
            "comments": run.get("comments") or [],
            "status": run.status,
            "exitStatus": formatted["exit_status"],
            "command": formatted["command"],
            "otherAttrs": self._other_attrs(run),
            "flags": run.get("flags", {}),
            "scalars": self._run_scalars(run, index),
            "env": run.get("env", {}),
            "deps": self._format_deps(run.get("deps", {})),
            "files": self._format_files(run.iter_files(), run.path),
            "sourcecode": _sourcecode_data(run),
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
    def _format_tags(tags):
        return ", ".join(tags)

    @staticmethod
    def _other_attrs(run):
        return {name: run.get(name) for name in runs_impl.other_attr_names(run)}

    @staticmethod
    def _run_scalars(run, index):
        return index.run_scalars(run)

    def _format_deps(self, deps):
        runs_dir = var.runs_dir()
        runs = {}
        for paths in deps.values():
            for path in paths:
                if not path.startswith(runs_dir):
                    continue
                subdir = path[len(runs_dir) + 1 :]
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
        formatted = [self._format_dep(run, paths) for run, paths in runs.values()]
        return sorted(formatted, key=lambda x: x["operation"])

    @staticmethod
    def _run_for_id(run_id):
        return var.get_run(run_id)

    @staticmethod
    def _format_dep(run, paths):
        return {
            "run": run.short_id,
            "operation": run_util.format_operation(run, nowarn=True),
            "paths": paths,
        }

    def _format_files(self, files, root):
        filtered = [
            path for path in files if os.path.islink(path) or os.path.isfile(path)
        ]
        formatted = [self._format_file(path, root) for path in filtered]
        return util.natsorted(formatted, key=lambda x: x["path"])

    def _format_file(self, path, root):
        typeDesc, icon, iconTooltip, viewer = self._file_type_info(path)
        opDesc, opRun = self._op_source_info(path)
        relpath = path[len(root) + 1 :]
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
            target = util.realpath(path)
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

    def _base_file_type_info(self, path):
        path_lower = path.lower()
        if re.search(r"\.tfevents\.", path_lower):
            return "Event log", "file-chart", "File", None
        elif re.search(r"saved_model\.pb$", path_lower):
            return "SavedModel protocol buffer", "file", "File", None
        elif re.search(r"graph\.pb$", path_lower):
            return "GraphDef protocol buffer", "file", "File", None
        elif re.search(r"saved_model\.pbtxt$", path_lower):
            return ("SavedModel protocol buffer", "file-document", "Text file", "text")
        elif re.search(r"graph\.pbtxt$", path_lower):
            return ("GraphDef protocol buffer", "file-document", "Text file", "text")
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
            return self._default_file_type_info(path)

    @staticmethod
    def _default_file_type_info(path):
        if not os.path.exists(path):
            return "File", "file", "File", None
        if util.is_text_file(path):
            return "Text file", "file-document", "Text file", "text"
        return "File", "file", "File", None

    def _op_source_info(self, path):
        if not os.path.islink(path):
            return None, None
        path = util.realpath(path)
        runs_dir = var.runs_dir()
        if not path.startswith(runs_dir):
            return None, None
        subdir = path[len(runs_dir) + 1 :]
        parts = subdir.split(os.path.sep, 1)
        try:
            run = self._run_for_id(parts[0])
        except LookupError:
            return "%s (deleted)" % parts[0][:8], None
        else:
            operation = run_util.format_operation(run, nowarn=True)
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

    def compare_data(self):
        return compare_impl.get_data(self._compare_args, format_cells=False)


def _sourcecode_data(run):
    rel_root = _sourcecode_root(run)
    root = os.path.join(run.dir, rel_root)
    files = sorted(_iter_sourcecode_files(root))
    return {
        "root": rel_root,
        "files": files,
    }


def _sourcecode_root(run):
    op = run.get("op")
    # pylint: disable=consider-using-ternary
    return (op and op.get("sourcecode-root")) or ".guild/sourcecode"


def _iter_sourcecode_files(path):
    for root, _dirs, files in os.walk(path):
        for name in files:
            yield os.path.relpath(os.path.join(root, name), path)


def main(args):
    if args.test_runs_data:
        _test_runs_data(args)
    else:
        _start_view(args)


def _test_runs_data(args):
    data = ViewDataImpl(args)
    runs_data = data.runs_data()
    view.fix_runs_data_for_json(runs_data)
    json.dump(runs_data, sys.stdout)


def _start_view(args):
    data = ViewDataImpl(args)
    host = _host(args)
    port = args.port or util.free_port()
    if args.test:
        _start_tester(host, port)
        args.no_open = True
    try:
        view.serve_forever(data, host, port, args.no_open, args.dev, args.logging)
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
