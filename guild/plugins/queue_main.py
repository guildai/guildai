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

import argparse
import logging
import os
import time

from guild import _api as gapi
from guild import log as loglib
from guild import util
from guild import var

log = logging.getLogger("queue")

RUN_ID = os.environ["RUN_ID"]

class _State(object):

    def __init__(self):
        self.show_waiting_msg = True

def main():
    args = _parse_args()
    init_logging()
    poll(args.poll_interval)

def _parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--poll-interval", type=int, default=10)
    return p.parse_args()

def init_logging():
    level = int(os.getenv("LOG_LEVEL", logging.WARN))
    format = os.getenv("LOG_FORMAT", "%(levelname)s: [%(name)s] %(message)s")
    loglib.init_logging(level, {"_": format})

def poll(interval):
    state = _State()
    util.loop(lambda: _run_pending(state), time.sleep, interval, 0)

def _run_pending(state):
    for run in _pending_runs():
        log.info("Found pending run %s", run.id)
        runs = _running_runs()
        if runs:
            log.debug(
                "Runs in progress %s, skipping pending run %s",
                [run.short_id for run in runs], run.short_id)
            break
        _run(run, state)
    _log_waiting(state)

def _log_waiting(state):
    if state.show_waiting_msg:
        log.info("Waiting for pending runs")
        state.show_waiting_msg = False
    else:
        log.debug("Checking for pending runs")

def _pending_runs():
    return var.runs(
        sort=["timestamp"],
        filter=var.run_filter("attr", "status", "pending"))

def _running_runs():
    running = var.runs(filter=var.run_filter("attr", "status", "running"))
    return [run for run in running if run.id != RUN_ID]

def _run(run, state):
    log.info("Starting %s", run.id)
    gapi.run(restart=run.id, extra_env={"NO_RESTARTING_MSG": "1"})
    state.show_waiting_msg = True

if __name__ == "__main__":
    main()
