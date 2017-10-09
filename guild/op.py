import logging
import os
import re
import shlex
import subprocess
import sys
import time
import uuid

import guild.run
import guild.util
import guild.var

OS_ENVIRON_WHITELIST = [
    "LD_LIBRARY_PATH",
]

GUILD_PACKAGES = [
    "org_guildai_guild",
    "org_psutil",
]

class InvalidCmd(ValueError):
    pass

class Operation(object):

    def __init__(self, name, cmd_args, cmd_env, attrs={}):
        self.name = name
        self.cmd_args = cmd_args
        self.cmd_env = cmd_env
        self.attrs = attrs
        self._running = False
        self._run = None
        self._proc = None
        self._exit_status = None

    def run(self):
        assert not self._running
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
        logging.debug("Initializing run in %s", path)
        self._run.init_skel()

    def _init_attrs(self):
        assert self._run is not None
        for name, val in self.attrs.items():
            self._run.write_attr(name, val)
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
        logging.debug("Starting process %s" % (args,))
        self._proc = subprocess.Popen(args, env=env, cwd=cwd)
        _write_proc_lock(self._proc, self._run)

    def _proc_args(self):
        assert self._run
        return self.cmd_args + ["--rundir", self._run.path]

    def _proc_env(self):
        assert self._run
        env = {}
        env.update(self.cmd_env)
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

def _write_proc_lock(proc, run):
    with open(run.guild_path("LOCK"), "w") as f:
        f.write(str(proc.pid))

def _delete_proc_lock(run):
    try:
        os.remove(run.guild_path("LOCK"))
    except OSError:
        pass

def from_project_op(project_op):
    flags = _op_flags(project_op)
    cmd_args = _op_cmd_args(project_op, flags)
    cmd_env = _op_cmd_env(project_op)
    attrs = {
        "flags": flags
    }
    return Operation(
        project_op.full_name,
        cmd_args,
        cmd_env,
        attrs)

def _op_flags(op):
    flags = {}
    _acc_flags(op.model.flags, flags)
    _acc_flags(op.flags, flags)
    return flags

def _acc_flags(project_flags, flags):
    for name, val in project_flags.items():
        if isinstance(val, dict):
            val = val.get("value", None)
        flags[name] = val

def _op_cmd_args(project_op, flags):
    python_args = [_python_cmd(project_op), "-um", "guild.op_main"]
    cmd_args = _cmd_args(project_op)
    if not cmd_args:
        raise InvalidCmd(project_op.cmd)
    flag_args = _flag_args(flags)
    return python_args + cmd_args + flag_args

def _python_cmd(_project_op):
    # TODO: This is an important operation that should be controlled
    # by the model (e.g. does it run under Python 2 or 3, etc.) and
    # not by whatever Python runtime is configured in the user env.
    return "python"

def _cmd_args(project_op):
    cmd = project_op.cmd
    if isinstance(cmd, str):
        return shlex.split(cmd)
    elif isinstance(cmd, list):
        return cmd
    else:
        raise AssertionError(cmd)

def _flag_args(flags):
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

def _op_cmd_env(project_op):
    env = {}
    env.update(_op_os_env())
    env["GUILD_PLUGINS"] = _op_plugins(project_op)
    env["LOG_LEVEL"] = str(logging.getLogger().getEffectiveLevel())
    env["PYTHONPATH"] = _python_path(project_op)
    return env

def _op_os_env():
    return {
        name: val
        for name, val in os.environ.items()
        if name in OS_ENVIRON_WHITELIST
    }

def _op_plugins(project_op):
    op_plugins = []
    for name, plugin in guild.plugin.iter_plugins():
        if _plugin_disabled(name, project_op):
            logging.debug("plugin '%s' disabled for operation", name)
            continue
        if plugin.enabled_for_op(project_op):
            logging.debug("plugin '%s' enabled for operation", name)
            op_plugins.append(name)
    return ",".join(op_plugins)

def _plugin_disabled(name, project_op):
    return (name in project_op.disabled_plugins
            or name in project_op.model.disabled_plugins)

def _python_path(project_op):
    paths = _model_paths(project_op) + _guild_paths()
    return os.path.pathsep.join(paths)

def _model_paths(project_op):
    return [os.path.dirname(project_op.project.src)]

def _guild_paths():
    return [path for path in sys.path if _is_guild_path(path)]

def _is_guild_path(path):
    for pkg in GUILD_PACKAGES:
        if path.endswith(pkg):
            return True
    return False
