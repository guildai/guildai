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

import re
import time

from guild import click_util
import guild.cmd_impl_support
import guild.var

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

def list_runs(args, ctx):
    runs = [
        _format_run(run, i)
        for i, run in enumerate(runs_for_args(args, ctx))
    ]
    cols = ["index", "operation", "started", "status"]
    detail = RUN_DETAIL if args.verbose else None
    guild.cli.table(runs, cols=cols, detail=detail)

def runs_for_args(args, ctx, force_deleted=False):
    return guild.var.runs(
        _runs_root_for_args(args, force_deleted),
        sort=["-started"],
        filter=_runs_filter(args, ctx))

def _runs_root_for_args(args, force_deleted):
    deleted = force_deleted or getattr(args, "deleted", False)
    return guild.var.runs_dir(deleted=deleted)

def _runs_filter(args, ctx):
    filters = []
    _apply_project_models_filter(args, filters, ctx)
    _apply_arg_models_filter(args, filters)
    _apply_status_filter(args, filters)
    return guild.var.run_filter("all", filters)

def _apply_project_models_filter(args, filters, ctx):
    if args.system:
        _maybe_warn_project_location_ignored(args)
    else:
        project = _project_args(args, ctx)
        model_filters = [_model_filter(model) for model in project]
        filters.append(guild.var.run_filter("any", model_filters))

def _model_filter(model):
    return lambda r: r.get("op", "").startswith(model.name + ":")

def _maybe_warn_project_location_ignored(args):
    if args.project_location:
        guild.cli.out(
            "Warning: --system option specified, ignoring project location",
            err=True)

def _project_args(args, ctx):
    return guild.cmd_impl_support.project_for_location(args.project_location, ctx)

def _apply_arg_models_filter(args, filters):
    for model_name in getattr(args, "models", []):
        filters.append(_model_name_filter(model_name))

def _model_name_filter(model_name):
    return lambda r: r.get("op", "").startswith(model_name + ":")

def _apply_status_filter(args, filters):
    status = getattr(args, "status", None)
    if not status:
        return
    if status == "stopped":
        # Special case, filter on any of "terminated" or "error"
        filters.append(
            guild.var.run_filter("any", [
                guild.var.run_filter("attr", "extended_status", "terminated"),
                guild.var.run_filter("attr", "extended_status", "error"),
            ]))
    else:
        filters.append(
            guild.var.run_filter("attr", "extended_status", status))

def _format_run(run, index=None):
    return {
        "id": run.id,
        "index": _format_run_index(run, index),
        "short_index": _format_run_index(run),
        "operation": run.get("op", "?"),
        "status": run.extended_status,
        "pid": run.pid or "(not running)",
        "started": _format_timestamp(run.get("started")),
        "stopped": _format_timestamp(run.get("stopped")),
        "rundir": run.path,
        "command": _format(run.get("cmd", "")),
        "exit_status": run.get("exit_status", ""),
    }

def _format_run_index(run, index=None):
    if index is not None:
        return "[%i:%s]" % (index, run.short_id)
    else:
        return "[%s]" % run.short_id

def _format_timestamp(ts):
    if not ts:
        return ""
    struct_time = time.localtime(float(ts))
    return time.strftime("%Y-%m-%d %H:%M:%S", struct_time)

def _format(cmd):
    args = cmd.split("\n")
    return " ".join([_maybe_quote_arg(arg) for arg in args])

def _maybe_quote_arg(arg):
    return '"%s"' % arg if " " in arg else arg

def _format_attr_val(s):
    parts = s.split("\n")
    if len(parts) == 1:
        return " %s" % parts[0]
    else:
        return "\n%s" % "\n".join(
            ["  %s" % part for part in parts]
        )

def runs_op(args, ctx, force_delete, preview_msg, confirm_prompt, op_callback):
    runs = runs_for_args(args, ctx, force_delete)
    runs_arg = args.runs or ALL_RUNS_ARG
    selected = selected_runs(runs, runs_arg, ctx)
    if not selected:
        _no_selected_runs_error()
    preview = [_format_run(run) for run in selected]
    if not args.yes:
        guild.cli.out(preview_msg)
        cols = ["short_index", "operation", "started", "status"]
        guild.cli.table(preview, cols=cols, indent=2)
    if args.yes or guild.cli.confirm(confirm_prompt):
        op_callback(selected)

def selected_runs(all_runs, selected_specs, cmd_ctx):
    selected = []
    for spec in selected_specs:
        try:
            slice_start, slice_end = _parse_slice(spec)
        except ValueError:
            selected.append(_find_run_by_id(spec, all_runs, cmd_ctx))
        else:
            if _in_range(slice_start, slice_end, all_runs):
                selected.extend(all_runs[slice_start:slice_end])
            else:
                selected.append(_find_run_by_id(spec, all_runs, cmd_ctx))
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

def _find_run_by_id(id_part, runs, cmd_ctx):
    matches = []
    for run in runs:
        if run.id.startswith(id_part):
            matches.append(run)
    if len(matches) == 0:
        _no_matching_run_error(id_part, cmd_ctx)
    elif len(matches) > 1:
        _non_unique_run_id_error(matches)
    else:
        return matches[0]

def _no_matching_run_error(id_part, cmd_ctx):
    guild.cli.error(
        "could not find run matching '%s'\n"
        "Try 'guild runs list' for a list or '%s' for more information."
        % (id_part, click_util.cmd_help(cmd_ctx)))

def _non_unique_run_id_error(matches):
    guild.cli.out("'%s' matches multiple runs:\n", err=True)
    formatted = [_format_run(run) for run in matches]
    cols = ["id", "op", "started", "status"]
    guild.cli.table(formatted, cols=cols, err=True)

def _in_range(slice_start, slice_end, l):
    return (
        (slice_start is None or slice_start >= 0) and
        (slice_end is None or slice_end <= len(l))
    )

def _no_selected_runs_error():
    guild.cli.error(
        "no matching runs\n"
        "Try 'guild runs list' to list available runs.")

def delete_runs(args, ctx):
    if args.purge:
        preview = (
            "WARNING: You are about to permanently delete "
            "the following runs:")
        confirm = "Permanently delete these runs?"
    else:
        preview = "You are about to delete the following runs:"
        confirm = "Delete these runs?"
    def delete(selected):
        guild.var.delete_runs(selected, args.purge)
        if args.purge:
            guild.cli.out("Permanently deleted %i run(s)" % len(selected))
        else:
            guild.cli.out("Deleted %i run(s)" % len(selected))
    runs_op(args, ctx, False, preview, confirm, delete)

def purge_runs(args, ctx):
    preview = (
        "WARNING: You are about to permanently delete "
        "the following runs:")
    confirm = "Permanently delete these runs?"
    def purge(selected):
        guild.var.purge_runs(selected)
        guild.cli.out("Permanently deleted %i run(s)" % len(selected))
    runs_op(args, ctx, True, preview, confirm, purge)

def restore_runs(args, ctx):
    preview = "You are about to permanently restore the following runs:"
    confirm = "Restore these runs?"
    def restore(selected):
        guild.var.restore_runs(selected)
        guild.cli.out("Restored %i run(s)" % len(selected))
    runs_op(args, ctx, True, preview, confirm, restore)

def restore_runs_delme(args, ctx):
    runs = runs_for_args(args, ctx, force_deleted=True)
    runs_arg = args.runs or ALL_RUNS_ARG
    selected = selected_runs(runs, runs_arg, ctx)
    if not selected:
        _no_selected_runs_error()
    preview = [_format_run(run) for run in selected]
    if not args.yes:
        guild.cli.out("You are about to restore the following runs:")
        cols = ["short_index", "operation", "started", "status"]
        guild.cli.table(preview, cols=cols, indent=2)
    if args.yes or guild.cli.confirm("Restore these runs?"):
        guild.var.restore_runs(selected)
        guild.cli.out("Restored %i run(s)" % len(selected))

def run_info(args, ctx):
    runs = runs_for_args(args, ctx)
    runspec = args.run or "0"
    selected = selected_runs(runs, [runspec], ctx)
    if len(selected) == 0:
        _no_selected_runs_error()
    elif len(selected) > 1:
        _non_unique_run_id_error(selected)
    run = selected[0]
    formatted = _format_run(run)
    out = guild.cli.out
    for name in RUN_DETAIL:
        out("%s: %s" % (name, formatted[name]))
    if args.env:
        out("environment:", nl=False)
        out(_format_attr_val(run.get("env", "")))
    if args.flags:
        out("flags:", nl=False)
        out(_format_attr_val(run.get("flags", "")))
    if args.files:
        out("files:")
        for path in run.iter_files():
            out("  %s" % path)
