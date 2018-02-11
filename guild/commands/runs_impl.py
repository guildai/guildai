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

import logging
import os
import re
import time

import guild.opref
import guild.run

from guild import cli
from guild import cmd_impl_support
from guild import config
from guild import util
from guild import var

log = logging.getLogger("guild")

RUN_DETAIL = [
    "id",
    "operation",
    "status",
    "started",
    "stopped",
    "rundir",
    "command",
    "exit_status",
    "pid",
]

ALL_RUNS_ARG = [":"]

CORE_RUN_ATTRS = [
    "cmd",
    "env",
    "exit_status",
    "flags",
    "opref",
    "started",
    "stopped",
    "deps",
]

def list_runs(args):
    runs = runs_for_args(args)
    formatted = [
        format_run(run, i)
        for i, run in enumerate(runs)
    ]
    filtered = _filter_runs(formatted, args.filters)
    cols = ["index", "operation", "started", "status", "label"]
    detail = RUN_DETAIL if args.verbose else None
    cli.table(filtered, cols=cols, detail=detail)

def runs_for_args(args, force_deleted=False):
    return var.runs(
        _runs_root_for_args(args, force_deleted),
        sort=["-started"],
        filter=_runs_filter(args),
        run_init=init_run)

def _runs_root_for_args(args, force_deleted):
    deleted = force_deleted or getattr(args, "deleted", False)
    return var.runs_dir(deleted=deleted)

def _runs_filter(args):
    filters = []
    _apply_status_filter(args, filters)
    _apply_cwd_modelfile_filter(args, filters)
    _apply_ops_filter(args, filters)
    _apply_run_id_filter(args, filters)
    return var.run_filter("all", filters)

def _apply_status_filter(args, filters):
    status_filters = [
        var.run_filter("attr", "status", status)
        for status in ["running", "completed", "error", "terminated"]
        if getattr(args, status)
    ]
    if status_filters:
        filters.append(var.run_filter("any", status_filters))

def _apply_cwd_modelfile_filter(args, filters):
    cwd_modelfile = cmd_impl_support.cwd_modelfile()
    if cwd_modelfile and not args.all:
        _notify_runs_limited()
        modelfile_dir = os.path.abspath(cwd_modelfile.dir)
        filters.append(_cwd_run_filter(modelfile_dir))

def _notify_runs_limited():
    cli.note_once(
        "Limiting runs to %s (use --all to include all)"
        % cmd_impl_support.cwd_desc())

def _cwd_run_filter(abs_cwd):
    def f(run):
        if run.opref.pkg_type == "modelfile":
            model_dir = run.opref.pkg_name
            if os.path.isabs(model_dir):
                if model_dir == abs_cwd:
                    return True
            else:
                log.warning(
                    "unexpected non-absolute modelfile path for run %s: %s",
                    run.id, model_dir)
        return False
    return f

def _apply_ops_filter(args, filters):
    if args.ops:
        filters.append(_op_run_filter(args.ops))

def _op_run_filter(op_refs):
    def f(run):
        op_desc = format_op_desc(run.opref, nowarn=True)
        return any((ref in op_desc for ref in op_refs))
    return f

def _apply_run_id_filter(args, filters):
    if args.run_ids:
        filters.append(_run_id_filter(args.run_ids))

def _run_id_filter(run_ids):
    def f(run):
        return any((run.id.startswith(id) for id in run_ids))
    return f

def init_run(run):
    try:
        opref = guild.opref.OpRef.from_run(run)
    except guild.opref.OpRefError as e:
        log.warning("unable to read opref for run %s: %s", run.id, e)
        return None
    else:
        run.opref = opref
        return run

def format_run(run, index=None):
    return {
        "id": run.id,
        "index": _format_run_index(run, index),
        "short_index": _format_run_index(run),
        "model": run.opref.model_name,
        "op_name": run.opref.op_name,
        "operation": format_op_desc(run.opref),
        "pkg": run.opref.pkg_name,
        "status": run.status,
        "label": run.get("label") or "",
        "pid": run.pid or "",
        "started": _format_timestamp(run.get("started")),
        "stopped": _format_timestamp(run.get("stopped")),
        "rundir": run.path,
        "command": _format_command(run.get("cmd", "")),
        "exit_status": run.get("exit_status", ""),
    }

def _format_run_index(run, index=None):
    if index is not None:
        return "[%i:%s]" % (index, run.short_id)
    else:
        return "[%s]" % run.short_id

def format_op_desc(opref, nowarn=False):
    if opref.pkg_type == "modelfile":
        return _format_modelfile_op(opref)
    elif opref.pkg_type == "package":
        return _format_package_op(opref)
    else:
        if not nowarn:
            log.warning(
                "cannot format op desc, unexpected pkg type: %s (%s)",
                opref.pkg_type, opref.pkg_name)
        return "?"

def _format_modelfile_op(opref):
    relpath = os.path.relpath(opref.pkg_name, config.cwd())
    if relpath[0] != '.':
        relpath = os.path.join('.', relpath)
    return "%s/%s:%s" % (relpath, opref.model_name, opref.op_name)

def _format_package_op(opref):
    return "%s/%s:%s" % (opref.pkg_name, opref.model_name, opref.op_name)

def _format_timestamp(ts):
    if not ts:
        return ""
    struct_time = time.localtime(guild.run.timestamp_seconds(ts))
    return time.strftime("%Y-%m-%d %H:%M:%S", struct_time)

def _format_command(cmd):
    if not cmd:
        return ""
    return " ".join([_maybe_quote_arg(arg) for arg in cmd])

def _maybe_quote_arg(arg):
    return '"%s"' % arg if " " in arg else arg

def _format_attr_val(val):
    if isinstance(val, list):
        return _format_attr_list(val)
    elif isinstance(val, dict):
        return _format_attr_dict(val)
    else:
        return str(val)

def _format_attr_list(l):
    return "\n%s" % "\n".join([
        "  %s" % item for item in l
    ])

def _format_attr_dict(d):
    return "\n%s" % "\n".join([
        "  %s: %s" % (key, d[key] or "") for key in sorted(d)
    ])

def _filter_runs(runs, filters):
    return [run for run in runs if _filter_run(run, filters)]

def _filter_run(run, filters):
    filter_vals = [
        run["model"],
        run["op_name"],
        run["label"],
    ]
    return util.match_filters(filters, filter_vals)

def _runs_op(args, ctx, force_delete, preview_msg, confirm_prompt,
             no_runs_help, op_callback):
    runs = runs_for_args(args, force_delete)
    runs_arg = args.runs or ALL_RUNS_ARG
    selected = selected_runs(runs, runs_arg, ctx)
    if not selected:
        _no_selected_runs_error(no_runs_help)
    preview = [format_run(run) for run in selected]
    if not args.yes:
        cli.out(preview_msg)
        cols = ["short_index", "operation", "started", "status"]
        cli.table(preview, cols=cols, indent=2)
    if args.yes or cli.confirm(confirm_prompt):
        op_callback(selected)

def selected_runs(runs, select_specs, ctx=None):
    selected = []
    for spec in select_specs:
        try:
            slice_start, slice_end = _parse_slice(spec)
        except ValueError:
            selected.append(_find_run_by_id(spec, runs, ctx))
        else:
            if _in_range(slice_start, slice_end, runs):
                selected.extend(runs[slice_start:slice_end])
            else:
                selected.append(_find_run_by_id(spec, runs, ctx))
    return selected

def _parse_slice(spec):
    try:
        index = int(spec)
    except ValueError:
        m = re.match("(\\d+)?:(\\d+)?", spec)
        if m:
            try:
                return (
                    _slice_part(m.group(1)),
                    _slice_part(m.group(2), incr=True)
                )
            except ValueError:
                pass
        raise ValueError(spec)
    else:
        return index, index + 1

def _slice_part(s, incr=False):
    if s is None:
        return None
    elif incr:
        return int(s) + 1
    else:
        return int(s)

def _find_run_by_id(id_part, runs, ctx):
    matches = []
    for run in runs:
        if run.id.startswith(id_part):
            matches.append(run)
    return cmd_impl_support.one_run(matches, id_part, ctx)

def _in_range(slice_start, slice_end, l):
    return (
        (slice_start is None or slice_start >= 0) and
        (slice_end is None or slice_end <= len(l))
    )

def _no_selected_runs_error(help_msg=None):
    help_msg = help_msg or "Try 'guild runs list' to list available runs."
    cli.error("no matching runs\n%s" % help_msg)

def delete_runs(args, ctx):
    if args.permanent:
        preview = (
            "WARNING: You are about to permanently delete "
            "the following runs:")
        confirm = "Permanently delete these runs?"
    else:
        preview = "You are about to delete the following runs:"
        confirm = "Delete these runs?"
    no_runs_help = "Nothing to delete."
    def delete(selected):
        var.delete_runs(selected, args.permanent)
        if args.permanent:
            cli.out("Permanently deleted %i run(s)" % len(selected))
        else:
            cli.out("Deleted %i run(s)" % len(selected))
    _runs_op(args, ctx, False, preview, confirm, no_runs_help, delete)

def purge_runs(args, ctx):
    preview = (
        "WARNING: You are about to permanently delete "
        "the following runs:")
    confirm = "Permanently delete these runs?"
    no_runs_help = "Nothing to purge."
    def purge(selected):
        var.purge_runs(selected)
        cli.out("Permanently deleted %i run(s)" % len(selected))
    _runs_op(args, ctx, True, preview, confirm, no_runs_help, purge)

def restore_runs(args, ctx):
    preview = "You are about to restore the following runs:"
    confirm = "Restore these runs?"
    no_runs_help = "Nothing to restore."
    def restore(selected):
        var.restore_runs(selected)
        cli.out("Restored %i run(s)" % len(selected))
    _runs_op(args, ctx, True, preview, confirm, no_runs_help, restore)

def run_info(args, ctx):
    runs = runs_for_args(args)
    runspec = args.run or "0"
    selected = selected_runs(runs, [runspec], ctx)
    run = cmd_impl_support.one_run(selected, runspec, ctx)
    formatted = format_run(run)
    out = cli.out
    for name in RUN_DETAIL:
        out("%s: %s" % (name, formatted[name]))
    for name in run.attr_names():
        if name not in CORE_RUN_ATTRS:
            out("%s: %s" % (name, run.get(name, "")))
    if args.env:
        out("environment:", nl=False)
        out(_format_attr_val(run.get("env", "")))
    if args.flags:
        out("flags:", nl=False)
        out(_format_attr_val(run.get("flags", "")))
    if args.deps:
        out("dependencies:")
        deps = run.get("deps", {})
        for name in sorted(deps):
            out("  %s:" % name)
            for path in deps[name]:
                out("    %s" % path)
    if args.files or args.all_files:
        out("files:")
        for path in sorted(run.iter_files(args.all_files, args.follow_links)):
            if not args.full_path:
                path = os.path.relpath(path, run.path)
            out("  %s" % path)

def label(args):
    run = cmd_impl_support.one_run([
        guild.run.Run(id, path) for id, path in var.find_runs(args.run)
    ], args.run)
    if args.clear:
        run.del_attr("label")
    elif args.label:
        run.write_attr("label", args.label)
    else:
        cli.out(run.get("label", ""))
