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

    def runs(self):
        runs = runs_impl.runs_for_args(self._args)
        return self._filter_batch_runs(runs)

    def _filter_batch_runs(self, runs):
        """Filter out batch runs unless otherwise configured.

        Batch runs are included if `include_batch` or `deleted` is specified in
        args. We include batch runs when listing deleted for consistency with
        'guild runs list'.
        """
        if self._args.include_batch or self._args.deleted:
            return runs
        return [run for run in runs if not batch_util.is_batch(run)]

    def runs_data(self, api_version=1):
        return list(self._runs_data_iter(self.runs(), api_version))

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
        return run_data(run, index)

    def _runs_data_iter(self, runs, api_version):
        index = self._init_index(runs)
        for run in runs:
            try:
                yield run_data(run, index, api_version)
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

    def config(self):
        cwd = util.format_dir(config.cwd())
        return {
            "cwd": cwd,
            "titleLabel": self._title_label(cwd),
            "version": guild.__version__,
        }

    def _title_label(self, cwd):
        if len(self._args.runs) == 1:
            return self._single_run_title_label(self._args.runs[0])
        return self._cwd_title_label(cwd)

    @staticmethod
    def _single_run_title_label(run_id):
        return f"[{run_id}]"

    @staticmethod
    def _all_title_label(args):
        if args.ops:
            return f"all {' '.join(args.ops)}"
        return "all"

    @staticmethod
    def _cwd_title_label(cwd):
        parts = cwd.split(os.path.sep)
        if len(parts) < 2:
            return cwd
        return os.path.join(*parts[-2:])

    def compare_data(self):
        compare_args = _compare_args_for_view_args(self._args)
        return compare_impl.get_compare_data(compare_args, format_cells=False)


def run_data(run, index=None, api_version=1):
    if api_version == 1:
        return _run_data_v1(run, index)
    if api_version == 2:
        return _run_data_v2(run, index)
    assert False, api_version


def _run_data_v1(run, index):
    formatted = run_util.format_run(run)
    data = {
        "id": run.id,
        "shortId": run.short_id,
        "dir": run.dir,
        "operation": formatted["operation"],
        "started": formatted["started"],
        "stopped": formatted["stopped"],
        "time": _run_duration(run),
        "label": formatted["label"],
        "tags": _format_tags(run.get("tags") or []),
        "comments": run.get("comments") or [],
        "status": run.status,
        "exitStatus": formatted["exit_status"],
        "command": formatted["command"],
        "otherAttrs": _other_attrs(run),
        "flags": run.get("flags", {}),
        "env": run.get("env", {}),
        "deps": _format_deps(run.get("deps", {})),
        "files": _format_files(run.iter_files(), run.path),
        "sourcecode": _sourcecode_data(run),
        "projectDir": run_util.run_op_dir(run),
        "opRef": _opref_data(run),
        "marked": run.get("marked") or False
    }
    if index:
        data["scalars"] = _run_scalars(run, index)
    return data


def _run_data_v2(run, index):
    data = _run_data_v1(run, index)
    data["tags"] = run.get("tags") or []
    data["started"] = run.get("started")
    data["stopped"] = run.get("stopped")
    del data["time"]
    return data


def _run_duration(run):
    started = run.get("started")
    if run.status == "running":
        return util.format_duration(started)
    stopped = run.get("stopped")
    if stopped:
        return util.format_duration(started, stopped)
    return ""


def _format_tags(tags):
    return ", ".join(tags)


def _other_attrs(run):
    return {name: run.get(name) for name in runs_impl.other_attr_names(run)}


def _format_deps(deps):
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
                    run = _run_for_id(run_id)
                except LookupError:
                    # Dep run is missing - silently drop it from the
                    # list of deps.
                    pass
                else:
                    runs[run_id] = run, run_paths
            run_paths.append(os.path.join(*parts[1:]))
    formatted = [_format_dep(run, paths) for run, paths in runs.values()]
    return sorted(formatted, key=lambda x: x["operation"])


def _run_for_id(run_id):
    return var.get_run(run_id)


def _format_dep(run, paths):
    return {
        "run": run.short_id,
        "operation": run_util.format_operation(run, nowarn=True),
        "paths": paths,
    }


def _format_files(files, root):
    filtered = [path for path in files if os.path.islink(path) or os.path.isfile(path)]
    formatted = [_format_file(path, root) for path in filtered]
    return util.natsorted(formatted, key=lambda x: x["path"])


def _format_file(path, root):
    typeDesc, icon, iconTooltip, viewer = _file_type_info(path)
    opDesc, opRun = _op_source_info(path)
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


def _file_type_info(path):
    typeDesc, icon, iconTooltip, viewer = _base_file_type_info(path)
    if os.path.islink(path):
        target = util.realpath(path)
        link_type = "directory" if os.path.isdir(target) else "file"
        if target.startswith(var.runs_dir()):
            typeDesc = "Link to operation output"
        elif target.startswith(var.cache_dir()):
            typeDesc = f"Link to resource {link_type}"
        else:
            typeDesc = "Link"
        icon = "folder-move" if link_type == "directory" else "file-send"
        iconTooltip = "Link"
    return typeDesc, icon, iconTooltip, viewer


def _base_file_type_info(path):
    path_lower = path.lower()
    if re.search(r"\.tfevents\.", path_lower):
        return "Event log", "file-chart", "File", None
    if re.search(r"saved_model\.pb$", path_lower):
        return "SavedModel protocol buffer", "file", "File", None
    if re.search(r"graph\.pb$", path_lower):
        return "GraphDef protocol buffer", "file", "File", None
    if re.search(r"saved_model\.pbtxt$", path_lower):
        return ("SavedModel protocol buffer", "file-document", "Text file", "text")
    if re.search(r"graph\.pbtxt$", path_lower):
        return ("GraphDef protocol buffer", "file-document", "Text file", "text")
    if re.search(r"\.index$", path_lower):
        return "Checkpoint index", "file", "File", None
    if re.search(r"\.meta$", path_lower):
        return "Checkpoint meta graph", "file", "File", None
    if re.search(r"[/\\]checkpoint$", path_lower):
        return "Latest checkpoint marker", "file", "File", None
    if re.search(r"data-\d+-of-\d+$", path_lower):
        return "Checkpoint values", "file", "File", None
    if re.search(r"\.tfrecord$", path_lower):
        return "Dataset file", "file", "File", None
    if re.search(r"\.(jpg|jpeg|gif|png|tiff)$", path_lower):
        return "Image", "file-image", "Image", "image"
    if re.search(r"\.mid", path_lower):
        return "Audio", "file-music", "Audio", "midi"
    if re.search(r"\.(wav|mp3)", path_lower):
        return "Audio", "file-music", "Audio", None
    if re.search(r"\.(csv|tsv)", path_lower):
        return "Table", "file-delimited", "Delimited", "table"
    return _default_file_type_info(path)


def _default_file_type_info(path):
    if not os.path.exists(path):
        return "File", "file", "File", None
    if util.is_text_file(path):
        return "Text file", "file-document", "Text file", "text"
    return "File", "file", "File", None


def _op_source_info(path):
    if not os.path.islink(path):
        return None, None
    path = util.realpath(path)
    runs_dir = var.runs_dir()
    if not path.startswith(runs_dir):
        return None, None
    subdir = path[len(runs_dir) + 1 :]
    parts = subdir.split(os.path.sep, 1)
    try:
        run = _run_for_id(parts[0])
    except LookupError:
        return f"{parts[0]} (deleted)", None
    else:
        operation = run_util.format_operation(run, nowarn=True)
        return operation, run.short_id


def _run_scalars(run, index):
    return index.run_scalars(run)


def _compare_args_for_view_args(view_args):
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
        **view_args.as_kw(),
    )


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


def _opref_data(run):
    if not run.opref:
        return None
    return {
        "pkgType": run.opref.pkg_type,
        "pkgName": run.opref.pkg_name,
        "pkgVersion": run.opref.pkg_version,
        "modelName": run.opref.model_name,
        "opName": run.opref.op_name,
    }


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
