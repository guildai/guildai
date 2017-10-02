import time

import guild.cli
import guild.cmd_support
import guild.var

def list_runs(args):
    runs_filter = _runs_filter(args)
    runs = [_format_run(run) for run in guild.var.runs(filter=runs_filter)]
    cols = ["id", "op", "started", "status"]
    detail = ["pid", "stopped"] if args.verbose else None
    guild.cli.table(runs, cols=cols, detail=detail)

def _runs_filter(args):
    filters = []
    _apply_project_models_filter(args, filters)
    return guild.var.run_filter("all", filters)

def _apply_project_models_filter(args, filters):
    if args.all:
        _maybe_warn_project_location_ignored(args)
    else:
        project = _project_for_list_args(args)
        model_filters = [_model_filter(model) for model in project]
        filters.append(guild.var.run_filter("any", model_filters))

def _model_filter(model):
    return lambda r: r.get("op", "").startswith(model.name + ":")

def _maybe_warn_project_location_ignored(args):
    if args.project_location:
        guild.cli.out(
            "--all option specified, ignoring project location",
            err=True)

def _project_for_list_args(args):
    project = guild.cmd_support.find_project_for_location(
        args.project_location)
    if project is None:
        guild.cli.error(
            "%s does not contain any models\n"
            "Try specifying a project location or use --all to list all runs."
            % guild.cmd_support.project_location_desc(args.project_location))
    return project

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

def delete(args):
    print("TODO: delete runs %s" % (args.runs,))
