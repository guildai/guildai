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

import yaml

import guild.model
import guild.op

from guild import cli
from guild import cmd_impl_support
from guild import deps

def main(args):
    model_ref, op_name = _parse_opspec(args.opspec)
    model = _resolve_model(model_ref)
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

def _resolve_model(model_ref):
    model = _try_resolve_cwd_model(model_ref)
    if model:
        return model
    return _resolve_system_model(model_ref)

def _try_resolve_cwd_model(model_ref):
    cwd_modelfile = cmd_impl_support.cwd_modelfile()
    if cwd_modelfile:
        path_save = guild.model.get_path()
        guild.model.set_path([cwd_modelfile.dir])
        model = _match_one_model(model_ref)
        guild.model.set_path(path_save)
        if model:
            return model
    return None

def _resolve_system_model(model_ref):
    model = _match_one_model(model_ref)
    if not model:
        _no_model_error(model_ref)
    return model

def _match_one_model(model_ref):
    matches = list(_iter_matching_models(model_ref))
    if not matches:
        return None
    elif len(matches) > 1:
        _multiple_models_error(model_ref, matches)
    else:
        return matches[0]

def _iter_matching_models(model_ref):
    cwd_modelfile = cmd_impl_support.cwd_modelfile()
    for model in guild.model.iter_models():
        if model_ref is None:
            if _is_default_cwd_model(model, cwd_modelfile):
                yield model
                break
        else:
            if _match_model_ref(model_ref, model):
                yield model

def _is_default_cwd_model(model, cwd_modelfile):
    default_model = cwd_modelfile and cwd_modelfile.default_model
    return (default_model and
            default_model.modelfile.dir == model.modeldef.modelfile.dir and
            default_model.name == model.name)

def _match_model_ref(model_ref, model):
    if "/" in model_ref:
        # If user includes a '/' assume it's a complete name
        return model_ref == model.fullname
    else:
        # otherwise treat as a match term
        return model_ref in model.name

def _no_model_error(model_ref):
    if model_ref is None:
        cli.error(
            "there are no models in %s\n"
            "Try a different directory or 'guild operations' for "
            "available operations."
            % cmd_impl_support.cwd_desc())
    else:
        cli.error(
            "cannot find a model matching '%s'\n"
            "Try 'guild models' for a list of available models."
            % model_ref)

def _multiple_models_error(model_ref, models):
    models_list = "\n".join([
        "  %s" % name
        for name in sorted([m.fullname for m in models])
    ])
    cli.error(
        "there are multiple models that match '%s'\n"
        "Try specifying one of the following:\n"
        "%s"
        % (model_ref, models_list))

def _resolve_opdef(name, model):
    opdef = model.modeldef.get_operation(name)
    if opdef is None:
        _no_such_operation_error(name, model)
    return opdef

def _no_such_operation_error(name, model):
    cli.error(
        "operation '%s' is not defined for model '%s'\n"
        "Try 'guild operations %s' for a list of available operations."
        % (name, model.name, model.name))

def _init_op(opdef, model, args):
    _apply_arg_flags(args, opdef)
    _validate_opdef_flags(opdef)
    _apply_arg_disable_plugins(args, opdef)
    attrs = {"label": args.label} if args.label else None
    if args.run_dir:
        cli.note(
            "Run directory is '%s' (results will not be visible to Guild)"
            % args.run_dir)
    return guild.op.Operation(model, opdef, args.run_dir, attrs)

def _apply_arg_flags(args, opdef):
    for arg in args.args:
        name, val = _parse_flag(arg)
        opdef.set_flag_value(name, val)

def _parse_flag(s):
    parts = s.split("=", 1)
    if len(parts) == 1:
        return parts[0], None
    else:
        return parts[0], _parse_flag_val(parts[1])

def _parse_flag_val(s):
    try:
        return yaml.load(s)
    except yaml.YAMLError:
        return s

def _validate_opdef_flags(opdef):
    vals = opdef.flag_values()
    _check_missing_flag_vals(vals, opdef)
    _check_valid_flag_vals(vals, opdef)

def _check_missing_flag_vals(vals, opdef):
    missing = _missing_flag_vals(vals, opdef)
    if missing:
        _missing_required_flags_error(missing)

def _missing_flag_vals(vals, opdef):
    return [flag for flag in opdef.flags
            if flag.required and not vals.get(flag.name)]

def _missing_required_flags_error(missing):
    cli.out("Operation requires the following missing flags:\n", err=True)
    cli.table(
        [{"name": flag.name, "desc": flag.description} for flag in missing],
        ["name", "desc"],
        indent=2,
        err=True)
    cli.out(
        "\nRun the command again with these flags specified as NAME=VAL.",
        err=True)
    cli.error()

def _check_valid_flag_vals(vals, opdef):
    for flag in opdef.flags:
        val = vals.get(flag.name)
        if (val and flag.options and
            val not in [opt.value for opt in flag.options]):
            _invalid_flag_value_error(flag)

def _invalid_flag_value_error(flag):
    cli.out(
        "Unsupported value for '%s' - supported values are:\n"
        % flag.name, err=True)
    cli.table(
        [{"val": opt.value, "desc": opt.description}
         for opt in flag.options],
        ["val", "desc"],
        indent=2,
        err=True)
    cli.out("\nRun the command again using one of these options.", err=True)
    cli.error()

def _apply_arg_disable_plugins(args, opdef):
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
        _run(op)

def _run(op):
    try:
        result = op.run()
    except deps.DependencyError as e:
        _handle_dependency_error(e)
    else:
        _handle_run_result(result)

def _handle_dependency_error(e):
    cli.error(
        "run failed because a dependency was not met: %s" % e)

def _handle_run_result(exit_status):
    if exit_status != 0:
        cli.error(exit_status=exit_status)

def _confirm_run(op, model):
    op_desc = "%s:%s" % (model.fullname, op.opdef.name)
    flags = op.opdef.flag_values(include_none=False)
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

def _format_op_flags(flags):
    return "\n".join([
        "  %s" % _format_flag(name, flags[name])
        for name in sorted(flags)
    ])

def _format_flag(name, val):
    if val is True:
        return "%s: (boolean switch)" % name
    else:
        return "%s: %s" % (name, val)
