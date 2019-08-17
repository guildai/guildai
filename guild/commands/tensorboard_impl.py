# Copyright 2017-2019 TensorHub, Inc.
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

from guild import batch_util
from guild import cli
from guild import util

from . import runs_impl

log = logging.getLogger("guild")

def main(args):
    tensorboard = _guild_tensorboard_module()
    with util.TempDir("guild-tensorboard-") as tmp:
        logdir = tmp.path
        log.debug("Using logdir %s", logdir)
        monitor = tensorboard.RunsMonitor(
            logdir,
            _list_runs_cb(args),
            args.refresh_interval)
        monitor.run_once(exit_on_error=True)
        monitor.start()
        try:
            tensorboard.serve_forever(
                logdir=logdir,
                host=(args.host or "0.0.0.0"),
                port=(args.port or util.free_port()),
                reload_interval=args.refresh_interval,
                ready_cb=(_open_url if not args.no_open else None))
        except tensorboard.TensorboardError as e:
            cli.error(str(e))
        finally:
            log.debug("Stopping")
            monitor.stop()
            log.debug("Removing logdir %s", logdir) # Handled by ctx mgr
    if util.PLATFORM != "Windows":
        cli.out()

def _guild_tensorboard_module():
    try:
        from guild import tensorboard
    except ImportError as e:
        _handle_tensorboard_import_error(e)
    else:
        tensorboard.setup_logging()
        return tensorboard

def _handle_tensorboard_import_error(e):
    if "tensorflow" in str(e):
        cli.out(
            "TensorBoard cannot not be started because TensorFlow "
            "is not installed.\n"
            "Refer to https://www.tensorflow.org/install/ for help "
            "installing TensorFlow on your system.", err=True)
    else:
        cli.out("TensorBoard could not be started: %s" % e, err=True)
    cli.error()

def _list_runs_cb(args):
    return lambda: _runs_for_args(args)

def _runs_for_args(args):
    runs = runs_impl.runs_for_args(args)
    if args.include_batch:
        return runs
    return _remove_batch_runs(runs)

def _remove_batch_runs(runs):
    return [run for run in runs if not batch_util.is_batch(run)]

def _open_url(url):
    util.open_url(url)
