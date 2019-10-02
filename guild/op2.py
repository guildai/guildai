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
import re
import sys

from guild import flag_util
from guild import op_util2 as op_util
from guild import util

log = logging.getLogger("guild")

CMD_OPTION_P = re.compile("--([^=]+)")

DEFAULT_EXEC = "${python_exe} -um guild.op_main ${main_args} -- ${flag_args}"
STEPS_EXEC = "${python_exe} -um guild.steps_main"

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
# Operation API
###################################################################

class Operation(object):

    def __init__(self, opref, cmd_args, flag_vals=None, flag_map=None,
                 label=None, extra_run_attrs=None, sourcecode=None,
                 sourcecode_digest=True, run_dir=None):
        self.opref = opref
        self.cmd_args = cmd_args
        self.flag_vals = flag_vals
        self.flag_map = flag_map
        self.label = label
        self.extra_run_attrs = extra_run_attrs
        self.sourcecode = sourcecode
        self.sourcecode_digest = sourcecode_digest
        self.run_dir = run_dir

def run(op, _quiet=False, _background_pidfile=None, _stop_after=None):
    run = init(op)
    _op_run(run)
    return run

def init(op):
    run = _op_init_run(op)
    _op_set_run_attrs(op, run)
    _op_copy_sourcecode(op, run)
    _op_init_sourcecode_digest(op, run)
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
    if op.label is not None:
        run.write_attr("label", op.label)
    if op.flag_map:
        run.write_attr("flag_map", op.flag_map)

def _op_copy_sourcecode(op, _run):
    if op.sourcecode:
        assert False, ("TODO: what is op.sourcecode? - a list of "
                       "files to copy or a copytree spec?")

def _op_init_sourcecode_digest(op, run):
    if op.sourcecode_digest:
        op_util.write_sourcecode_digest(run)

def _op_run(run):
    print("TODO: run operation staged in %s" % run.dir)

###################################################################
# Op from opdef
###################################################################

def from_opdef(opdef, flag_vals, **kw):
    cmd_args, flag_vals, flag_map = _op_init_cmd_args(opdef, flag_vals)
    return Operation(
        opdef.opref,
        cmd_args,
        flag_vals=flag_vals,
        flag_map=flag_map,
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

###################################################################
# Op from run
###################################################################

def from_run(_run):
    assert False, "TODO"
