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
from guild import click_util
from guild import cmd_impl_support
from guild import config
from guild import var

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

def list_runs(args):
    runs = runs_for_args(args)
    formatted = [
        format_run(run, i)
        for i, run in enumerate(runs)
    ]
    cols = ["index", "operation", "started", "status"]
    detail = RUN_DETAIL if args.verbose else None
    cli.table(formatted, cols=cols, detail=detail)

def runs_for_args(args, force_deleted=False):
    return var.runs(
        _runs_root_for_args(args, force_deleted),
        sort=["-started"],
        filter=_runs_filter(args),
        run_init=_init_run)

def _runs_root_for_args(args, force_deleted):
    deleted = force_deleted or getattr(args, "deleted", False)
    return var.runs_dir(deleted=deleted)

def _runs_filter(args):
    filters = []
    _apply_status_filter(args, filters)
    _apply_model_filter(args, filters)
    return var.run_filter("all", filters)

def _apply_status_filter(args, filters):
    status = getattr(args, "status", None)
    if not status:
        return
    if status == "stopped":
        # Special case, filter on any of "terminated" or "error"
        filters.append(
            var.run_filter("any", [
                var.run_filter("attr", "extended_status", "terminated"),
                var.run_filter("attr", "extended_status", "error"),
            ]))
    else:
        filters.append(
            var.run_filter("attr", "extended_status", status))

def _apply_model_filter(args, filters):
    cwd_modelfile = cmd_impl_support.cwd_modelfile_path()
    if cwd_modelfile:
        if not args.all:
            _notify_runs_limited()
            modelfile_dir = os.path.abspath(os.path.dirname(cwd_modelfile))
            filters.append(_cwd_run_filter(modelfile_dir))
    if args.models:
        filters.append(_model_run_filter(args.models))

def _notify_runs_limited():
    cli.note_once(
        "Limiting runs to %s (use --all to include all)"
        % cmd_impl_support.cwd_desc())

def _cwd_run_filter(abs_cwd):
    def f(run):
        if run.opref.pkg_type == "modelfile":
            model_path = os.path.dirname(run.opref.pkg_name)
            if os.path.isabs(model_path):
                if model_path == abs_cwd:
                    return True
            else:
                logging.warning(
                    "unexpected non-absolute modelfile path for run %s: %s",
                    run.id, model_path)
        return False
    return f

def _model_run_filter(model_refs):
    def f(run):
        return any((ref in run.opref.model_name for ref in model_refs))
    return f

def _init_run(run):
    try:
        opref = guild.opref.OpRef.from_run(run)
    except guild.opref.OpRefError as e:
        logging.warning("unable to read opref for run %s: %s", run.id, e)
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
        "operation": _format_op_desc(run.opref),
        "pkg": run.opref.pkg_name,
        "status": run.extended_status,
        "pid": run.pid or "(not running)",
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

def _format_op_desc(opref):
    if opref.pkg_type == "modelfile":
        return _format_modelfile_op(opref)
    elif opref.pkg_type == "package":
        return _format_package_op(opref)
    else:
        logging.warning(
            "cannot format op desc, unexpected pkg type: %s (%s)",
            opref.pkg_type, opref.pkg_name)
        return "?"

def _format_modelfile_op(opref):
    relpath = os.path.relpath(os.path.dirname(opref.pkg_name), config.cwd())
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
        "  %s: %s" % (key, d[key]) for key in sorted(d)
    ])

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

def selected_runs(all_runs, selected_specs, ctx):
    selected = []
    for spec in selected_specs:
        try:
            slice_start, slice_end = _parse_slice(spec)
        except ValueError:
            selected.append(_find_run_by_id(spec, all_runs, ctx))
        else:
            if _in_range(slice_start, slice_end, all_runs):
                selected.extend(all_runs[slice_start:slice_end])
            else:
                selected.append(_find_run_by_id(spec, all_runs, ctx))
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
    if len(matches) == 0:
        _no_matching_run_error(id_part, ctx)
    elif len(matches) > 1:
        _non_unique_run_id_error(matches)
    else:
        return matches[0]

def _no_matching_run_error(id_part, ctx):
    cli.error(
        "could not find run matching '%s'\n"
        "Try 'guild runs list' for a list or '%s' for more information."
        % (id_part, click_util.cmd_help(ctx)))

def _non_unique_run_id_error(matches):
    cli.out("'%s' matches multiple runs:\n", err=True)
    formatted = [format_run(run) for run in matches]
    cols = ["id", "op", "started", "status"]
    cli.table(formatted, cols=cols, err=True)

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
    if len(selected) == 0:
        _no_selected_runs_error()
    elif len(selected) > 1:
        _non_unique_run_id_error(selected)
    run = selected[0]
    formatted = format_run(run)
    out = cli.out
    for name in RUN_DETAIL:
        out("%s: %s" % (name, formatted[name]))
    if args.env:
        out("environment:", nl=False)
        out(_format_attr_val(run.get("env", "")))
    if args.flags:
        out("flags:", nl=False)
        out(_format_attr_val(run.get("flags", "")))
    if args.files or args.all_files:
        out("files:")
        for path in sorted(run.iter_files(args.all_files)):
            out("  %s" % path)
