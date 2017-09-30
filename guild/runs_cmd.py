import guild.cli
import guild.var

def list(_args):
    guild.cli.table(
        [_format_run(run) for run in guild.var.runs()],
        cols=["id", "op", "status"])

def _format_run(run):
    return {
        "id": run.short_id,
        "op": run.get("op", "?"),
        "status": run.extended_status,
    }

def delete(args):
    print("TODO: delete runs %s" % (args.runs,))
