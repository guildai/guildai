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
import time

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

PROC_TERM_TIMEOUT_SECONDS = 30

class InvalidCmd(ValueError):
    pass

class Operation(object):

    def __init__(self, model, opdef, rundir=None, resource_config=None,
                 extra_attrs=None):
        self.model = model
        self.opdef = opdef
        self.cmd_args, self._flag_map = _init_cmd_args(opdef)
        self.cmd_env = _init_cmd_env(opdef)
        self._rundir = rundir
        self.resource_config = resource_config
        self.extra_attrs = extra_attrs
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
        self._run = init_run(self._rundir)
        log.debug("initializing run in %s", self._run.path)
        self._run.init_skel()

    def _init_attrs(self):
        assert self._run is not None
        for name, val in (self.extra_attrs or {}).items():
            self._run.write_attr(name, val)
        self._run.write_attr("opref", self._opref_attr())
        self._run.write_attr("flags", self.opdef.flag_values())
        self._run.write_attr("cmd", self.cmd_args)
        self._run.write_attr("env", self.cmd_env)
        self._run.write_attr("started", self._started)
        self._run.write_attr("_flag-map", self._flag_map)
        for key, val in self.model.modeldef.extra.items():
            self._run.write_attr("_%s" % key, val)

    def _opref_attr(self):
        ref = opref.OpRef.from_op(self.opdef.name, self.model.reference)
        return str(ref)

    def _resolve_deps(self):
        assert self._run is not None
        ctx = deps.ResolutionContext(
            target_dir=self._run.path,
            opdef=self.opdef,
            resource_config=self.resource_config)
        resolved = deps.resolve(self.opdef.dependencies, ctx)
        self._run.write_attr("deps", resolved)

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
        try:
            self._exit_status = self._proc.wait()
        except KeyboardInterrupt:
            self._exit_status = self._handle_proc_interrupt()
        self._stopped = guild.run.timestamp()
        _delete_proc_lock(self._run)

    def _handle_proc_interrupt(self):
        log.info("Operation interrupted - waiting for process to exit")
        kill_after = time.time() + PROC_TERM_TIMEOUT_SECONDS
        while time.time() < kill_after:
            if self._proc.poll() is not None:
                break
            time.sleep(1)
        if self._proc.poll() is None:
            log.warning("Operation process did not exit - stopping forcefully")
            self._proc.kill()
        return -15 # exit code for SIGTERM

    def _finalize_attrs(self):
        assert self._run is not None
        assert self._exit_status is not None
        assert self._stopped is not None
        if not os.path.exists(self._run.path):
            log.warning("run directory has been deleted, unable to finalize")
            return
        self._run.write_attr("exit_status", self._exit_status)
        self._run.write_attr("stopped", self._stopped)

def _init_cmd_args(opdef):
    python_args = [_python_cmd(opdef), "-um", "guild.op_main"]
    flag_vals = util.resolve_all_refs(opdef.flag_values())
    cmd_args = _cmd_args(opdef.cmd, flag_vals)
    flag_args, flag_map = _flag_args(flag_vals, opdef, cmd_args)
    cmd_args = python_args + cmd_args + flag_args
    return cmd_args, flag_map

def _python_cmd(_opdef):
    # TODO: This is an important operation that should be controlled
    # by the model (e.g. does it run under Python 2 or 3, etc.) and
    # not by whatever Python runtime is configured in the user env.
    return sys.executable

def _cmd_args(cmd, flag_vals):
    return [util.resolve_refs(part, flag_vals) for part in _split_cmd(cmd)]

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

def _flag_args(flag_vals, opdef, cmd_args):
    flag_args = []
    flag_vals, flag_map = _flag_cmd_arg_vals(flag_vals, opdef)
    cmd_options = _cmd_options(cmd_args)
    for name in sorted(flag_vals):
        value = flag_vals[name]
        if name in cmd_options:
            log.warning(
                "ignoring flag '%s = %s' because it's shadowed "
                "in the operation cmd", name, value)
            continue
        flag_args.extend(_cmd_option_args(name, value))
    return flag_args, flag_map

def _flag_cmd_arg_vals(flag_vals, opdef):
    vals = {}
    flag_map = {}
    for name, val in flag_vals.items():
        if val is None:
            continue
        flagdef = opdef.get_flagdef(name)
        if flagdef:
            if flagdef.options:
                _apply_option_args(flagdef, val, flag_vals, vals, flag_map)
            elif not flagdef.arg_skip:
                _apply_flag_arg(flagdef, val, flag_vals, vals, flag_map)
        else:
            vals[name] = val
    return vals, flag_map

def _apply_option_args(flagdef, val, flag_vals, target, flag_map):
    for opt in flagdef.options:
        if opt.value == val:
            if opt.args:
                args = {
                    name: util.resolve_refs(val, flag_vals)
                    for name, val in opt.args.items()
                }
                target.update(args)
            elif not flagdef.arg_skip:
                _apply_flag_arg(flagdef, val, flag_vals, target, flag_map)
            break
    else:
        log.warning(
            "unsupported option %r for '%s' flag, ignoring",
            val, flagdef.name)

def _apply_flag_arg(flagdef, value, flag_vals, target, flag_map):
    if flagdef.arg_name:
        arg_name = flagdef.arg_name
        flag_map[arg_name] = flagdef.name
    else:
        arg_name = flagdef.name
    arg_val = util.resolve_refs(value, flag_vals)
    target[arg_name] = arg_val

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

def init_run(path=None):
    run_id = guild.run.mkid()
    if not path:
        path = os.path.join(var.runs_dir(), run_id)
    return guild.run.Run(run_id, path)
