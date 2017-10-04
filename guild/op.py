import logging
import os
import re
import shlex
import subprocess
import time
import uuid

import guild.run
import guild.util
import guild.var

OS_ENVIRON_WHITELIST = [
    "LD_LIBRARY_PATH",
]

class InvalidCmdSpec(ValueError):
    pass

class Operation(object):

    def __init__(self, name, cmd_args, cmd_env):
        self.name = name
        self.cmd_args = cmd_args
        self.cmd_env = cmd_env
        self._running = False
        self._run = None
        self._proc = None
        self._exit_status = None

    def run(self):
        if self._running:
            raise AssertionError("op already running")
        self._running = True
        self._started = int(time.time())
        self._init_run()
        self._init_attrs()
        self._start_proc()
        self._wait_for_proc()
        self._finalize_attrs()
        return self._exit_status

    def _init_run(self):
        id = unique_run_id()
        path = os.path.join(guild.var.runs_dir(), id)
        self._run = guild.run.Run(id, path)
        logging.info("Initializing run in %s", path)
        self._run.init_skel()

    def _init_attrs(self):
        assert self._run is not None
        self._run.write_attr("cmd", self.cmd_args)
        self._run.write_attr("env", self.cmd_env)
        self._run.write_attr("started", self._started)
        self._run.write_attr("op", self.name)

    def _start_proc(self):
        assert self._proc is None
        assert self._run is not None
        args = self._proc_args()
        env = self._proc_env()
        cwd = self._run.path
        logging.info("Starting process %s" % (args,))
        self._proc = subprocess.Popen(args, env=env, cwd=cwd)
        _write_proc_lock(self._proc, self._run)

    def _proc_args(self):
        assert self._run
        return self.cmd_args + ["--rundir", self._run.path]

    def _proc_env(self):
        assert self._run
        env = {}
        env.update(self.cmd_env)
        env.update(_op_os_env())
        env["RUNDIR"] = self._run.path
        return env

    def _wait_for_proc(self):
        assert self._proc is not None
        self._exit_status = self._proc.wait()
        self._stopped = int(time.time())
        _delete_proc_lock(self._run)

    def _finalize_attrs(self):
        assert self._run is not None
        assert self._exit_status is not None
        assert self._stopped is not None
        self._run.write_attr("exit_status", self._exit_status)
        self._run.write_attr("stopped", self._stopped)

def unique_run_id():
    return uuid.uuid1().get_hex()

def _op_os_env():
    return {
        name: val
        for name, val in os.environ.items()
        if name in OS_ENVIRON_WHITELIST
    }

def _write_proc_lock(proc, run):
    with open(run.guild_path("LOCK"), "w") as f:
        f.write(str(proc.pid))

def _delete_proc_lock(run):
    try:
        os.remove(run.guild_path("LOCK"))
    except OSError:
        pass

def from_project_op(project_op):
    cmd_args = _python_cmd_for_project_op(project_op)
    cmd_env = _op_cmd_env()
    return Operation(
        project_op.full_name,
        cmd_args,
        cmd_env)

def _python_cmd_for_project_op(project_op):
    spec = project_op.cmd
    spec_parts = shlex.split(spec)
    if len(spec_parts) < 1:
        raise InvalidCmdSpec(spec)
    script = _resolve_script_path(spec_parts[0], project_op.project.src)
    flags = flag_args(all_op_flags(project_op))
    return ["python", "-u", script] + spec_parts[1:] + flags

def _resolve_script_path(script, project_src):
    script_path = _script_path_for_project_src(script, project_src)
    return guild.util.find_apply(
        [_explicit_path,
         _path_missing_py_ext,
         _unmodified_path],
        script_path)

def _script_path_for_project_src(script, project_src):
    project_dir = os.path.dirname(project_src)
    return os.path.join(project_dir, script)

def _explicit_path(path):
    return path if os.path.isfile(path) else None

def _path_missing_py_ext(part_path):
    return _explicit_path(part_path + ".py")

def _unmodified_path(val):
    return val

def all_op_flags(op):
    flags = {}
    _apply_flags(op.model.flags, flags)
    _apply_flags(op.flags, flags)
    return flags

def _apply_flags(project_flags, flags):
    for name, val in project_flags.items():
        if isinstance(val, dict):
            val = val.get("value", None)
        flags[name] = val

def flag_args(flags):
    return [
        arg for args in
        [_opt_args(name, val) for name, val in _sorted_flags(flags)]
        for arg in args
    ]

def _sorted_flags(flags):
    flags = flags or {}
    return [(key, flags[key]) for key in sorted(flags)]

def _opt_args(name, val):
    opt = "--%s" % name
    return [opt] if val is None else [opt, str(val)]

def _op_cmd_env():
    # TODO or delete
    return {}
