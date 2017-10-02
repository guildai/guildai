import logging
import os
import shlex
import subprocess
import time
import uuid

import guild.run
import guild.util
import guild.var

class InvalidCmdSpec(ValueError):
    pass

class Operation(object):

    def __init__(self, cmd_args, cmd_env, project_op):
        self._cmd_args = cmd_args
        self._cmd_env = cmd_env
        self._project_op = project_op
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
        id = uuid.uuid1().get_hex()
        path = os.path.join(guild.var.runs_dir(), id)
        self._run = guild.run.Run(id, path)
        self._run.init_skel()
        logging.debug("Initialized run in %s", path)

    def _init_attrs(self):
        assert self._run is not None
        self._run.write_attr("cmd", self._cmd_args)
        self._run.write_attr("env", self._cmd_env)
        self._run.write_attr("started", self._started)
        self._run.write_attr("op", self._project_op.full_name)

    def _start_proc(self):
        assert self._proc is None
        assert self._run is not None
        env = self._cmd_env
        args = _resolve_cmd_args(self._cmd_args, env)
        cwd = self._run.path
        logging.debug("Starting process %s" % (args,))
        self._proc = subprocess.Popen(args, env=env, cwd=cwd)
        _write_proc_lock(self._proc, self._run)

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
        
def _resolve_cmd_args(args, env):
    return [_resolve_arg_env_refs(arg, env) for arg in args]

def _resolve_arg_env_refs(arg, env):
    for name, val in env.items():
        arg = re.sub(r"\$" + name, val, arg)
    return arg

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
    cmd_env = {}
    return Operation(cmd_args, cmd_env, project_op)

def _python_cmd_for_project_op(project_op):
    spec = project_op.cmd
    spec_parts = shlex.split(spec)
    if len(spec_parts) < 1:
        raise InvalidCmdSpec(spec)
    script = _resolve_script_path(spec_parts[0], project_op.project.src)
    return ["python", "-u", script] + spec_parts[1:]

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
