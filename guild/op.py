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
import re
import shlex
import subprocess
import sys

import guild.plugin
import guild.run

from guild import deps
from guild import opref
from guild import util
from guild import var

log = logging.getLogger("guild")

OP_RUNFILE_PATHS = [
    ["org_click"],
    ["org_psutil"],
    ["guild", "external"],
]

class InvalidCmd(ValueError):
    pass

class Operation(object):

    def __init__(self, model, opdef, rundir=None, resource_config=None,
                 extra_attrs=None):
        self.model = model
        self.opdef = opdef
        self.cmd_args = _init_cmd_args(opdef)
        self.cmd_env = _init_cmd_env(opdef)
        self._rundir = rundir
        self._resource_config = resource_config
        self._extra_attrs = extra_attrs
        self._running = False
        self._started = None
        self._stopped = None
        self._run = None
        self._proc = None
        self._exit_status = None

    @property
    def rundir(self):
        return self._rundir or (self._run.path if self._run else None)

    def run(self):
        assert not self._running
        self._running = True
        self._started = guild.run.timestamp()
        self._init_run()
        self._init_attrs()
        self._resolve_deps()
        self._start_proc()
        self._wait_for_proc()
        self._finalize_attrs()
        return self._exit_status

    def _init_run(self):
        run_id = guild.run.mkid()
        if self._rundir:
            path = self._rundir
        else:
            path = os.path.join(var.runs_dir(), run_id)
        self._run = guild.run.Run(run_id, path)
        log.debug("initializing run in %s", path)
        self._run.init_skel()

    def _init_attrs(self):
        assert self._run is not None
        for name, val in (self._extra_attrs or {}).items():
            self._run.write_attr(name, val)
        self._run.write_attr("opref", self._opref_attr())
        self._run.write_attr("flags", self.opdef.flag_values())
        self._run.write_attr("cmd", self.cmd_args)
        self._run.write_attr("env", self.cmd_env)
        self._run.write_attr("started", self._started)

    def _opref_attr(self):
        ref = opref.OpRef.from_op(self.opdef.name, self.model.reference)
        return str(ref)

    def _resolve_deps(self):
        assert self._run is not None
        ctx = deps.ResolutionContext(
            target_dir=self._run.path,
            opdef=self.opdef,
            resource_config=self._resource_config)
        deps.resolve(self.opdef.dependencies, ctx)

    def _start_proc(self):
        assert self._proc is None
        assert self._run is not None
        args = self._proc_args()
        env = self._proc_env()
        cwd = self._run.path
        log.debug("starting operation run %s", self._run.id)
        log.debug("operation command: %s", args)
        log.debug("operation env: %s", env)
        log.debug("operation cwd: %s", cwd)
        self._proc = subprocess.Popen(args, env=env, cwd=cwd)
        _write_proc_lock(self._proc, self._run)

    def _proc_args(self):
        return self.cmd_args

    def _proc_env(self):
        assert self._run is not None
        env = {}
        env.update(self.cmd_env)
        env["RUNDIR"] = self._run.path
        env["RUNID"] = self._run.id
        return env

    def _wait_for_proc(self):
        assert self._proc is not None
        self._exit_status = self._proc.wait()
        self._stopped = guild.run.timestamp()
        _delete_proc_lock(self._run)

    def _finalize_attrs(self):
        assert self._run is not None
        assert self._exit_status is not None
        assert self._stopped is not None
        self._run.write_attr("exit_status", self._exit_status)
        self._run.write_attr("stopped", self._stopped)

def _init_cmd_args(opdef):
    python_args = [_python_cmd(opdef), "-u", _run_script_path()]
    cmd_args = _split_cmd(opdef.cmd)
    flag_args = _flag_args(opdef, cmd_args)
    return python_args + cmd_args + flag_args

def _python_cmd(_opdef):
    # TODO: This is an important operation that should be controlled
    # by the model (e.g. does it run under Python 2 or 3, etc.) and
    # not by whatever Python runtime is configured in the user env.
    return sys.executable

def _run_script_path():
    return os.path.join(os.path.dirname(__file__), "scripts", "run")

def _split_cmd(cmd):
    if isinstance(cmd, list):
        return cmd
    else:
        # If cmd is None, this call will block (see
        # https://bugs.python.org/issue27775)
        if not cmd:
            raise InvalidCmd(cmd)
        parts = shlex.split(cmd or "")
        stripped = [part.strip() for part in parts]
        return [x for x in stripped if x]

def _flag_args(opdef, cmd_args):
    flag_args = []
    flag_vals = _flag_cmd_arg_vals(opdef)
    cmd_options = _cmd_options(cmd_args)
    for name in sorted(flag_vals):
        value = flag_vals[name]
        if name in cmd_options:
            log.warning(
                "ignoring flag '%s = %s' because it's shadowed "
                "in the operation cmd", name, value)
            continue
        flag_args.extend(_cmd_option_args(name, value))
    return flag_args

def _flag_cmd_arg_vals(opdef):
    vals = {}
    for name, flag_val in opdef.flag_values().items():
        if flag_val is None:
            continue
        flagdef = opdef.get_flagdef(name)
        if flagdef:
            if flagdef.options:
                _apply_option_args(flagdef, flag_val, vals)
            else:
                _apply_flag_arg(flagdef, flag_val, vals)
        else:
            vals[name] = flag_val
    return vals

def _apply_option_args(flagdef, val, target):
    for opt in flagdef.options:
        if opt.value == val:
            if opt.args:
                target.update(opt.args)
            else:
                target[_flagdef_arg_name(flagdef)] = val
            break
    else:
        log.warning(
            "unsupported option %r for '%s' flag, ignoring",
            val, flagdef.name)

def _flagdef_arg_name(flagdef):
    return flagdef.arg_name if flagdef.arg_name else flagdef.name

def _apply_flag_arg(flagdef, value, target):
    target[_flagdef_arg_name(flagdef)] = value

def _cmd_options(args):
    p = re.compile("--([^=]+)")
    return [m.group(1) for m in [p.match(arg) for arg in args] if m]

def _cmd_option_args(name, val):
    opt = "--%s" % name
    if val is None:
        return []
    elif val is True:
        return [opt]
    else:
        return [opt, str(val)]

def _init_cmd_env(opdef):
    env = {}
    env.update(util.safe_osenv())
    env["GUILD_PLUGINS"] = _op_plugins(opdef)
    env["LOG_LEVEL"] = str(logging.getLogger().getEffectiveLevel())
    env["PYTHONPATH"] = _python_path(opdef)
    env["SCRIPT_DIR"] = ""
    return env

def _op_plugins(opdef):
    op_plugins = []
    for name, plugin in guild.plugin.iter_plugins():
        if _plugin_disabled_in_project(name, opdef):
            plugin_enabled = False
            reason = "explicitly disabled by model or user config"
        else:
            plugin_enabled, reason = plugin.enabled_for_op(opdef)
        log.debug(
            "plugin '%s' %s%s",
            name,
            "enabled" if plugin_enabled else "disabled",
            " (%s)" % reason if reason else "")
        if plugin_enabled:
            op_plugins.append(name)
    return ",".join(sorted(op_plugins))

def _plugin_disabled_in_project(name, opdef):
    disabled = (opdef.disabled_plugins +
                opdef.modeldef.disabled_plugins)
    return any([disabled_name in (name, "all") for disabled_name in disabled])

def _python_path(opdef):
    paths = _env_paths() + _model_paths(opdef) + _guild_paths()
    return os.path.pathsep.join(paths)

def _env_paths():
    env = os.getenv("PYTHONPATH")
    return env.split(os.path.pathsep) if env else []

def _model_paths(opdef):
    return [os.path.abspath(opdef.modelfile.dir)]

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

def _write_proc_lock(proc, run):
    with open(run.guild_path("LOCK"), "w") as f:
        f.write(str(proc.pid))

def _delete_proc_lock(run):
    try:
        os.remove(run.guild_path("LOCK"))
    except OSError:
        pass
