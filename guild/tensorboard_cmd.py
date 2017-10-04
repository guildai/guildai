import logging
import os
import shutil
import tempfile
import time

import guild.cli
import guild.runs_cmd
import guild.tensorboard
import guild.util

def main(args, ctx):
    runs = guild.runs_cmd.runs_for_args(args, ctx)
    logdir = tempfile.mkdtemp(prefix="guild-tensorboard-logdir-")
    logging.info("Using logdir %s" % logdir)
    for run in runs:
        run_name = _format_run_name(run)
        link_path = os.path.join(logdir, run_name)
        os.symlink(run.path, link_path)
    # TODO: monitor runs_for_args and update links in logdir accordingly
    port = guild.util.free_port()
    guild.tensorboard.main(logdir, "", port, ready_cb=_launch_url)
    _cleanup(logdir)
    guild.cli.out()

def _format_run_name(run):
    model = run.get("op", "").split(":", 1)[0]
    started = run.get("started", "")
    formatted_started = time.strftime(
        "%Y-%m-%d %H:%M:%S",
        time.localtime(float(started)))
    return "%s %s" % (model, formatted_started)

def _launch_url(url):
    guild.util.open_url(url)

def _cleanup(logdir):
    assert os.path.dirname(logdir) == tempfile.gettempdir()
    shutil.rmtree(logdir)
