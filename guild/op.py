import logging
import os
import shlex
import time
import uuid

import guild.run
import guild.util

class InvalidCmdSpec(ValueError):
    pass

class Operation(object):

    def __init__(self, cmd_args, cmd_env):
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
        self._started = time.time()
        self._init_run()
        #self._init_meta()
        #self._init_db()
        self._start_proc()
        #self._start_tasks()
        self._wait_for_proc()
        #self._finalize_meta()
        #self._stop_tasks()
        #self._finalize_db()
        return self._exit_status

    def _init_run(self):
        id = uuid.uuid1().get_hex()
        path = os.path.join(guild.var.runs_dir(), run_id)
        self._run = Run(id, path)
        self._run.init_skel()
        logging.debug("Initialized run in %s", path)

    def _start_proc(self):
        assert self._proc is None
        assert self._rundir is not None
        env = self.cmd_env
        args = _resolve_cmd_args(self.cmd_args, env)
        cwd = self._rundir.path
        logging.debug("Starting process %s" % (args,))
        self._proc = subprocess.Popen(args, env=env, cwd=cwd)
        _write_proc_lock(self._proc, self._rundir.path)

    def _wait_for_proc(self):
        assert self._proc is not None
        self._exit_status = self._proc.wait()
        _delete_proc_lock(self._rundir.path)

def _resolve_cmd_args(args, env):
    return [_resolve_arg_env_refs(arg, env) for arg in args]

def _resolve_arg_env_refs(arg, env):
    for name, val in env.items():
        arg = re.sub(r"\$" + name, val, arg)
    return arg

def _write_proc_lock(proc, rundir):
    with open(rundir.guild_path("LOCK"), "w") as f:
        f.write(str(proc.pid))

def _delete_proc_lock(rundir):
    try:
        os.remove(rundir.guild_path("LOCK"))
    except OSError:
        pass

def from_project_op(project_op):
    cmd_args = _python_cmd_for_project_op(project_op)
    cmd_env = {}
    return Operation(cmd_args, cmd_env)

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
