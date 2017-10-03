import os
import tempfile
import time

import guild.runs_cmd
import guild.tensorboard

def main(args, ctx):
    runs = guild.runs_cmd.runs_for_args(args, ctx)
    logdir = tempfile.mkdtemp(prefix="guild-tensorboard-logdir-")
    for run in runs:
        run_name = _format_run_name(run)
        link_path = os.path.join(logdir, run_name)
        os.symlink(run.path, link_path)
    # TODO: monitor runs_for_args and update links in logdir accordingly
    guild.tensorboard.main(logdir, "", 6006)

def _format_run_name(run):
    model = run.get("op", "").split(":", 1)[0]
    started = run.get("started", "")
    formatted_started = time.strftime(
        "%Y-%m-%d %H:%M:%S",
        time.localtime(float(started)))
    return "%s %s" % (model, formatted_started)
