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
import subprocess
import sys
import time

from guild import config
from guild import exit_code
from guild import log as loglib
from guild import op_dep
from guild import op_util
from guild import run as runlib
from guild import util

log = logging.getLogger("guild")

OP_RUNFILE_PATHS = [
    ["guild"],
]

PROC_TERM_TIMEOUT_SECONDS = 30
LOG_WAITING_DELAY_SECONDS = 2

###################################################################
# Exception classes
###################################################################


class InvalidOpDef(ValueError):
    def __init__(self, opdef, msg):
        super().__init__(opdef, msg)
        self.opdef = opdef
        self.msg = msg

    def __str__(self):
        return self.msg


class ProcessError(Exception):
    pass


###################################################################
# State
###################################################################


class Operation:
    def __init__(self):
        self.opref = None
        self.cmd_args = []
        self.cmd_env = {}
        self.private_env = []
        self.sourcecode_paths = []
        self.run_dir = None
        self.run_attrs = {}
        self.deps = []
        self.callbacks = None


class OperationCallbacks:
    def __init__(
        self,
        init_output_summary=None,
        run_initialized=None,
        dep_source_resolved=None,
    ):
        self.init_output_summary = init_output_summary
        self.run_initialized = run_initialized
        self.dep_source_resolved = dep_source_resolved


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


def stage(op, continue_on_deps_error=False):
    run = init_run(op)
    try:
        _stage_run_proc_env(op, run)
        _resolve_deps(op, run, for_stage=True, continue_on_error=continue_on_deps_error)
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
            out.write(f"export {name}={util.env_var_quote(env[name])}\n")


###################################################################
# Run
###################################################################


def run(
    op,
    quiet=False,
    pidfile=None,
    stop_after=None,
    extra_env=None,
    continue_on_deps_error=False,
):
    run = init_run(op)
    op_util.clear_run_marker(run, "STAGED")
    try:
        _resolve_deps(op, run, continue_on_error=continue_on_deps_error)
    finally:
        op_util.clear_run_pending(run)
    op_util.set_run_started(run)
    if pidfile:
        _run_op_in_background(run, op, pidfile, quiet, stop_after, extra_env)
        return run, None
    exit_status = _run_op(run, op, quiet, stop_after, extra_env)
    return run, exit_status


def _run_op_in_background(run, op, pidfile, quiet, stop_after, extra_env):
    import daemonize

    action = lambda: _run_op(run, op, quiet, stop_after, extra_env)
    daemon = daemonize.Daemonize(
        app="guild_op", action=action, pid=pidfile, chdir=config.cwd()
    )
    # Need to log before starting daemon, otherwise output isn't
    # visible.
    if not quiet:
        log.info(
            "%s started in background as %s (pidfile %s)",
            run.opref.to_opspec(config.cwd()),
            run.id,
            pidfile,
        )
    try:
        daemon.start()
    except SystemExit:
        op_util.clear_run_pending(run)
        raise


def _run_op(run, op, quiet, stop_after, extra_env):
    proc = _op_start_proc(op, run, quiet, extra_env)
    exit_status = _op_wait_for_proc(op, proc, run, quiet, stop_after)
    _op_finalize_run_attrs(run, exit_status)
    return exit_status


def _op_start_proc(op, run, quiet, extra_env):
    env = _op_proc_env(op, run)
    if extra_env:
        env.update(extra_env)
    run.write_attr("env", _safe_env(env, op))
    log.debug("starting run %s in %s", run.id, run.dir)
    log.debug("operation command: %s", op.cmd_args)
    log.debug("operation env: %s", _hide_secret_env(env))
    stdout, stderr = _proc_streams(quiet)
    try:
        proc = subprocess.Popen(
            op.cmd_args,
            env=env,
            cwd=run.dir,
            stdout=stdout,
            stderr=stderr,
        )
    except OSError as e:
        raise ProcessError(e) from e
    else:
        op_util.write_proc_lock(proc.pid, run)
        return proc


def _safe_env(env, op):
    return _remove_secrets(_remove_private_env(env, op))


def _remove_private_env(env, op):
    return {name: env[name] for name in env if name not in op.private_env}


def _remove_secrets(env):
    def is_secret_env(name):
        is_secret = _is_secret_env(name)
        if is_secret:
            log.debug("found op env secret %r - will be removed", name)
        return is_secret

    return {name: env[name] for name in env if not is_secret_env(name)}


def _is_secret_env(name):
    """Returns True if name might be a secret.

    Uses a simple heuristic to test for a secret name.
    """
    name_lower = name.lower()
    secret_parts = ("password", "token", "secret")
    return any(part in name_lower for part in secret_parts)


def _hide_secret_env(env):
    return {name: _maybe_hide_secret(name, env) for name in env}


def _maybe_hide_secret(name, env):
    if _is_secret_env(name):
        return "***"
    return env[name]


def _proc_streams(quiet):
    """Returns a tuple of stdout, stderr streams for use in op subprocess."""
    if os.getenv("NO_RUN_OUTPUT") == "1":
        if quiet:
            return _devnull(), _devnull()
        return None, None
    if os.getenv("SYNC_RUN_OUTPUT") == "1":
        return subprocess.PIPE, subprocess.STDOUT
    return subprocess.PIPE, subprocess.PIPE


def _devnull():
    try:
        from subprocess import DEVNULL
    except ImportError:
        return open(os.devnull, 'wb')
    else:
        return DEVNULL


def _op_wait_for_proc(op, proc, run, quiet, stop_after):
    try:
        return _op_watch_proc(op, proc, run, quiet, stop_after)
    except KeyboardInterrupt:
        return _handle_proc_keyboard_interrupt(proc)


def _op_watch_proc(op, proc, run, quiet, stop_after):
    if os.getenv("NO_RUN_OUTPUT") != "1":
        output_summary = _output_summary_for_run(run, op)
        return _proc_wait_with_run_output(proc, run, quiet, output_summary, stop_after)
    return _proc_wait(proc, stop_after)


def _output_summary_for_run(run, op):
    if not op.callbacks or not op.callbacks.init_output_summary:
        return None
    return op.callbacks.init_output_summary(op, run)


def _proc_wait_with_run_output(proc, run, quiet, output_summary, stop_after):
    with _RunOutput(run, proc, quiet, output_summary):
        return _proc_wait(proc, stop_after)


class _RunOutput:
    def __init__(self, run, proc, quiet, output_summary):
        self._output = None
        self._run = run
        self._proc = proc
        self._quiet = quiet
        self._output_summary = output_summary

    def __enter__(self):
        self._output = op_util.RunOutput(self._run, self._quiet, self._output_summary)
        self._output.open(self._proc)

    def __exit__(self, *_exc):
        assert self._output
        self._output.wait_and_close()
        self._output = None


def _proc_wait(proc, stop_after):
    if stop_after is None:
        return proc.wait()
    return _proc_wait_minutes(proc, stop_after)


def _proc_wait_minutes(proc, minutes):
    poll_interval = util.get_env("STOP_AFTER_POLL_INTERVAL", float)
    kill_delay = util.get_env("STOP_AFTER_KILL_DELAY", float)
    return op_util.wait_for_proc(
        proc, minutes, poll_interval=poll_interval, kill_delay=kill_delay
    )


def _handle_proc_keyboard_interrupt(proc):
    log_waiting_after = time.time() + LOG_WAITING_DELAY_SECONDS
    kill_after = time.time() + PROC_TERM_TIMEOUT_SECONDS
    while time.time() < kill_after:
        if log_waiting_after and time.time() > log_waiting_after:
            if os.getenv("NO_OP_INTERRUPTED_MSG") != "1":
                log.info("Operation interrupted - waiting for process to exit")
            log_waiting_after = None
        if proc.poll() is not None:
            break
        time.sleep(1)
    if proc.poll() is None:
        log.warning("Operation process did not exit - stopping forcefully")
        util.kill_process_tree(proc.pid, force=True)
    return exit_code.KEYBOARD_INTERRUPT


def _op_exit_status(proc_exit_status, opdef):
    if (
        proc_exit_status in (exit_code.SIGTERM, exit_code.KEYBOARD_INTERRUPT)
        and opdef.stoppable
    ):
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
    op_util.delete_proc_lock(run)


# =================================================================
# Proc env
# =================================================================


def _op_proc_env(op, run):
    """Returns the proc env for op and associated run.

    Proc env is made up of system env, op env, and run env. System env
    is passed through unless otherwise defined by op env or run
    env. Run env takes precedence when it conflicts with op end.
    """
    env = {}
    env.update(_op_proc_system_env())
    env.update(_op_proc_op_env(op))
    env.update(_op_proc_run_env(run))
    return env


def _op_proc_system_env():
    return util.safe_osenv()


def _op_proc_op_env(op):
    env = {}
    env.update(op.cmd_env)
    if op.opref:
        env["GUILD_OP"] = op.opref.to_opspec()
    env["GUILD_HOME"] = config.guild_home()
    env["GUILD_SOURCECODE"] = _guild_sourcecode_env(op)
    env["LOG_LEVEL"] = _log_level()
    env["PYTHONPATH"] = _python_path(op)
    env["CMD_DIR"] = os.getcwd()
    return env


def _op_proc_run_env(run):
    return {
        "RUN_DIR": run.dir,
        "RUN_ID": run.id,
    }


def _guild_sourcecode_env(op):
    return os.path.pathsep.join(op.sourcecode_paths)


def _log_level():
    try:
        return os.environ["LOG_LEVEL"]
    except KeyError:
        return str(logging.getLogger().getEffectiveLevel())


def _python_path(op):
    paths = _op_pythonpath_env(op) + op.sourcecode_paths + _guild_paths() + _env_paths()
    return os.path.pathsep.join(paths)


def _op_pythonpath_env(op):
    env = op.cmd_env.get("PYTHONPATH")
    if not env:
        return []
    return env.split(os.path.pathsep)


def _guild_paths():
    guild_path = os.path.dirname(os.path.dirname(__file__))
    abs_guild_path = os.path.abspath(guild_path)
    return _runfile_paths() + [abs_guild_path]


def _runfile_paths():
    return [os.path.abspath(path) for path in sys.path if _is_runfile_pkg(path)]


def _is_runfile_pkg(path):
    for runfile_path in OP_RUNFILE_PATHS:
        split_path = path.split(os.path.sep)
        if split_path[-len(runfile_path) :] == runfile_path:
            return True
    return False


def _env_paths():
    env = os.getenv("PYTHONPATH")
    return env.split(os.path.pathsep) if env else []


# =================================================================
# Resolve deps
# =================================================================


def _resolve_deps(op, run, for_stage=False, continue_on_error=False):
    resolve_context = op_dep.ResolveContext(run)
    deps_attr = run.get("deps") or {}
    for dep in op.deps or []:
        resolved_sources = deps_attr.setdefault(dep.resdef.name, {})
        try:
            _apply_resolve_dep_sources(
                op,
                dep,
                resolve_context,
                run,
                for_stage,
                resolved_sources,
            )
        except op_dep.OpDependencyError as e:
            if not continue_on_error:
                raise
            log.warning("a dependency was not met: %s", e)
    run.write_attr("deps", deps_attr)


def _apply_resolve_dep_sources(op, dep, resolve_context, run, for_stage, resolved):
    log.info(loglib.dim("Resolving %s dependency"), dep.resdef.name)
    for source in dep.resdef.sources:
        if not source.always_resolve and source.name in resolved:
            log.info(
                "Skipping resolution of %s because it's already resolved", source.name
            )
            continue
        if for_stage and _is_operation_source(source):
            log.info("Skipping resolution of %s because it's being staged", source.name)
            continue
        run_rel_resolved_paths = _resolve_dep_source(
            op, source, dep, resolve_context, run
        )
        resolved[source.name] = source_info = {
            "uri": source.uri,
            "paths": run_rel_resolved_paths,
        }
        if dep.config:
            source_info["config"] = dep.config


def _resolve_dep_source(op, source, dep, resolve_context, run):
    resolved_abs_paths = op_dep.resolve_source(
        source,
        dep,
        resolve_context,
        resolve_cb=_resolve_source_cb(op),
    )
    return [os.path.relpath(path, run.dir) for path in resolved_abs_paths]


def _resolve_source_cb(op):
    def f(resolved_source):
        _callback("dep_source_resolved", op, resolved_source)

    return f


def _is_operation_source(source):
    return source.uri.startswith("operation:")
