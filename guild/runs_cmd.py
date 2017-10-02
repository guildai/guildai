import re
import time

import guild.cli
import guild.cmd_support
import guild.var

def list_runs(args):
    runs = [_format_run(run) for run in _runs_for_args(args, "list")]
    cols = ["id", "op", "started", "status"]
    detail = ["pid", "stopped"] if args.verbose else None
    guild.cli.table(runs, cols=cols, detail=detail)

def _runs_for_args(args, context_cmd):
    return guild.var.runs(
        sort=["-started"],
        filter=_runs_filter(args, context_cmd))

def _runs_filter(args, context_cmd):
    filters = []
    _apply_project_models_filter(args, filters, context_cmd)
    return guild.var.run_filter("all", filters)

def _apply_project_models_filter(args, filters, context_cmd):
    if args.all:
        _maybe_warn_project_location_ignored(args)
    else:
        project = _project_args(args, context_cmd)
        model_filters = [_model_filter(model) for model in project]
        filters.append(guild.var.run_filter("any", model_filters))

def _model_filter(model):
    return lambda r: r.get("op", "").startswith(model.name + ":")

def _maybe_warn_project_location_ignored(args):
    if args.project_location:
        guild.cli.out(
            "--all option specified, ignoring project location",
            err=True)

def _project_args(args, context_cmd):
    return guild.cmd_support.project_for_location(
        args.project_location,
        "guild runs %s --help" % context_cmd)

def _format_run(run):
    return {
        "id": "[%s]" % run.short_id,
        "op": run.get("op", "?"),
        "status": run.extended_status,
        "pid": run.pid or "",
        "started": _format_timestamp(run.get("started")),
        "stopped": _format_timestamp(run.get("stopped")),
    }

def _format_timestamp(ts):
    if not ts:
        return ""
    struct_time = time.localtime(float(ts))
    return time.strftime("%Y-%m-%d %H:%M:%S", struct_time)

def delete_runs(args):
    runs = _runs_for_args(args, "delete")
    selected = _selected_runs(runs, args.runs)
    if not selected:
        _no_selected_runs_error()
    formatted = [_format_run(run) for run in selected]
    if not args.yes:
        guild.cli.out("You are about to delete the following runs:")
        cols = ["id", "op", "started", "status"]
        guild.cli.table(formatted, cols=cols, indent=2)
    if guild.cli.confirm("Delete these runs?"):
        guild.var.delete_runs(selected)
        guild.cli.out("Deleted %i run(s)" % len(selected))
    
def _selected_runs(all_runs, selected_specs):
    selected = []
    for spec in selected_specs:
        try:
            slice_start, slice_end = _parse_slice(spec)
        except ValueError:
            selected.append(_find_run_by_id(spec, all_runs))
        else:
            if _in_range(slice_start, slice_end, all_runs):
                selected.extend(all_runs[slice_start:slice_end])
            else:
                selected.append(_find_run_by_id(spec, all_runs)) 
    return selected

def _parse_slice(spec):
    try:
        index = int(spec)
    except ValueError:
        m = re.match("(\\d+)?:(\\d+)?", spec)
        if m:
            try:
                return _slice_part(m.group(1)), _slice_part(m.group(2))
            except ValueError:
                pass
        raise ValueError(spec)    
    else:
        return index, index + 1

def _slice_part(s):
    return None if s is None else int(s)

def _find_run_by_id(id_part, runs):
    matches = []
    for run in runs:
        if run.id.startswith(id_part):
            matches.append(run)
    if len(matches) == 0:
        _no_matching_run_error(id_part)
    elif len(matches) > 1:
        _non_unique_run_id_error(matches)
    else:
        return matches[0]

def _no_matching_run_error(id_part):
    guild.cli.error(
        "could not find run matching '%s'\n"
        "Try 'guild runs list' to list available runs."
        % id_part)

def _non_unique_run_id_error(matches):
    guild.cli.out("'%s' matches multiple runs:\n", err=True)
    formatted = [_format_run(run) for run in _runs_for_args(args, "list")]
    cols = ["id", "op", "started", "status"]
    guild.cli.table(formatted, cols=cols, err=True)

def _in_range(start, end, l):
    return (
        start is None or start >= 0 and
        end is None or end < len(l))

def _no_selected_runs_error():
    guild.cli.error(
        "no matching runs\n"
        "Try 'guild runs list' to list available runs.")
