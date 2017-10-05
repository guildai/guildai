import re
import time

import guild.cli
import guild.cmd_support
import guild.var

RUN_DETAIL = [
    "id",
    "operation",
    "status",
    "started",
    "stopped",
    "rundir",
    "command",
    "environ",
    "exit_status",
    "pid",
]

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
    return guild.cmd_support.project_for_location(args.project_location, ctx)

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
        "command": _format_cmd(run.get("cmd", "")),
        "environ": _format_attr_val(run.get("env", "")),
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

def _format_cmd(cmd):
    args = cmd.split("\n")
    return " ".join([_maybe_quote_cmd_arg(arg) for arg in args])

def _maybe_quote_cmd_arg(arg):
    return '"%s"' % arg if " " in arg else arg

def _format_attr_val(s):
    parts = s.split("\n")
    if len(parts) == 1:
        return " %s" % parts[0]
    else:
        return "\n%s" % "\n".join(
            ["    %s" % part for part in parts]
        )

def delete_runs(args, ctx):
    runs = runs_for_args(args, ctx)
    selected = selected_runs(runs, args.runs, ctx)
    if not selected:
        _no_selected_runs_error()
    preview = [_format_run(run) for run in selected]
    if not args.yes:
        guild.cli.out("You are about to delete the following runs:")
        cols = ["short_index", "operation", "started", "status"]
        guild.cli.table(preview, cols=cols, indent=2)
    if args.yes or guild.cli.confirm("Delete these runs?"):
        guild.var.delete_runs(selected)
        guild.cli.out("Deleted %i run(s)" % len(selected))

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
        % (id_part, guild.cli.ctx_cmd_help(cmd_ctx)))

def _non_unique_run_id_error(matches):
    guild.cli.out("'%s' matches multiple runs:\n", err=True)
    formatted = [_format_run(run) for run in runs_for_args(args, "list")]
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

def restore_runs(args, ctx):
    runs = runs_for_args(args, ctx, force_deleted=True)
    selected = selected_runs(runs, args.runs, ctx)
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
        _non_unique_run_id_error(matches)
    run = selected[0]
    formatted = _format_run(run)
    out = guild.cli.out
    for name in RUN_DETAIL:
        out("%s: %s" % (name, formatted[name]))
    if args.files:
        out("files:")
        for path in run.iter_files():
            out("  %s" % path)
