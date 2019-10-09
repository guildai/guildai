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
import re
import subprocess
import sys
import time

from guild import config
from guild import exit_code
from guild import flag_util
from guild import op_cmd
from guild import op_dep
from guild import op_util2 as op_util
from guild import plugin as pluginlib
from guild import run as runlib
from guild import summary
from guild import util

log = logging.getLogger("guild")

OP_RUNFILE_PATHS = [
    ["org_click"],
    ["org_psutil"],
    ["guild", "external"],
]

PROC_TERM_TIMEOUT_SECONDS = 30

CMD_OPTION_P = re.compile("--([^=]+)")

DEFAULT_EXEC = "${python_exe} -um guild.op_main ${main_args} -- ${flag_args}"
STEPS_EXEC = "${python_exe} -um guild.steps_main"

DEFAULT_OUTPUT_SCALARS = [
    r"^(\key):\s+(\value)$",
]

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
# Operation state
###################################################################

class Operation(object):

    def __init__(self, opref, cmd_template, cmd_args, flag_vals=None,
                 flag_map=None, flag_null_labels=None, label=None,
                 extra_run_attrs=None, sourcecode_select=None,
                 sourcecode_src=None, run_dir=None, cmd_env=None,
                 deps=None, output_scalars=None, stoppable=False,
                 python_requires=None, callbacks=None):
        self.cmd_template = cmd_template
        self.opref = opref
        self.cmd_args = cmd_args
        self.flag_vals = flag_vals
        self.flag_map = flag_map
        self.flag_null_labels = flag_null_labels
        self.label = label
        self.extra_run_attrs = extra_run_attrs
        self.sourcecode_src = sourcecode_src
        self.sourcecode_select = sourcecode_select
        self.run_dir = run_dir
        self.cmd_env = cmd_env
        self.deps = deps
        self.output_scalars = output_scalars
        self.stoppable = stoppable
        self.python_requires = python_requires
        self.callbacks = callbacks

class OperationCallbacks(object):

    def __init__(self, run_initialized=None):
        self.run_initialized = run_initialized

def _callback(name, op, *rest_args):
    if op.callbacks:
        cb = getattr(op.callbacks, name, None)
        if cb:
            cb(op, *rest_args)

###################################################################
# Op for opdef
###################################################################

def for_opdef(opdef, flag_vals, gpus=None, **kw):
    cmd_template = _op_init_cmd_template(opdef)

    # TODO gpus should be in extra_env

    cmd_args, flag_vals, flag_map = _op_init_cmd_args(opdef, flag_vals)


    sourcecode_select = op_util.sourcecode_select_for_opdef(opdef)
    cmd_env = _op_init_cmd_env(opdef, cmd_args, flag_vals, gpus)
    deps = _op_deps_for_opdef(opdef, flag_vals)
    flag_null_labels = _op_init_flag_null_labels(opdef)
    python_requires = opdef.python_requires or opdef.modeldef.python_requires
    return Operation(
        opdef.opref,
        cmd_template,
        cmd_args,
        flag_vals=flag_vals,
        flag_map=flag_map,
        flag_null_labels=flag_null_labels,
        sourcecode_src=opdef.guildfile.dir,
        sourcecode_select=sourcecode_select,
        cmd_env=cmd_env,
        deps=deps,
        output_scalars=opdef.output_scalars,
        stoppable=opdef.stoppable,
        python_requires=python_requires,
        **kw)

# =================================================================
# Cmd template
# =================================================================

def _op_init_cmd_template(opdef):
    cmd_args = _template_cmd_args(opdef)
    flag_args = _template_flag_args(opdef)
    return op_cmd.CmdTemplate(cmd_args, flag_args)

def _template_cmd_args(opdef):
    main_args = op_util.split_cmd(opdef.main or "")
    exec_args = op_util.split_cmd(_opdef_exec(opdef))
    _apply_main_args(main_args, exec_args)
    _apply_flag_args_marker(exec_args)
    return exec_args

def _opdef_exec(opdef):
    """Returns exec template for opdef.

    If exec is specified explicitly, it's returned, otherwise main or
    steps are used to generate a template.
    """
    if opdef.exec_:
        if opdef.main:
            log.warning(
                "operation 'exec' and 'main' both specified, "
                "ignoring 'main'")
        if opdef.steps:
            log.warning(
                "operation 'exec' and 'steps' both specified, "
                "ignoring 'steps'")
        return opdef.exec_
    elif opdef.main:
        if opdef.steps:
            log.warning(
                "operation 'main' and 'steps' both specified, "
                "ignoring 'steps'")
        return DEFAULT_EXEC
    elif opdef.steps:
        return STEPS_EXEC
    else:
        raise ValueError(
            "invalid definition for %s: must define either "
            "exec, main, or steps" % opdef.fullname)

def _apply_main_args(main_args, exec_args):
    i = 0
    while i < len(exec_args):
        if exec_args[i] == "${main_args}":
            exec_args[i:i+1] = main_args
            i += len(main_args)
        i += 1

def _apply_flag_args_marker(exec_args):
    for i, val in enumerate(exec_args):
        if val == "${flag_args}":
            exec_args[i] = "__flag_args__"

def _template_flag_args(opdef):
    return {
        flagdef.name: _template_flag_arg(flagdef)
        for flagdef in opdef.flags
    }

def _template_flag_arg(flagdef):
    return op_cmd.FlagArg(
        arg_name=flagdef.arg_name,
        arg_skip=_flagdef_arg_skip(flagdef),
        arg_switch=flagdef.arg_switch,
    )

def _flagdef_arg_skip(flagdef):
    if flagdef.arg_skip is not None:
        return flagdef.arg_skip
    return flagdef.opdef.default_flag_arg_skip

# =================================================================
# Cmd args for opdef
# =================================================================

def _op_init_cmd_args(opdef, flag_vals):
    flag_vals = _op_flag_vals(opdef, flag_vals)
    main_cmd_args = _op_main_args(opdef, flag_vals)
    flag_args, flag_map = _op_flag_args(opdef, main_cmd_args, flag_vals)
    exec_cmd_args = _op_exec_args(opdef, flag_vals, main_cmd_args, flag_args)
    return exec_cmd_args, flag_vals, flag_map

def _op_flag_vals(opdef, flag_vals):
    vals = {
        flag.name: flag.default
        for flag in opdef.flags
    }
    vals.update(flag_vals)
    return util.resolve_all_refs(vals)

def _op_main_args(opdef, flag_vals):
    """Returns a list of args per opdef.main.

    Returns empty list if main is not specified.
    """
    if not opdef.main:
        return []
    try:
        return _split_and_resolve_args(opdef.main, flag_vals)
    except util.UndefinedReferenceError as e:
        raise InvalidOpDef(
            opdef,
            "main contains invalid reference '%s'"
            % e.reference)

def _split_and_resolve_args(cmd, flag_vals):
    """Splits and resolve args for string or list cmd."""
    format_part = lambda part: str(util.resolve_refs(part, flag_vals))
    return [format_part(part) for part in op_util.split_cmd(cmd)]

def _op_flag_args(opdef, cmd_args, flag_vals):
    flag_args = []
    flag_vals, flag_map = op_util.mapped_flag_vals(flag_vals, opdef)
    cmd_options = _cmd_options(cmd_args)
    for name, val in sorted(flag_vals.items()):
        if name in cmd_options:
            log.warning(
                "ignoring flag '%s = %s' because it's shadowed "
                "in the operation cmd", name, val)
            continue
        flag_args.extend(_cmd_option_args(name, val))
    return flag_args, flag_map

def _cmd_options(args):
    return [
        m.group(1)
        for m in [CMD_OPTION_P.match(arg) for arg in args]
        if m
    ]

def _cmd_option_args(name, val):
    if val is None:
        return []
    opt = "--%s" % name
    if val is op_util.NO_ARG_VALUE:
        return [opt]
    else:
        return [opt, flag_util.encode_flag_val(val)]

def _op_exec_args(opdef, flag_vals, main_args, flag_args):
    template = _exec_template(opdef)
    flag_vals = _extended_flag_vals(flag_vals, opdef)
    try:
        args = _split_and_resolve_args(template, flag_vals)
    except util.UndefinedReferenceError as e:
        raise InvalidOpDef(
            opdef,
            "exec contains invalid reference '%s'"
            % e.args[0])
    else:
        args = _repl_args(args, "__main_args__", main_args)
        args = _repl_args(args, "__flag_args__", flag_args)
        return args

def _exec_template(opdef):
    """Returns exec template for opdef.

    If exec is specified explicitly, it's returned, otherwise main or
    steps are used to generate a template.
    """
    if opdef.exec_:
        if opdef.main:
            log.warning(
                "operation 'exec' and 'main' both specified, "
                "ignoring 'main'")
        if opdef.steps:
            log.warning(
                "operation 'exec' and 'steps' both specified, "
                "ignoring 'steps'")
        return opdef.exec_
    elif opdef.main:
        if opdef.steps:
            log.warning(
                "operation 'main' and 'steps' both specified, "
                "ignoring 'steps'")
        return DEFAULT_EXEC
    elif opdef.steps:
        return STEPS_EXEC
    assert False, opdef

def _extended_flag_vals(flag_vals, opdef):
    """Extend flag_vals with special flag vals for op exec resolution.

    The following flag vals are included in the extended flag vals:

      'python_exe': full path to Python exe per opdef

      'main_args':  special marker object designating the location of
                    args specified in opdef main

      'flag_args':  special marker object designating the location of
                    flag args

      'model_dir':  directory containing the operation guild file

    If any of the extended values are defined in flag_vals, they are
    replaced here.
    """
    extended = dict(flag_vals)
    extended.update({
        "python_exe": _python_exe_for_opdef(opdef),
        "main_args": "__main_args__",
        "flag_args": "__flag_args__",
        "model_dir": opdef.guildfile.dir,
    })
    return extended

def _python_exe_for_opdef(opdef):
    req = opdef.python_requires or opdef.modeldef.python_requires
    if req:
        matching = util.find_python_interpreter(req)
        if not matching:
            raise OpInitError(
                "cannot find a python interpreter for "
                "version requirement %r" % req)
        path, _ver = matching
        return path
    return sys.executable

def _repl_args(args, key, replacement):
    """Replaces occurrences of key in args with replacement."""
    ret = []
    for arg in args:
        if arg == key:
            ret.extend(replacement)
        else:
            ret.append(arg)
    return ret

# =================================================================
# Cmd env for opdef
# =================================================================

def _op_init_cmd_env(opdef, cmd_args, flag_vals, gpus):
    env = {}
    _apply_opdef_env(opdef, env)
    _apply_cmd_args_env(cmd_args, env)
    _apply_flags_env(flag_vals, env)
    _apply_system_env(gpus, env)
    util.check_env(env)
    return env

def _apply_opdef_env(opdef, env):
    env.update(opdef.env or {})
    env["GUILD_OP"] = opdef.fullname
    env["GUILD_PLUGINS"] = _op_plugins(opdef)
    env["PROJECT_DIR"] = opdef.guildfile.dir or ""
    if opdef.flags_dest:
        env["FLAGS_DEST"] = opdef.flags_dest
    if opdef.handle_keyboard_interrupt:
        env["HANDLE_KEYBOARD_INTERRUPT"] = "1"

def _op_plugins(opdef):
    project_plugins = _project_plugins(opdef)
    op_plugins = []
    for name, plugin in pluginlib.iter_plugins():
        if not _plugin_selected(plugin, project_plugins):
            log.debug("plugin '%s' not configured for operation", name)
            continue
        enabled, reason = plugin.enabled_for_op(opdef)
        if not enabled:
            log.debug(
                "plugin '%s' configured for operation but cannot be enabled%s",
                name, " (%s)" % reason if reason else "")
            continue
        log.debug(
            "plugin '%s' enabled for operation%s",
            name, " (%s)" % reason if reason else "")
        op_plugins.append(name)
    return ",".join(sorted(op_plugins))

def _project_plugins(opdef):
    if opdef.plugins is not None:
        return opdef.plugins or []
    return opdef.modeldef.plugins or []

def _plugin_selected(plugin, selected):
    for name in selected:
        if name == plugin.name or name in plugin.provides:
            return True
    return False


def _apply_cmd_args_env(args, env):
    flags, _other_args = op_util.args_to_flags(args)
    env.update({
        name.upper(): str(val)
        for name, val in flags.items()
    })

def _apply_flags_env(flag_vals, env):
    env.update({
        _flag_env_name(name): flag_util.encode_flag_val(val)
        for name, val in flag_vals.items()
    })

def _flag_env_name(name):
    return "FLAG_%s" % util.env_var_name(name)

def _apply_system_env(gpus, env):
    env.update(util.safe_osenv())
    env["GUILD_HOME"] = config.guild_home()
    env["LOG_LEVEL"] = _log_level()
    env["PYTHONPATH"] = _python_path()
    env["CMD_DIR"] = os.getcwd()
    if gpus is not None:
        env["CUDA_VISIBLE_DEVICES"] = gpus

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
# Misc op init for opdef
# =================================================================

def _op_deps_for_opdef(opdef, flag_vals):
    try:
        return op_dep.deps_for_opdef(opdef, flag_vals)
    except op_dep.OpDependencyError as e:
        raise InvalidOpDef(opdef, str(e))

def _op_init_flag_null_labels(opdef):
    return {
        f.name: f.null_label
        for f in opdef.flags
        if f.null_label is not None
    }

###################################################################
# Op for run
###################################################################

def for_run(run, gpus=None, **kw):
    cmd_args = run.get("cmd")
    flag_vals = run.get("flags")
    flag_map = run.get("flag_map")
    cmd_env = _op_init_cmd_env_for_run(run, gpus)
    output_scalars = run.get("output_scalars")
    stoppable = run.get("stoppable")
    return Operation(
        run.opref,
        cmd_args,
        flag_vals=flag_vals,
        flag_map=flag_map,
        cmd_env=cmd_env,
        output_scalars=output_scalars,
        run_dir=run.dir,
        stoppable=stoppable,
        **kw)

def _op_init_cmd_env_for_run(run, gpus):
    env = run.get("env")
    _apply_system_env(gpus, env)
    util.check_env(env)
    return env

###################################################################
# Run
###################################################################

def run(op, stage=False, quiet=False, _background_pidfile=None,
        stop_after=None):
    run = init_run(op)
    _callback("run_initialized", op, run)
    if stage:
        exit_status = _op_stage(op, run)
    else:
        exit_status = _op_run(op, run, quiet, stop_after)
    return run, exit_status

# =================================================================
# Init run
# =================================================================

def init_run(op, run_dir=None):
    run = _op_init_pending_run(op, run_dir)
    _op_init_run_attrs(op, run)
    _op_copy_sourcecode(op, run)
    _op_init_sourcecode_digest(run)
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
    for name, val in (op.extra_run_attrs or {}).items():
        run.write_attr(name, val)
    run.write_attr("flags", op.flag_vals)
    run.write_attr("cmd", op.cmd_args)
    run.write_attr("env", op.cmd_env)
    if op.output_scalars:
        run.write_attr("output_scalars", op.output_scalars)
    if op.stoppable:
        run.write_attr("stoppable", op.stoppable)
    if op.label is not None:
        run.write_attr("label", op.label)
    if op.flag_map:
        run.write_attr("flag_map", op.flag_map)

def _op_copy_sourcecode(op, run):
    if os.getenv("NO_SOURCECODE") == "1":
        log.debug("NO_SOURCECODE=1, skipping sourcecode copy")
        return
    if not op.sourcecode_src:
        log.debug("no sourcecode source, skipping sourcecode copy")
        return
    if not op.sourcecode_select:
        log.debug("no sourcecode rules, skipping sourcecode copy")
        return
    dest = run.guild_path("sourcecode")
    log.debug(
        "copying source code files for run %s from %s to %s",
        run.id, op.sourcecode_src, dest)
    op_util.copy_sourcecode(op.sourcecode_src, op.sourcecode_select, dest)

def _op_init_sourcecode_digest(run):
    op_util.write_sourcecode_digest(run)

# =================================================================
# Stage op
# =================================================================

def _op_stage(op, run):
    env = _op_run_cmd_env(op, run)
    _op_resolve_deps(op, run)
    _op_write_sourceable_env(env, run)
    op_util.set_run_started(run)
    op_util.set_run_marker(run, "STAGED")
    op_util.clear_run_pending(run)
    return 0

def _op_run_cmd_env(op, run):
    env = dict(op.cmd_env)
    env["RUN_DIR"] = run.path
    env["RUN_ID"] = run.id
    util.check_env(env)
    return env

def _op_resolve_deps(op, run):
    if op.deps is None:
        return
    resolved = {}
    for dep in op.deps:
        resolved_sources = op_dep.resolve(dep, run.dir)
        resolved.setdefault(dep.resdef.name, []).extend(resolved_sources)
    run.write_attr("deps", resolved)

def _op_write_sourceable_env(env, run):
    skip_env = ("PWD", "_")
    with open(run.guild_path("ENV"), "w") as out:
        for name in sorted(env):
            if name in skip_env:
                continue
            out.write(
                "export %s=%s\n"
                % (name, util.shlex_quote(env[name])))

# =================================================================
# Run op
# =================================================================

def _op_run(op, run, quiet, stop_after):
    env = _op_run_cmd_env(op, run)
    _op_resolve_deps(op, run)
    op_util.set_run_started(run)
    try:
        proc = _op_proc(op, run, env)
        exit_status = _op_wait_for_proc(op, proc, run, quiet, stop_after)
        _op_finalize_run_attrs(run, exit_status)
        return exit_status
    finally:
        op_util.clear_run_marker(run, "STAGED")
        op_util.clear_run_pending(run)

def _op_proc(op, run, env):
    args = proc_args(op)
    assert args == op.cmd_args, (args, op.cmd_args)
    cwd = run.dir
    log.debug("starting operation run %s in %s", run.id, cwd)
    log.debug("operation command: %s", args)
    log.debug("operation env: %s", env)
    log.debug("operation cwd: %s", cwd)
    try:
        proc = subprocess.Popen(
            args,
            env=env,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
    except OSError as e:
        raise ProcessError(e)
    else:
        _write_proc_lock(proc, run)
        return proc

def proc_args(op):
    unresolved_args = op_cmd.cmd_args(op.cmd_template, op.flag_vals)
    params = _proc_arg_resolve_params(op)
    return [util.resolve_refs(arg, params) for arg in unresolved_args]

def _proc_arg_resolve_params(op):
    params = dict(op.flag_vals)
    params["python_exe"] = _proc_python_exe(op)
    return params

def _proc_python_exe(op):
    if op.python_requires:
        matching = util.find_python_interpreter(op.python_requires)
        if not matching:
            raise ProcessError(
                "cannot find a python interpreter for "
                "requirement %r" % op.python_requires)
        path, _ver = matching
        return path
    return sys.executable

def _write_proc_lock(proc, run):
    with open(run.guild_path("LOCK"), "w") as f:
        f.write(str(proc.pid))

def _op_wait_for_proc(op, proc, run, quiet, stop_after):
    try:
        return _op_watch_proc(op, proc, run, quiet, stop_after)
    except KeyboardInterrupt:
        return _handle_proc_interrupt(proc)

def _op_watch_proc(op, proc, run, quiet, stop_after):
    output_summary = _output_scalars_summary(op, run)
    with _RunOutput(run, proc, quiet, output_summary):
        return _proc_wait(proc, stop_after)

def _output_scalars_summary(op, run):
    try:
        summary.check_enabled()
    except summary.Disabled as e:
        log.warning(e)
        return None
    else:
        config, ignore = _output_scalars_config(op)
        summary_path = run.guild_path()
        return summary.OutputScalars(config, summary_path, ignore)

def _output_scalars_config(op):
    if op.output_scalars is None:
        return DEFAULT_OUTPUT_SCALARS, op.flag_vals.keys()
    return op.output_scalars, None

class _RunOutput(object):

    def __init__(self, run, *args):
        self._output = None
        self._run = run
        self._rest_args = args

    def __enter__(self):
        if os.getenv("NO_RUN_OUTPUT_CAPTURE") != "1":
            self._output = op_util.RunOutput(self._run, *self._rest_args)

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
