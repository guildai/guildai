# Copyright 2017-2021 TensorHub, Inc.
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
from guild import util

from . import gen_queue

logging.basicConfig(
    level=int(os.getenv("LOG_LEVEL", logging.INFO)),
    format="%(levelname)s: [%(name)s] %(asctime)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

RUN_STATUS_LOCK_TIMEOUT = 30
WAIT_FOR_RUNNING_DELAY = 5.0

log = logging.getLogger("guild")


class State(gen_queue.StateBase):
    def __init__(self, args):
        super(State, self).__init__(
            _start_run,
            _is_queue,
            name="Dask scheduler",
            init_cb=_init_client,
            wait_for_running_cb=_wait_for_running,
            cleanup_cb=_cleanup,
            max_startable_runs=1,
            poll_interval=args.poll_interval,
            run_once=args.run_once,
            wait_for_running=args.wait_for_running,
        )
        self.args = args
        self.client = None  # Initialized in _init_client
        self.futures = []


def main():
    args = _parse_args()
    state = State(args)
    gen_queue.run(state)


def _parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--workers", type=int)
    p.add_argument("--loglevel")
    p.add_argument("--dashboard-address")
    p.add_argument("--poll-interval", type=int, default=10)
    p.add_argument("--run-once", action="store_true")
    p.add_argument("--wait-for-running", action="store_true")
    return p.parse_args()


def _init_client(state):
    client, dashboard_disabled = _init_dask_client(state.args)
    state.client = client
    state.dashboard_disabled = dashboard_disabled
    _log_state_info(state)


def _init_dask_client(args):
    _workaround_multiprocessing_cycle()
    try:
        from dask.distributed import Client, LocalCluster
    except ImportError:
        raise SystemExit(
            "dask.distributed not available - "
            "install it first using 'pip install dask[distributed]'"
        )
    else:
        dashboard_address = _dashboard_address(args)
        log.info("Initializing cluster%s", _workers_log_entry_suffix(args))
        cluster = LocalCluster(
            n_workers=args.workers,
            processes=False,
            silence_logs=_dask_loglevel(args),
            dashboard_address=dashboard_address,
        )
        dashboard_disabled = dashboard_address is None
        client = Client(cluster)
        return client, dashboard_disabled


def _workaround_multiprocessing_cycle():
    # See https://github.com/dask/distributed/issues/4168#issuecomment-722049470
    try:
        import multiprocessing.popen_spawn_posix as _
    except ImportError:
        pass


def _dask_loglevel(args):
    return args.loglevel.upper()


def _dashboard_address(args):
    address = util.find_apply(
        [
            _false_flag_for_arg,
            _port_int,
            lambda s: s,
        ],
        args.dashboard_address,
    )
    return _dashboard_address_for_typed_val(address)


def _false_flag_for_arg(s):
    """Returns False IIF s is an empty string otherwise returns None.

    Use to test if an arg is a False flag. Guild passes False values
    as empty strings assuming that argparse `type=boolean` is used to
    convert values to booleans.
    """
    if s == "":
        return False
    return None


def _port_int(s):
    """Returns s as an int if possible otherwise returns None."""
    try:
        return int(s)
    except ValueError:
        return None


def _dashboard_address_for_typed_val(val):
    if val is False:
        return None
    elif isinstance(val, int):
        return ":%s" % val
    else:
        return val


def _workers_log_entry_suffix(args):
    if args.workers is None:
        return ""
    elif args.workers == 1:
        return " with 1 worker"
    else:
        return " with %i workers" % args.workers


def _log_state_info(state):
    cluster = state.client.cluster
    link = cluster.dashboard_link if not state.dashboard_disabled else "<disabled>"
    log.info("Dashboard link: %s", link)


def _start_run(run, state):
    _release_futures(state)
    _start_run_(run, state)


def _release_futures(state):
    active_futures = []
    for f in state.futures:
        if f.done():
            log.debug("Releasing future %s", f.key)
            f.release()
        else:
            active_futures.append(f)
    state.futures = active_futures


def _start_run_(run, state):
    log.info("Starting staged run %s", run.id)
    env = _run_env(run)
    f = state.client.submit(
        gapi.run,
        key="run-%s" % run.id,
        restart=run.id,
        extra_env=env,
        gpus=state.gpus,
    )
    state.futures.append(f)


def _run_env(run):
    return {
        "NO_RESTARTING_MSG": "1",
        "PYTHONPATH": run.guild_path("job-packages"),
    }


def _wait_for_running(state):
    while True:
        _release_futures(state)
        log.debug("wait_for_running futures: %i", len(state.futures))
        if not state.futures:
            break
        time.sleep(WAIT_FOR_RUNNING_DELAY)


def _is_queue(run):
    return run.opref.to_opspec() == "dask:scheduler"


def _cleanup(state):
    log.info("Stopping Dask cluster")
    state.client.close()
    state.client.cluster.close()


if __name__ == "__main__":
    main()
