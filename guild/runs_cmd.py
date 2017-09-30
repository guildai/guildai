import time

import guild.cli
import guild.var

def list(args):
    guild.cli.table(
        [_format_run(run) for run in guild.var.runs()],
        cols=["id", "op", "started", "status"],
        detail=(
            ["pid", "stopped"]
            if args.verbose else []))

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
