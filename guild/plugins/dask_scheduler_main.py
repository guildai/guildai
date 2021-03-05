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

    client = None
    dashboard_disabled = False
    resources = None

    def __init__(self, args):
        super(State, self).__init__(
            _start_run,
            _is_queue,
            name="Dask scheduler",
            init_cb=_init_client,
            can_start_cb=_can_start_run,
            wait_for_running_cb=_wait_for_running,
            sync_state_cb=_sync_state_for_staged,
            cleanup_cb=_cleanup,
            max_startable_runs=1,
            poll_interval=args.poll_interval,
            run_once=args.run_once,
            wait_for_running=args.wait_for_running,
            gpus=args.gpus,
        )
        self.args = args
        self.futures = []
        self._logged_missing_resoures = set()


def main():
    args = _parse_args()
    state = State(args)
    gen_queue.simulate_batch()
    gen_queue.run(state)


def _parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--workers", type=int)
    p.add_argument("--loglevel")
    p.add_argument("--dashboard-address")
    p.add_argument("--poll-interval", type=int, default=10)
    p.add_argument("--run-once", action="store_true")
    p.add_argument("--wait-for-running", action="store_true")
    p.add_argument("--gpus")
    p.add_argument("--resources")
    return p.parse_args()


def _init_client(state):
    client, dashboard_disabled, resources = _init_dask_client(state.args)
    state.client = client
    state.dashboard_disabled = dashboard_disabled
    state.resources = resources
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
        resources = _cluster_resources(args)
        log.info("Initializing Dask cluster%s", _workers_log_entry_suffix(args))
        cluster = LocalCluster(
            n_workers=1,
            threads_per_worker=args.workers,
            processes=False,
            silence_logs=_dask_loglevel(args),
            dashboard_address=dashboard_address,
            resources=resources,
        )
        dashboard_disabled = dashboard_address is None
        client = Client(cluster)
        return client, dashboard_disabled, resources


def _workaround_multiprocessing_cycle():
    # See https://github.com/dask/distributed/issues/4168#issuecomment-722049470
    try:
        if util.get_platform() == "Windows":
            import multiprocessing.popen_spawn_win32 as _
        else:
            import multiprocessing.popen_spawn_posix as _
    except ImportError:
        pass


def _dask_loglevel(args):
    if log.getEffectiveLevel() <= logging.DEBUG:
        return "DEBUG"
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


def _cluster_resources(args):
    if not args.resources:
        return None
    return _decode_dask_resources(args.resources)


def _log_state_info(state):
    cluster = state.client.cluster
    link = (
        _cluster_dashboard_link(cluster)
        if not state.dashboard_disabled
        else "<disabled>"
    )
    log.info("Dashboard link: %s", link)
    if state.resources:
        log.info("Cluster resources: %s", _resources_desc(state.resources))


def _cluster_dashboard_link(cluster):
    try:
        link = cluster.dashboard_link
    except KeyError as e:
        if e.args and e.args[0] != "bokeh":
            raise
        return "<disabled> (Bokeh not installed)"
    else:
        return link or "<disabled>"


def _start_run(run, state):
    _release_futures(state)
    _start_run_(run, state)


def _release_futures(state):
    active_futures = []
    for f in state.futures:
        if f.done():
            _maybe_log_future_error(f)
            log.debug("Releasing future %s", f.key)
            f.release()
        else:
            active_futures.append(f)
    state.futures = active_futures


def _maybe_log_future_error(f):
    exc = f.exception()
    if exc:
        log.error("exception detail for %s:\n%s", f.key, _format_exc(exc))


def _format_exc(exc):
    import traceback

    return "".join(traceback.format_tb(exc.__traceback__))


def _start_run_(run, state):
    resources = _run_resources(run, quiet=True)
    _log_scheduling(run, resources)
    run_kwargs = dict(
        restart=run.id,
        extra_env=_run_env(run),
        gpus=state.gpus,
    )
    future = state.client.submit(
        _run,
        run=run,
        run_kwargs=run_kwargs,
        key=_run_key(run),
        resources=resources,
    )
    state.futures.append(future)


def _run_resources(run, quiet=False):
    tags = run.get("tags") or []
    resources = {}
    for tag in tags:
        if tag.startswith("dask:"):
            encoded = tag[5:]
            resources.update(_decode_dask_resources(encoded, quiet))
    return resources


def _decode_dask_resources(encoded, quiet=False):
    from guild import op_util

    args = util.shlex_split(encoded)
    try:
        return op_util.parse_flag_assigns(args)
    except op_util.ArgValueError:
        if not quiet:
            log.warning(
                "Ignoring invalid dask resources spec %r: parts must be in "
                "format KEY=VAL",
                encoded,
            )
        return {}


def _log_scheduling(run, resources):
    if resources:
        log.info(
            "Scheduling run %s (requires %s)",
            run.id,
            _resources_desc(resources),
        )
    else:
        log.info("Scheduling run %s", run.id)


def _resources_desc(resources):
    from guild import flag_util

    return " ".join(flag_util.flag_assigns(resources))


def _run_env(run):
    return {
        "NO_RESTARTING_MSG": "1",
        "PYTHONPATH": run.guild_path("job-packages"),
    }


def _run_key(run):
    return "run-%s" % run.id


def _run_id_for_key(key):
    assert key.startwith("run-") and len(key) == 36, key
    return key[4:]


def _run(run, run_kwargs):
    log.info("Run %s started", run.id)
    try:
        gapi.run(**run_kwargs)
    except gapi.RunError as e:
        log.error("Run %s exited with code %i", run.id, e.returncode)
    else:
        log.info("Run %s completed", run.id)


def _can_start_run(run, state):
    run_resources = _run_resources(run) or {}
    if not run_resources:
        return True
    return _check_run_resources(run_resources, run, state)


def _check_run_resources(run_resources, run, state):
    cluster_resources = state.resources or {}
    missing_resources = [
        name for name in run_resources if name not in cluster_resources
    ]
    if missing_resources:
        _handle_missing_resources(missing_resources, run, state)
        return False
    return True


def _handle_missing_resources(missing_resources, run, state):
    if run.id not in state._logged_missing_resoures:
        log.info(
            "Ignorning staged run %s (requires resources not defined for cluster: %s)",
            run.id,
            ", ".join(sorted(missing_resources)),
        )
        state._logged_missing_resoures.add(run.id)


def _wait_for_running(state):
    while True:
        _release_futures(state)
        log.debug("wait_for_running futures: %i", len(state.futures))
        if not state.futures:
            break
        time.sleep(WAIT_FOR_RUNNING_DELAY)


def _is_queue(run):
    return run.opref.to_opspec() == "dask:scheduler"


def _sync_state_for_staged(state, staged, **_kw):
    staged_run_ids = [run.id for run in (staged or [])]
    state._logged_missing_resoures.intersection_update(staged_run_ids)
    if state._logged_missing_resoures:
        log.debug("missing resource runs: %s", state._logged_missing_resoures)


def _cleanup(state):
    log.info("Stopping Dask cluster")
    state.client.close()
    state.client.cluster.close()


if __name__ == "__main__":
    main()
