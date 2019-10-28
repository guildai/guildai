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
import os
import subprocess
import sys
import time

from guild import config
from guild import exit_code
from guild import op_dep
from guild import op_util2 as op_util
from guild import run as runlib
from guild import util

log = logging.getLogger("guild")

OP_RUNFILE_PATHS = [
    ["org_click"],
    ["org_psutil"],
    ["guild", "external"],
]

PROC_TERM_TIMEOUT_SECONDS = 30

###################################################################
# Exception classes
###################################################################

class InvalidOpDef(ValueError):

    def __init__(self, opdef, msg):
        super(InvalidOpDef, self).__init__(opdef, msg)
        self.opdef = opdef
        self.msg = msg

    def __str__(self):
        return self.msg

class OpInitError(Exception):
    pass

class ProcessError(Exception):
    pass

###################################################################
# State
###################################################################

class Operation(object):

    def __init__(self):
        self.opref = None
        self.cmd_args = []
        self.cmd_env = {}
        self.run_dir = None
        self.run_attrs = {}
        self.deps = []
        self.callbacks = None

class OperationCallbacks(object):

    def __init__(self, init_output_summary=None, run_initialized=None):
        self.init_output_summary = init_output_summary
        self.run_initialized = run_initialized

def _callback(name, op, *rest_args):
    if op.callbacks:
        cb = getattr(op.callbacks, name, None)
        if cb:
            cb(op, *rest_args)

###################################################################
# Init run
###################################################################

def init_run(op, run_dir=None):
    run = _op_init_pending_run(op, run_dir)
    _op_init_run_attrs(op, run)
    _callback("run_initialized", op, run)
    return run

def _op_init_pending_run(op, run_dir):
    run_dir = run_dir or op.run_dir
    run = op_util.init_run(run_dir)
    log.debug("initializing run in %s", run.dir)
    run.init_skel()
    op_util.set_run_pending(run)
    return run

def _op_init_run_attrs(op, run):
    run.write_opref(op.opref)
    run.write_attr("cmd", op.cmd_args)
    for name, val in (op.run_attrs or {}).items():
        run.write_attr(name, val)

###################################################################
# Stage
###################################################################

def stage(op):
    run = init_run(op)
    _stage_run_proc_env(op, run)
    try:
        _resolve_deps(op, run, for_stage=True)
        op_util.set_run_staged(run)
    finally:
        op_util.clear_run_pending(run)
    return run

def _stage_run_proc_env(op, run):
    env = _op_proc_env(op, run)
    skip_env = ("PWD", "_")
    with open(run.guild_path("ENV"), "w") as out:
        for name in sorted(env):
            if name in skip_env:
                continue
            out.write(
                "export %s=%s\n"
                % (name, util.env_var_quote(env[name])))

###################################################################
# Run
###################################################################

def run(op, quiet=False, stop_after=None, extra_env=None):
    run = init_run(op)
    try:
        _resolve_deps(op, run)
        op_util.set_run_started(run)
        proc = _op_start_proc(op, run, extra_env)
        exit_status = _op_wait_for_proc(op, proc, run, quiet, stop_after)
        _op_finalize_run_attrs(run, exit_status)
        return run, exit_status
    finally:
        op_util.clear_run_marker(run, "STAGED")
        op_util.clear_run_pending(run)

def _op_start_proc(op, run, extra_env=None):
    env = _op_proc_env(op, run)
    if extra_env:
        env.update(extra_env)
    run.write_attr("env", env)
    log.debug("starting run %s in %s", run.id, run.dir)
    log.debug("operation command: %s", op.cmd_args)
    log.debug("operation env: %s", env)
    try:
        proc = subprocess.Popen(
            op.cmd_args,
            env=env,
            cwd=run.dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
    except OSError as e:
        raise ProcessError(e)
    else:
        _write_proc_lock(proc, run)
        return proc

def _write_proc_lock(proc, run):
    with open(run.guild_path("LOCK"), "w") as f:
        f.write(str(proc.pid))

def _op_wait_for_proc(op, proc, run, quiet, stop_after):
    try:
        return _op_watch_proc(op, proc, run, quiet, stop_after)
    except KeyboardInterrupt:
        return _handle_proc_interrupt(proc)

def _op_watch_proc(op, proc, run, quiet, stop_after):
    output_summary = _output_summary_for_run(run, op)
    with _RunOutput(run, proc, quiet, output_summary):
        return _proc_wait(proc, stop_after)

def _output_summary_for_run(run, op):
    if not op.callbacks or not op.callbacks.init_output_summary:
        return None
    return op.callbacks.init_output_summary(op, run)

class _RunOutput(object):

    def __init__(self, run, *args):
        self._output = None
        self._run = run
        self._test_init_args = args

    def __enter__(self):
        if os.getenv("NO_RUN_OUTPUT_CAPTURE") != "1":
            self._output = op_util.RunOutput(self._run, *self._rest_init_args)

    def __exit__(self, *_exc):
        if self._output:
            self._output.wait_and_close()
        self._output = None

def _proc_wait(proc, stop_after):
    if stop_after is None:
        return proc.wait()
    else:
        return op_util.wait_for_proc(proc, stop_after)

def _handle_proc_interrupt(proc):
    log.info("Operation interrupted - waiting for process to exit")
    kill_after = time.time() + PROC_TERM_TIMEOUT_SECONDS
    while time.time() < kill_after:
        if proc.poll() is not None:
            break
        time.sleep(1)
    if proc.poll() is None:
        log.warning("Operation process did not exit - stopping forcefully")
        util.kill_process_tree(proc.pid, force=True)
    return exit_code.SIGTERM

def _op_exit_status(proc_exit_status, opdef):
    if proc_exit_status == exit_code.SIGTERM and opdef.stoppable:
        return 0
    return proc_exit_status

def _op_finalize_run_attrs(run, exit_status):
    if not os.path.exists(run.dir):
        log.warning("run directory has been deleted, unable to finalize")
        return
    if not os.path.exists(run.guild_path()):
        log.warning("run Guild directory has been deleted, unable to finalize")
        return
    stopped = runlib.timestamp()
    run.write_attr("exit_status", exit_status)
    run.write_attr("stopped", stopped)
    _delete_proc_lock(run)

def _delete_proc_lock(run):
    try:
        os.remove(run.guild_path("LOCK"))
    except OSError:
        pass

# =================================================================
# Proc env
# =================================================================

def _op_proc_env(op, run):
    env = dict(op.cmd_env)
    env.update(_system_cmd_env())
    env.update(_run_cmd_env(run))
    return env

def _system_cmd_env():
    env = util.safe_osenv()
    env["GUILD_HOME"] = config.guild_home()
    env["LOG_LEVEL"] = _log_level()
    env["PYTHONPATH"] = _python_path()
    env["CMD_DIR"] = os.getcwd()
    return env

def _run_cmd_env(run):
    return {
        "RUN_DIR": run.dir,
        "RUN_ID": run.id,
    }

def _log_level():
    try:
        return os.environ["LOG_LEVEL"]
    except KeyError:
        return str(logging.getLogger().getEffectiveLevel())

def _python_path():
    paths = (
        _env_paths() +
        _run_sourcecode_paths() +
        _guild_paths()
    )
    return os.path.pathsep.join(paths)

def _env_paths():
    env = os.getenv("PYTHONPATH")
    return env.split(os.path.pathsep) if env else []

def _run_sourcecode_paths():
    return [".guild/sourcecode"]

def _guild_paths():
    guild_path = os.path.dirname(os.path.dirname(__file__))
    abs_guild_path = os.path.abspath(guild_path)
    return [abs_guild_path] + _runfile_paths()

def _runfile_paths():
    return [
        os.path.abspath(path)
        for path in sys.path if _is_runfile_pkg(path)
    ]

def _is_runfile_pkg(path):
    for runfile_path in OP_RUNFILE_PATHS:
        split_path = path.split(os.path.sep)
        if split_path[-len(runfile_path):] == runfile_path:
            return True
    return False

# =================================================================
# Resolve deps
# =================================================================

def _resolve_deps(op, run, for_stage=False):
    resolved = run.get("resolved_deps") or {}
    for dep in op.deps or []:
        log.info("Resolving %s dependency", dep.resdef.name)
        resolved_sources = resolved.setdefault(dep.resdef.name, {})
        for source in dep.resdef.sources:
            if source.name in resolved_sources:
                log.info(
                    "Skipping %s because it's already resolved",
                    source.name)
                continue
            if for_stage and _is_operation_source(source):
                log.info(
                    "Skipping operation dependency %s for stage",
                    source.name)
                continue
            paths = op_dep.resolve_source(source, dep, run.dir)
            rel_paths = [os.path.relpath(path, run.dir) for path in paths]
            resolved_sources[source.name] = rel_paths
    run.write_attr("resolved_deps", resolved)

def _is_operation_source(source):
    return source.uri.startswith("operation:")
