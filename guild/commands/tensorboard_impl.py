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

from guild import cli
from guild import util

from . import runs_impl

log = logging.getLogger("guild")

def main(args):
    tensorboard = _load_guild_tensorboard_module()
    tensorboard.setup_logging()
    with util.TempDir("guild-tensorboard-") as logdir:
        log.debug("Using logdir %s", logdir)
        list_runs_cb = lambda: runs_impl.runs_for_args(args)
        monitor = tensorboard.RunsMonitor(
            list_runs_cb, logdir, args.refresh_interval)
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

def _load_guild_tensorboard_module():
    try:
        from guild import tensorboard
    except ImportError as e:
        _handle_tensorboard_import_error(e)
    else:
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

def _open_url(url):
    util.open_url(url)
