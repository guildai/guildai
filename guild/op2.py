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

from guild import config
from guild import flag_util
from guild import op_util2 as op_util
from guild import plugin as pluginlib
from guild import run as runlib
from guild import util

log = logging.getLogger("guild")

OP_RUNFILE_PATHS = [
    ["org_click"],
    ["org_psutil"],
    ["guild", "external"],
]

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
    pass

class OpInitError(Exception):
    pass

class ProcessError(Exception):
    pass

###################################################################
# Operation state
###################################################################

class Operation(object):

    def __init__(self, opref, cmd_args, flag_vals=None, flag_map=None,
                 flag_null_labels=None, label=None, stage=False,
                 extra_run_attrs=None, sourcecode=None, run_dir=None,
                 cmd_env=None, pre_process=None):
        self.opref = opref
        self.cmd_args = cmd_args
        self.flag_vals = flag_vals
        self.flag_map = flag_map
        self.flag_null_labels = flag_null_labels
        self.label = label
        self.stage = stage
        self.extra_run_attrs = extra_run_attrs
        self.sourcecode = sourcecode
        self.run_dir = run_dir
        self.cmd_env = cmd_env
        self.pre_process = pre_process

###################################################################
# Operation API
###################################################################

def run(op, _quiet=False, _background_pidfile=None, _stop_after=None):
    run = _init_run(op)
    _op_run(op, run)
    return run

def _init_run(op):
    run = _op_init_run(op)
    _op_set_run_attrs(op, run)
    _op_copy_sourcecode(op, run)
    _op_init_sourcecode_digest(run)
    return run

def _op_init_run(op):
    run = op_util.init_run(op.run_dir)
    log.debug("initializing run in %s", run.dir)
    run.init_skel()
    op_util.set_run_pending(run)
    return run

def _op_set_run_attrs(op, run):
    run.write_opref(op.opref)
    for name, val in (op.extra_run_attrs or {}).items():
        run.write_attr(name, val)
    run.write_attr("flags", op.flag_vals)
    run.write_attr("cmd", op.cmd_args)
    run.write_attr("env", op.cmd_env)
    if op.label is not None:
        run.write_attr("label", op.label)
    if op.flag_map:
        run.write_attr("flag_map", op.flag_map)

def _op_copy_sourcecode(op, run):
    op_util.copy_sourcecode(op, run)

def _op_init_sourcecode_digest(run):
    op_util.write_sourcecode_digest(run)

def _op_run(op, run):
    _op_init_started(run)
    env = _op_run_cmd_env(op, run)
    try:
        _op_pre_proc(op, run, env)
        _op_proc(op, run, env)
    finally:
        _op_clear_pending(run)

def _op_init_started(run):
    started = runlib.timestamp()
    run.write_attr("started", started)

def _op_run_cmd_env(op, run):
    env = dict(op.cmd_env)
    env["RUN_DIR"] = run.path
    env["RUN_ID"] = run.id
    util.check_env(env)
    return env

def _op_pre_proc(op, run, env):
    if not op.pre_process:
        return
    cmd_unresolved = op.pre_process.strip()
    cmd = util.resolve_refs(cmd_unresolved, op.flag_vals)
    cwd = run.path
    log.debug("pre-process command: %s", cmd)
    log.debug("pre-process env: %s", env)
    log.debug("pre-process cwd: %s", cwd)
    subprocess.check_call(cmd, shell=True, env=env, cwd=cwd)

def _op_proc(op, run, _env):
    print("TODO: proc whaaa???", op, run)

def _op_clear_pending(run):
    op_util.clear_run_pending(run)

###################################################################
# Op from opdef
###################################################################

def from_opdef(opdef, flag_vals, gpus=None, **kw):
    cmd_args, flag_vals, flag_map = _op_init_cmd_args(opdef, flag_vals)
    flag_null_labels = _op_init_flag_null_labels(opdef)
    sourcecode = op_util.sourcecode_for_opdef(opdef)
    cmd_env = _op_init_cmd_env(opdef, cmd_args, flag_vals, gpus)
    return Operation(
        opdef.opref,
        cmd_args,
        flag_vals=flag_vals,
        flag_map=flag_map,
        flag_null_labels=flag_null_labels,
        sourcecode=sourcecode,
        cmd_env=cmd_env,
        pre_process=opdef.pre_process,
        **kw)

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
        if m]

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
        "python_exe": _python_exe(opdef),
        "main_args": "__main_args__",
        "flag_args": "__flag_args__",
        "model_dir": opdef.guildfile.dir,
    })
    return extended

def _python_exe(opdef):
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

def _op_init_flag_null_labels(opdef):
    return {
        f.name: f.null_label
        for f in opdef.flags
    }

def _op_init_cmd_env(opdef, cmd_args, flag_vals, gpus):
    env = {}
    _apply_opdef_env(opdef, env)
    _apply_cmd_args_env(cmd_args, env)
    _apply_flags_env(flag_vals, env)
    _apply_os_env(env)
    _apply_op_env(opdef, env, gpus)
    util.check_env(env)
    return env

def _apply_opdef_env(opdef, env):
    env.update({
        name: str(val)
        for name, val in opdef.env.items()
    })

def _apply_cmd_args_env(args, env):
    flags, _other_args = op_util.args_to_flags(args)
    env.update({
        name.upper(): str(val)
        for name, val in flags.items()
    })

def _apply_flags_env(flag_vals, env):
    env.update({
        name.upper(): flag_util.encode_flag_val(val)
        for name, val in flag_vals.items()
    })

def _apply_os_env(env):
    env.update(util.safe_osenv())

def _apply_op_env(opdef, env, gpus):
    env["GUILD_HOME"] = config.guild_home()
    env["GUILD_OP"] = opdef.fullname
    env["GUILD_PLUGINS"] = _op_plugins(opdef)
    env["LOG_LEVEL"] = _log_level()
    env["PYTHONPATH"] = _python_path(opdef)
    env["SCRIPT_DIR"] = ""
    env["CMD_DIR"] = os.getcwd()
    env["MODEL_DIR"] = opdef.guildfile.dir or ""
    env["MODEL_PATH"] = os.path.pathsep.join(_model_paths(opdef))
    if opdef.flags_dest:
        env["FLAGS_DEST"] = opdef.flags_dest
    if opdef.set_trace:
        env["SET_TRACE"] = "1"
    if opdef.handle_keyboard_interrupt:
        env["HANDLE_KEYBOARD_INTERRUPT"] = "1"
    util.apply_env(env, os.environ, ["PROFILE"])
    if gpus is not None:
        log.info(
            "Limiting available GPUs (CUDA_VISIBLE_DEVICES) to: %s",
            gpus or "<none>")
        env["CUDA_VISIBLE_DEVICES"] = gpus

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

def _log_level():
    try:
        return os.environ["LOG_LEVEL"]
    except KeyError:
        return str(logging.getLogger().getEffectiveLevel())

def _python_path(opdef):
    paths = (
        _env_paths() +
        _run_sourcecode_paths() +
        _model_paths(opdef) +
        _guild_paths()
    )
    return os.path.pathsep.join(paths)

def _env_paths():
    env = os.getenv("PYTHONPATH")
    return env.split(os.path.pathsep) if env else []

def _run_sourcecode_paths():
    return [".guild/sourcecode"]

def _model_paths(opdef):
    """Returns the model paths for opdef.

    Guild is moving to an isolation scheme that requires these paths
    NOT be included in a run system path. When they are, it's possible
    that the run sourcecode dir does not contain all of the required
    code and these model paths are relied on to silently provide
    what's missing.

    At the moment, cross package inheritance relies on these
    paths. Until multiple packages can be merged into a single
    sourcecode tree (tricky considering they use multiple roots that
    share a common path to guild.yml) we rely on these paths to
    support that functionality.
    """
    return op_util.opdef_model_paths(opdef)

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

###################################################################
# Op from run
###################################################################

def from_run(_run):
    assert False, "TODO"
