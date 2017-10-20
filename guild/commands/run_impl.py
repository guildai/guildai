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

import guild.op
from guild import cli
from guild import cmd_impl_support

def main(args, ctx):
    model_ref, op_name = _parse_opspec(args.opspec)
    model = _resolve_model(model_ref, ctx)
    opdef = _resolve_opdef(op_name, model)
    op = _init_op(opdef, model, args)
    if args.print_command:
        _print_command(op)
    elif args.print_env:
        _print_env(op)
    else:
        _maybe_run(op, model, args)

def _parse_opspec(spec):
    parts = spec.split(":", 1)
    if len(parts) == 1:
        return None, parts[0]
    else:
        return parts

def _resolve_model(model_ref, ctx):
    for model in cmd_impl_support.iter_all_models(ctx):
        if model_ref is None:
            if _is_default_cwd_model(model, ctx):
                return model
        else:
            if _match_model_ref(model_ref, model):
                return model
    _no_model_error(model_ref, ctx)

def _is_default_cwd_model(model, ctx):
    return (cmd_impl_support.is_cwd_model(model, ctx) and
            model.name == model.modeldef.modelfile.default_model.name)

def _match_model_ref(model_ref, model):
    if '/' in model_ref:
        return model_ref == model.fullname
    else:
        return model_ref == model.name

def _no_model_error(model_ref, ctx):
    if model_ref is None:
        cmd_impl_support.no_models_error(ctx)
    else:
        cli.error(
            "cannot find model '%s'\n"
            "Try 'guild models -a' for a list of available models."
            % model_ref)

def _resolve_opdef(name, model):
    opdef = model.modeldef.get_op(name)
    if opdef is None:
        _no_such_operation_error(name, model)
    return opdef

def _no_such_operation_error(name, model):
    cli.error(
        "operation '%s' is not defined for model '%s'\n"
        "Try 'guild operations %s' for a list of available operations."
        % (name, model.name, model.name))

def _init_op(opdef, model, args):
    _apply_flags(args, opdef)
    _apply_disable_plugins(args, opdef)
    ref = "%s %s" % (model.reference, opdef.name)
    return guild.op.from_opdef(opdef, ref)

def _apply_flags(args, opdef):
    for arg in args.args:
        name, val = _parse_flag(arg)
        opdef.set_flag_value(name, val)

def _parse_flag(s):
    parts = s.split("=", 1)
    if len(parts) == 1:
        return parts[0], None
    else:
        return parts

def _apply_disable_plugins(args, opdef):
    if args.disable_plugins:
        opdef.disabled_plugins.extend([
            name.strip() for name in args.disable_plugins.split(",")
        ])

def _print_command(op):
    formatted = " ".join([_maybe_quote_arg(arg) for arg in op.cmd_args])
    cli.out(formatted)

def _maybe_quote_arg(arg):
    return '"%s"' % arg if " " in arg else arg

def _print_env(op):
    for name, val in sorted(op.cmd_env.items()):
        cli.out("export %s=%s" % (name, val))

def _maybe_run(op, model, args):
    if args.yes or _confirm_run(op, model):
        result = op.run()
        if result != 0:
            cli.error(exit_status=result)

def _confirm_run(op, model):
    op_desc = "%s/%s" % (model.package_name, op.name)
    flags = _op_flags(op)
    if flags:
        prompt = (
            "You are about to run %s with the following flags:\n"
            "%s\n"
            "Continue?"
            % (op_desc, _format_op_flags(flags)))
    else:
        prompt = (
            "You are about to run %s\n"
            "Continue?" % op_desc)
    return guild.cli.confirm(prompt, default=True)

def _op_flags(op):
    flags = []
    args = op.cmd_args
    i = 1
    while i < len(args):
        cur_arg = args[i]
        i = i + 1
        next_arg = args[i] if i < len(args) else None
        if cur_arg[0:2] == "--":
            if next_arg and next_arg[0:2] != "--":
                flags.append((cur_arg[2:], next_arg))
                i = i + 1
            else:
                flags.append((cur_arg[2:], None))
    return flags

def _format_op_flags(flags):
    return "\n".join(["  %s" % _format_flag(name, val)
                      for name, val in flags])

def _format_flag(name, val):
    if val is None:
        return "%s: (boolean switch)" % name
    else:
        return "%s: %s" % (name, val)
