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

from guild import _api as gapi

from . import gen_queue

logging.basicConfig(
    level=int(os.getenv("LOG_LEVEL", logging.INFO)),
    format="%(levelname)s: [%(name)s] %(asctime)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

RUN_STATUS_LOCK_TIMEOUT = 30

log = logging.getLogger("guild")


class State(gen_queue.StateBase):
    def __init__(self, client, args):
        super(State, self).__init__(
            name="Dask scheduler",
            start_run_cb=_start_run,
            cleanup_cb=_cleanup,
            max_startable_runs=1,
            poll_interval=args.poll_interval,
            run_once=args.run_once,
            wait_for_running=args.wait_for_running,
        )
        self.client = client
        self.futures = []


def main():
    args = _parse_args()
    state = _init_state(args)
    gen_queue.run(state)


def _parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--poll-interval", type=int, default=10)
    p.add_argument("--run-once", action="store_true")
    p.add_argument("--wait-for-running", action="store_true")
    return p.parse_args()


def _init_state(args):
    log.info("Initializing Dask cluster")
    client = _init_dask_client(args)
    return State(client, args)


def _init_dask_client(_args):
    try:
        from dask.distributed import Client, LocalCluster
    except ImportError:
        raise SystemExit(
            "dask.distributed not available - "
            "install it first using 'pip install dask.distributed'"
        )
    else:
        cluster = LocalCluster()
        client = Client(cluster)
        return client


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


def _cleanup(state):
    log.info("Stopping Dask cluster")
    # TODO: send TERM signals to running runs via futures
    _release_futures(state)
    for f in state.futures:
        print("TODO: send TERM signal to %s" % f)
    state.client.cluster.close()
    state.client.close()


if __name__ == "__main__":
    main()
