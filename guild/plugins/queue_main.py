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

import argparse
import logging
import os
import time

from guild import _api as gapi
from guild import lock as locklib
from guild import op_util
from guild import util
from guild import var

logging.basicConfig(
    level=int(os.getenv("LOG_LEVEL", logging.INFO)),
    format="%(levelname)s: [%(name)s] %(asctime)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

RUN_STATUS_LOCK_TIMEOUT = 30

log = logging.getLogger("queue")


class _State(object):
    def __init__(self, args):
        for name, val in args._get_kwargs():
            setattr(self, name, val)
        self.run_id = os.environ["RUN_ID"]
        self.gpu_mismatch = set()
        self.waiting = set()
        self.logged_waiting = False
        self.lock = locklib.Lock(locklib.RUN_STATUS, timeout=RUN_STATUS_LOCK_TIMEOUT)


def main():
    args = _parse_args()
    if args.run_once:
        run_once(args)
    else:
        poll(args)


def _parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--poll-interval", type=int, default=10)
    p.add_argument("--run-once", action="store_true")
    p.add_argument("--wait-for-running", action="store_true")
    p.add_argument("--gpus")
    return p.parse_args()


def run_once(args):
    log.info("Processing staged runs")
    _run_staged(_State(args))


def poll(args):
    state = _State(args)
    util.loop(lambda: _run_staged(state), time.sleep, args.poll_interval, 0)


def _run_staged(state):
    while True:
        run = _safe_next_run(state)
        if not run:
            break
        _start_run(run, state)
    if not state.logged_waiting:
        _log_waiting(state)


def _safe_next_run(state):
    """Uses a system wide lock to get the next run."""
    try:
        state.lock.acquire()
    except locklib.Timeout as e:
        log.warning(
            "could not acquire lock for reading staged runs\n"
            "If this error persists, try stopping all queues and "
            "deleting %s",
            e.lock_file,
        )
        return None
    else:
        # Must only be called when we have a lock.
        return _unsafe_next_run(state)
    finally:
        state.lock.release()


def _unsafe_next_run(state):
    """Returns the next run for the queue.

    Note that this call is NOT safe across multiple queue
    instances. Use `safe_next_run` to ensure that multiple queues use
    proper locking.
    """
    blocking = _blocking_runs(state)
    staged = _staged_runs()
    _sync_state(blocking, staged, state)
    _log_state(state)
    for run in staged:
        if _can_start(run, blocking, state):
            # Setting run to PENDING takes it out of the running for
            # other queues to start.
            op_util.set_run_pending(run)
            return run
    return None


def _blocking_runs(state):
    if not state.wait_for_running:
        return []
    running = var.runs(filter=var.run_filter("attr", "status", "running"))
    return [run for run in running if not _is_queue_or_self(run, state)]


def _is_queue_or_self(run, state):
    return run.id == state.run_id or run.opref.to_opspec() == "queue:queue"


def _staged_runs():
    return var.runs(
        sort=["timestamp"], filter=var.run_filter("attr", "status", "staged")
    )


def _sync_state(blocking, staged, state):
    waiting_count0 = len(state.waiting)
    state.waiting.intersection_update(_run_ids(blocking))
    state.gpu_mismatch.intersection_update(_run_ids(staged))
    if waiting_count0 and not state.waiting:
        state.logged_waiting = False


def _run_ids(runs):
    return [run.id for run in runs]


def _log_state(state):
    if state.waiting:
        log.debug("waiting on: %s", state.waiting)
    if state.gpu_mismatch:
        log.debug("gpu mismatch: %s", state.gpu_mismatch)


def _can_start(run, blocking, state):
    return util.find_apply(
        [
            lambda: _check_gpu_mismatch(run, state),
            lambda: _check_blocking(run, blocking, state),
            lambda: True,
        ]
    )


def _check_gpu_mismatch(run, state):
    gpu_mismatch = _gpu_mismatch(run, state)
    if gpu_mismatch:
        _handle_gpu_mismatch(run, gpu_mismatch, state)
        return False
    return None


def _check_blocking(run, blocking, state):
    if blocking:
        _handle_blocking(run, blocking, state)
        return False
    return None


def _gpu_mismatch(run, state):
    if not state.gpus:
        return None
    run_gpus = _run_gpus(run)
    if run_gpus and run_gpus != state.gpus:
        return run_gpus
    return None


def _run_gpus(run):
    params = run.get("run_params") or {}
    return params.get("gpus")


def _handle_gpu_mismatch(run, run_gpus, state):
    if run.id not in state.gpu_mismatch:
        log.info(
            "Ignorning staged run %s (GPU spec mismatch: run is %s, queue is %s)"
            % (run.id, run_gpus, state.gpus)
        )
        state.gpu_mismatch.add(run.id)


def _handle_blocking(run, blocking, state):
    if run.id not in state.waiting:
        log.info(
            "Found staged run %s (waiting for runs to finish: %s)",
            run.short_id,
            _runs_desc(blocking),
        )
        state.logged_waiting = True
        state.waiting.add(run.id)


def _runs_desc(runs):
    return ", ".join([run.short_id for run in runs])


def _start_run(run, state):
    log.info("Starting staged run %s", run.id)
    try:
        _run(run, state)
    except gapi.RunError as e:
        log.error("%s failed with exit code %i", run.id, e.returncode)
    state.logged_waiting = False


def _run(run, state):
    env = _run_env(run)
    gapi.run(restart=run.id, extra_env=env, gpus=state.gpus)


def _run_env(run):
    return {
        "NO_RESTARTING_MSG": "1",
        "PYTHONPATH": run.guild_path("job-packages"),
    }


def _log_waiting(state):
    if not state.run_once:
        log.info("Waiting for staged runs")
    state.logged_waiting = True


if __name__ == "__main__":
    main()
