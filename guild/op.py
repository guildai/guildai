# Copyright 2017 TensorHub, Inc.
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
import shlex
import subprocess
import sys
import time
import uuid

import guild.run
import guild.util
import guild.var

OP_RUNFILES = [
    "org_psutil"
]

class InvalidCmd(ValueError):
    pass

class Operation(object):

    def __init__(self, name, cmd_args, cmd_env, attrs=None):
        self.name = name
        self.cmd_args = cmd_args
        self.cmd_env = cmd_env
        self.attrs = attrs or {}
        self._running = False
        self._started = None
        self._stopped = None
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
        logging.debug(
            "Starting op %s\n"
            " cmd: %s\n"
            " env: %s\n"
            " cwd: %s",
            self.name, args, env, cwd)
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
    return uuid.uuid1().hex

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
    _acc_flags(op.modeldef.flags, flags)
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
    env.update(guild.util.safe_osenv())
    env["GUILD_PLUGINS"] = _op_plugins(project_op)
    env["LOG_LEVEL"] = str(logging.getLogger().getEffectiveLevel())
    env["PYTHONPATH"] = _python_path(project_op)
    return env

def _op_plugins(project_op):
    op_plugins = []
    for name, plugin in guild.plugin.iter_plugins():
        if _plugin_disabled_in_project(name, project_op):
            plugin_enabled = False
            reason = "explicitly disabled by model or user config"
        else:
            plugin_enabled, reason = plugin.enabled_for_op(project_op)
        logging.debug(
            "plugin '%s' %s%s",
            name,
            "enabled" if plugin_enabled else "disabled",
            " (%s)" % reason if reason else "")
        if plugin_enabled:
            op_plugins.append(name)
    return ",".join(op_plugins)

def _plugin_disabled_in_project(name, project_op):
    disabled = (project_op.disabled_plugins +
                project_op.modeldef.disabled_plugins)
    return any([disabled_name in (name, "all") for disabled_name in disabled])

def _python_path(project_op):
    paths = _model_paths(project_op) + _guild_paths()
    return os.path.pathsep.join(paths)

def _model_paths(project_op):
    return [os.path.dirname(project_op.modelfile.src)]

def _guild_paths():
    guild_path = os.path.dirname(os.path.dirname(__file__))
    return [guild_path] + _runfile_paths()

def _runfile_paths():
    return [path for path in sys.path if _is_runfile_pkg(path)]

def _is_runfile_pkg(path):
    return os.path.split(path)[-1] in OP_RUNFILES
