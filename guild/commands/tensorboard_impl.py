# Copyright 2017-2020 TensorHub, Inc.
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

import csv
import logging
import os
import re
import sys
import time

from guild import batch_util
from guild import cli
from guild import op_util
from guild import run_util
from guild import tfevent
from guild import util

from . import runs_impl

log = logging.getLogger("guild")


DEFAULT_PREPARE_THRESHOLD = 5  # seconds


def main(args):
    if args.check:
        _check()
    elif args.export_scalars:
        _export_scalars(args)
    else:
        _run_tensorboard(args)


def _check():
    from guild.plugins import tensorboard

    tensorboard.check()


def _export_scalars(args):
    with _open_file(args.export_scalars) as f:
        out = csv.writer(f)
        out.writerow(["run", "path", "tag", "value", "step"])
        for run in _list_runs_cb(args)():
            for path, _digest, reader in tfevent.scalar_readers(run.dir):
                subpath = os.path.relpath(path, run.dir)
                for tag, value, step in reader:
                    out.writerow([run.id, subpath, tag, value, step])


def _open_file(path):
    if path == "-":
        return util.StdIOContextManager(sys.stdout)
    util.ensure_dir(os.path.dirname(path))
    try:
        return open(path, "w")
    except (OSError, IOError) as e:
        cli.error("error opening %s: %s" % (path, e))


def _run_tensorboard(args):
    from guild import tensorboard

    tensorboard.setup_logging()
    with util.TempDir("guild-tensorboard-", keep=args.keep_logdir) as tmp:
        logdir = tmp.path
        (log.info if args.keep_logdir else log.debug)("Using logdir %s", logdir)
        tensorboard_options = _tensorboard_options(args)
        monitor = tensorboard.RunsMonitor(
            logdir,
            _list_runs_cb(args),
            interval=args.refresh_interval,
            log_images=not args.skip_images,
            log_hparams=not args.skip_hparams,
            run_name_cb=_run_name_cb(args),
        )
        t0 = time.time()
        cli.out("Preparing runs for TensorBoard")
        monitor.run_once(exit_on_error=True)
        _maybe_log_prepare_time(t0)
        monitor.start()
        try:
            tensorboard.serve_forever(
                logdir=logdir,
                host=(args.host or "0.0.0.0"),
                port=(args.port or util.free_port()),
                reload_interval=args.refresh_interval,
                tensorboard_options=tensorboard_options,
                ready_cb=_open_cb(args),
            )
        except tensorboard.TensorboardError as e:
            cli.error(str(e))
        finally:
            log.debug("Stopping")
            monitor.stop()
            if not args.keep_logdir:
                # Removal of temp logdir occurs when context manager
                # exits.
                log.debug("Removing logdir %s", logdir)
            else:
                print("TensorBoard logs saved in %s" % logdir)
    if util.PLATFORM != "Windows":
        cli.out()


def _maybe_log_prepare_time(t0):
    prepare_time = time.time() - t0
    if prepare_time > _prepare_threshold():
        log.warning(
            "Guild took %0.2f seconds to prepare runs. To reduce startup time, "
            "try running with '--skip-images' or '--skip-hparams' options "
            "or reduce the number of runs with filters. Try 'guild tensorboard "
            "--help' for filter options.",
            prepare_time,
        )


def _prepare_threshold():
    try:
        return float(os.environ["PREPARE_THRESHOLD"])
    except (KeyError, ValueError):
        return DEFAULT_PREPARE_THRESHOLD


def _tensorboard_options(args):
    return dict([_parse_tensorboard_opt(opt) for opt in args.tensorboard_options])


def _parse_tensorboard_opt(opt):
    parts = opt.split("=", 1)
    if len(parts) != 2:
        cli.error("invalid TensorBoard option %r - must be OPTION=VALUE" % opt)
    return parts


def _run_name_cb(args):
    if args.run_name_flags is None:
        return None

    label_template = _run_label_template(args.run_name_flags)

    def f(run):
        flags = run.get("flags")
        return run_util.run_name(run, _run_label(label_template, flags))

    return f


def _run_label(label_template, flags):
    if not label_template:
        return ""
    return op_util.run_label(label_template, flags)


def _run_label_template(flags_arg):
    flags = _split_flags(flags_arg)
    return " ".join(["%s=${%s}" % (flag, flag) for flag in flags])


def _split_flags(flags_arg):
    return [arg.strip() for arg in re.split(r"[ ,]", flags_arg) if arg]


def _list_runs_cb(args):
    def f():
        runs = runs_impl.runs_for_args(args)
        if args.include_batch:
            return runs
        return _remove_batch_runs(runs)

    return f


def _remove_batch_runs(runs):
    return [run for run in runs if not batch_util.is_batch(run)]


def _open_cb(args):
    if args.no_open:
        return None

    def f(url):
        if args.tab:
            url += "#" + args.tab
        util.open_url(url)

    return f
