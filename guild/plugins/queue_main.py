# Copyright 2017-2023 Posit Software, PBC
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

import argparse
import logging

from guild import _api as gapi
from guild import util

from . import gen_queue

logging.basicConfig(
    level=util.get_env("LOG_LEVEL", int, logging.INFO),
    format="%(levelname)s: [%(name)s] %(asctime)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

log = logging.getLogger("guild")


class State(gen_queue.StateBase):
    def __init__(self, args):
        super().__init__(
            start_run_cb=_start_run,
            is_queue_cb=_is_queue,
            max_startable_runs=1,
            poll_interval=args.poll_interval,
            run_once=args.run_once,
            wait_for_running=args.wait_for_running,
            gpus=args.gpus,
        )


def main():
    args = _parse_args()
    state = State(args)
    gen_queue.simulate_batch()
    gen_queue.run(state)


def _parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--poll-interval", type=int, default=10)
    p.add_argument("--run-once", action="store_true")
    p.add_argument("--wait-for-running", action="store_true")
    p.add_argument("--gpus")
    return p.parse_args()


def _start_run(run, state):
    log.info("Starting staged run %s", run.id)
    try:
        gapi.run(restart=run.id, extra_env=_run_env(run), gpus=state.gpus)
    except gapi.RunError as e:
        raise RuntimeError(f"{run.id} failed with exit code {e.returncode}") from e


def _run_env(run):
    return {
        "NO_RESTARTING_MSG": "1",
        "PYTHONPATH": run.guild_path("job-packages"),
    }


def _is_queue(run):
    return run.opref.to_opspec() == "queue"


if __name__ == "__main__":
    main()
