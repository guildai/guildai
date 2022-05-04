# Copyright 2017-2022 RStudio, PBC
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

import logging
import os
import signal
import time

from guild import lock as locklib
from guild import op_util
from guild import util
from guild import var

log = logging.getLogger("guild")

DEFAULT_POLL_INTERVAL = 10
DEFAULT_RUN_STATUS_LOCK_TIMEOUT = 30


class StateBase(object):
    def __init__(
        self,
        start_run_cb,
        is_queue_cb,
        name="queue",
        init_cb=None,
        can_start_cb=None,
        wait_for_running_cb=None,
        sync_state_cb=None,
        cleanup_cb=None,
        max_startable_runs=None,
        run_once=False,
        wait_for_running=False,
        gpus=None,
        poll_interval=DEFAULT_POLL_INTERVAL,
        run_status_lock_timeout=DEFAULT_RUN_STATUS_LOCK_TIMEOUT,
    ):
        self.start_run_cb = start_run_cb
        self.is_queue_cb = is_queue_cb
        self.name = name
        self.init_cb = init_cb
        self.can_start_cb = can_start_cb
        self.wait_for_running_cb = wait_for_running_cb
        self.sync_state_cb = sync_state_cb
        self.cleanup_cb = cleanup_cb
        self.max_startable_runs = max_startable_runs
        self.run_once = run_once
        self.wait_for_running = wait_for_running
        self.gpus = gpus
        self.poll_interval = poll_interval
        self.run_id = os.environ["RUN_ID"]
        self._logged_gpu_mismatch = set()
        self.waiting = set()
        self.logged_waiting = False
        self.run_status_lock = locklib.Lock(
            locklib.RUN_STATUS, timeout=run_status_lock_timeout
        )
        self.started = 0


def run(state):
    log.info("Starting %s", state.name)
    _init(state)
    _init_sigterm_handler()
    try:
        _run(state)
    finally:
        log.info("Stopping %s", state.name)
        _stop(state)


def _init(state):
    if state.init_cb:
        state.init_cb(state)


def _run(state):
    if state.run_once:
        _run_once(state)
    else:
        _poll(state)


def _init_sigterm_handler():
    def handler(_signum, _stack_frame):
        # Reset handler for SIGTERM to avoid reentry.
        signal.signal(signal.SIGTERM, signal.SIG_DFL)
        raise SystemExit()

    signal.signal(signal.SIGTERM, handler)


def _run_once(state):
    log.info("Processing staged runs")
    time0 = time.time()
    _run_staged(state)
    _wait_for_running(state)
    _log_runtime(time0, state)


def _poll(state):
    util.loop(lambda: _run_staged(state), time.sleep, state.poll_interval, 0)


def _run_staged(state):
    while True:
        runs = _safe_next_runs(state)
        if not runs:
            break
        _start_runs(runs, state)
    if not state.logged_waiting:
        _log_waiting(state)


def _safe_next_runs(state):
    """Uses a system wide lock to get the next runs."""
    try:
        state.run_status_lock.acquire()
    except locklib.Timeout as e:
        log.warning(
            "could not acquire lock for reading staged runs\n"
            "If this error persists, try stopping all queues and "
            "deleting %s",
            e.lock_file,
        )
        return []
    else:
        # Must only be called when we have a lock.
        return _unsafe_next_runs(state)
    finally:
        state.run_status_lock.release()


def _unsafe_next_runs(state):
    """Returns the next runs for the queue.

    Note that this call is NOT safe across multiple queue
    instances. Use `safe_next_run` to ensure that multiple queues use
    proper locking.
    """
    blocking = _blocking_runs(state)
    staged = _staged_runs()
    _sync_state_for_blocking(blocking, state)
    _sync_state_for_staged(staged, state)
    if state.sync_state_cb:
        state.sync_state_cb(state, blocking=blocking, staged=staged)
    startable_runs = [run for run in staged if _can_start(run, blocking, state)]
    next_runs = _limit_startable_runs(startable_runs, state)
    for run in next_runs:
        # Setting run to PENDING takes it out of the running for
        # other queues to start.
        op_util.set_run_pending(run)
    return next_runs


def _blocking_runs(state):
    if not state.wait_for_running:
        return []
    running = var.runs(filter=var.run_filter("attr", "status", "running"))
    return [run for run in running if not _is_queue_or_self(run, state)]


def _is_queue_or_self(run, state):
    return run.id == state.run_id or state.is_queue_cb(run)


def _staged_runs():
    return var.runs(
        sort=["timestamp"], filter=var.run_filter("attr", "status", "staged")
    )


def _sync_state_for_blocking(blocking, state):
    waiting_count_before_sync = len(state.waiting)
    state.waiting.intersection_update(_run_ids(blocking))
    if state.waiting:
        log.debug("waiting on: %s", state.waiting)
    if waiting_count_before_sync and not state.waiting:
        state.logged_waiting = False


def _sync_state_for_staged(staged, state):
    state._logged_gpu_mismatch.intersection_update(_run_ids(staged))
    if state._logged_gpu_mismatch:
        log.debug("gpu mismatch: %s", state._logged_gpu_mismatch)


def _run_ids(runs):
    return [run.id for run in runs]


def _can_start(run, blocking, state):
    return util.find_apply(
        [
            lambda: _check_gpu_mismatch(run, state),
            lambda: _check_blocking(run, blocking, state),
            lambda: _check_state_can_start(run, state),
            lambda: True,
        ]
    )


def _check_gpu_mismatch(run, state):
    gpu_mismatch = _gpu_mismatch(run, state)
    if gpu_mismatch:
        _handle_gpu_mismatch(run, gpu_mismatch, state)
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
    if run.id not in state._logged_gpu_mismatch:
        log.info(
            "Ignorning staged run %s (GPU spec mismatch: run is %s, queue is %s)",
            run.id,
            run_gpus,
            state.gpus,
        )
        state._logged_gpu_mismatch.add(run.id)


def _check_blocking(run, blocking, state):
    if blocking:
        _handle_blocking(run, blocking, state)
        return False
    return None


def _handle_blocking(run, blocking, state):
    if run.id not in state.waiting:
        log.info(
            "Found staged run %s (waiting for runs to finish: %s)",
            run.id,
            _runs_desc(blocking),
        )
        state.logged_waiting = True
        state.waiting.add(run.id)


def _runs_desc(runs):
    return ", ".join([run.id for run in runs])


def _check_state_can_start(run, state):
    if not state.can_start_cb:
        return None
    return state.can_start_cb(run, state)


def _limit_startable_runs(runs, state):
    return runs[0 : state.max_startable_runs]


def _start_runs(runs, state):
    for run in runs:
        try:
            state.start_run_cb(run, state)
        except Exception:
            log.exception("error calling %r for run %s", state.start_run_cb, run.id)
        else:
            state.started += 1
    state.logged_waiting = False


def _log_waiting(state):
    if not state.run_once:
        log.info("Waiting for staged runs")
    state.logged_waiting = True


def _wait_for_running(state):
    if state.wait_for_running_cb:
        try:
            state.wait_for_running_cb(state)
        except KeyboardInterrupt:
            pass
        except Exception:
            log.exception("error waiting for runs via %r", state.wait_for_running_cb)


def _log_runtime(time0, state):
    runtime = time.time() - time0
    log.info(
        "%s processed %i run(s) in %f seconds",
        state.name,
        state.started,
        runtime,
    )


def _stop(state):
    if state.cleanup_cb:
        state.cleanup_cb(state)


def simulate_batch():
    """Ensure that the current queue run looks like a batch run to Guild.

    Creates a proto dir to mimick the appearance of a batch. This
    ensures that the queue doesn't show up in compare and other
    facilities that ignore batch runs by default.
    """
    this_run = op_util.current_run()
    util.ensure_dir(this_run.guild_path("proto"))
