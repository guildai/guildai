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

import os

import click

import guild.model
import guild.op
import guild.plugin

from guild import cli
from guild import cmd_impl_support
from guild import deps
from guild import modelfile
from guild import util
from guild import yaml

def main(args):
    model_ref, op_name = _parse_opspec(args.opspec)
    model = _resolve_model(model_ref)
    opdef = _resolve_opdef(op_name, model)
    _dispatch_cmd(args, opdef, model)

def _dispatch_cmd(args, opdef, model):
    if args.help_model:
        _print_model_help(model)
    elif args.help_op:
        _print_op_help(opdef)
    else:
        _dispatch_op_cmd(opdef, model, args)

def _dispatch_op_cmd(opdef, model, args):
    try:
        op = _init_op(opdef, model, args)
    except guild.op.InvalidCmd as e:
        _invalid_cmd_error(e, opdef)
    else:
        if args.print_cmd:
            _print_cmd(op)
        elif args.print_env:
            _print_env(op)
        else:
            _maybe_run(op, model, args)

def _invalid_cmd_error(e, opdef):
    cmd = e.args[0]
    if not cmd:
        cli.error("missing cmd for operation '%s'" % opdef.name)
    else:
        cli.error("invalid cmd '%s' for operation '%s'" % (cmd, opdef.name))

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
    if not model_ref:
        cli.error(
            "a model is required for this operation\n"
            "Try 'guild operations' for a list of model-qualified operations")
    return _resolve_system_model(model_ref)

def _try_resolve_cwd_model(model_ref):
    cwd_modelfile = cmd_impl_support.cwd_modelfile()
    if not cwd_modelfile:
        return None
    path_save = guild.model.get_path()
    guild.model.set_path([cwd_modelfile.dir])
    model = _match_one_model(model_ref, cwd_modelfile)
    guild.model.set_path(path_save)
    return model

def _resolve_system_model(model_ref):
    model = _match_one_model(model_ref)
    if not model:
        _no_model_error(model_ref)
    return model

def _match_one_model(model_ref, cwd_modelfile=None):
    matches = list(_iter_matching_models(model_ref, cwd_modelfile))
    if not matches:
        return None
    elif len(matches) > 1:
        complete_match = _model_by_name(model_ref, matches)
        if complete_match:
            return complete_match
        _multiple_models_error(model_ref, matches)
    else:
        return matches[0]

def _iter_matching_models(model_ref, cwd_modelfile):
    for model in guild.model.iter_models():
        if model_ref is None:
            if cwd_modelfile and _is_default_cwd_model(model, cwd_modelfile):
                yield model
                break
        else:
            if _match_model_ref(model_ref, model):
                yield model

def _is_default_cwd_model(model, cwd_modelfile):
    default_model = cwd_modelfile.default_model
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

def _model_by_name(name, models):
    for model in models:
        if model.name == name:
            return model
    return None

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
        opdef = _try_plugin_opdef(name, model)
    elif opdef.plugin_op:
        opdef = _plugin_opdef(opdef, model)
    if opdef is None:
        _no_such_operation_error(name, model)
    return opdef

def _try_plugin_opdef(parent_opdef_or_name, model):
    if isinstance(parent_opdef_or_name, str):
        plugin_op = modelfile.PluginOp(parent_opdef_or_name)
        parent_opdef = None
    else:
        plugin_op = parent_opdef_or_name.plugin_op
        parent_opdef = parent_opdef_or_name
    for _name, plugin in guild.plugin.iter_plugins():
        opdef = plugin.get_operation(plugin_op, model, parent_opdef)
        if opdef:
            return opdef
    return None

def _plugin_opdef(parent_opdef, model):
    opdef = _try_plugin_opdef(parent_opdef, model)
    if opdef is None:
        cli.error(
            "plugin-op '%s' specified by %s is not defined"
            % (parent_opdef.plugin_op.name, parent_opdef.fullname))
    return opdef

def _no_such_operation_error(name, model):
    cli.error(
        "operation '%s' is not defined for model '%s'\n"
        "Try 'guild operations %s' for a list of available operations."
        % (name, model.name, model.name))

def _init_op(opdef, model, args):
    parsed_args = _parse_args(args.args)
    flag_vals, resource_vals = _split_flags_and_resources(parsed_args, opdef)
    _apply_flag_vals(flag_vals, opdef)
    _validate_opdef_flags(opdef)
    _apply_arg_disable_plugins(args, opdef)
    attrs = _init_op_attrs(args)
    if args.run_dir:
        cli.note(
            "Run directory is '%s' (results will not be visible to Guild)"
            % args.run_dir)
    return guild.op.Operation(model, opdef, args.run_dir, resource_vals, attrs)

def _parse_args(args):
    return dict([_parse_flag(os.path.expanduser(arg)) for arg in args])

def _parse_flag(s):
    parts = s.split("=", 1)
    if len(parts) == 1:
        return parts[0], None
    else:
        return parts[0], _parse_flag_val(parts[1])

def _parse_flag_val(s):
    try:
        return yaml.safe_load(s)
    except yaml.YAMLError:
        return s

def _split_flags_and_resources(vals, opdef):
    ref_vars = _ref_vars_for_resource_lookup(vals, opdef)
    flag_vals = {}
    resource_vals = {}
    for name, val in vals.items():
        if _is_resource(name, opdef, ref_vars):
            resource_vals[name] = str(val)
        else:
            flag_vals[name] = val
    return flag_vals, resource_vals

def _ref_vars_for_resource_lookup(parsed_run_args, opdef):
    ref_vars = {}
    ref_vars.update(opdef.flag_values())
    ref_vars.update(parsed_run_args)
    return util.resolve_all_refs(ref_vars)

def _is_resource(name, opdef, ref_vars):
    for dep in opdef.dependencies:
        resolved_spec = util.resolve_refs(dep.spec, ref_vars, undefined=None)
        if resolved_spec == name:
            return True
    return False

def _apply_flag_vals(vals, opdef):
    for name, val in vals.items():
        opdef.set_flag_value(name, val)

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

def _init_resource_config(args):
    return dict(args.resource_config)

def _init_op_attrs(args):
    return {"label": args.label} if args.label else None

def _print_model_help(model):
    out = click.HelpFormatter()
    out.write_usage(
        "guild",
        "run [OPTIONS] {}:OPERATION [FLAG]...".format(model.modeldef.name))
    if model.modeldef.description:
        out.write_paragraph()
        out.write_text(model.modeldef.description.replace("\n", "\n\n"))
    out.write_paragraph()
    out.write_text(
        "Use 'guild run {}:OPERATION --help-op' for help on "
        "a particular operation.".format(model.modeldef.name))
    ops = _format_model_ops_dl(model)
    if ops:
        _write_dl_section("Operations", ops, out)
    resources = _format_model_resources_dl(model)
    if resources:
        _write_dl_section("Resources", resources, out)
    click.echo(out.getvalue(), nl=False)

def _format_model_ops_dl(model):
    line1 = lambda s: s.split("\n")[0]
    return [
        (op.name, line1(op.description or ""))
        for op in model.modeldef.operations
    ]

def _format_model_resources_dl(model):
    return [(res.name, res.description) for res in model.modeldef.resources]

def _write_dl_section(name, dl, out):
    out.write_paragraph()
    out.write_heading(name)
    out.indent()
    out.write_dl(dl)
    out.dedent()

def _print_op_help(opdef):
    out = click.HelpFormatter()
    out.write_usage(
        "guild",
        "run [OPTIONS] {} [FLAG]...".format(opdef.fullname))
    if opdef.description:
        out.write_paragraph()
        out.write_text(opdef.description.replace("\n", "\n\n"))
    out.write_paragraph()
    out.write_text("Use 'guild run --help' for a list of options.")
    deps = _format_op_deps_dl(opdef)
    if deps:
        _write_dl_section("Dependencies", deps, out)
    flags = _format_op_flags_dl(opdef)
    if flags:
        _write_dl_section("Flags", flags, out)
    click.echo(out.getvalue(), nl=False)

def _format_op_deps_dl(opdef):
    model_resources = {
        res.name: res.description or ""
        for res in opdef.modeldef.resources
    }
    formatted = [
        (dep.spec, _dep_description(dep, model_resources))
        for dep in opdef.dependencies
    ]
    # Show only deps that have descriptions (implicit user interface)
    return [item for item in formatted if item[1]]

def _dep_description(dep, model_resources):
    return dep.description or model_resources.get(dep.spec) or ""

def _format_op_flags_dl(opdef):
    dl = []
    seen = set()
    flags = opdef.flags + opdef.modeldef.flags
    for flag in flags:
        if flag.name in seen:
            continue
        seen.add(flag.name)
        dl.append((flag.name, _format_flag_desc(flag)))
    return dl

def _format_flag_desc(flag):
    if flag.default or flag.required:
        lines = flag.description.split("\n")
        if flag.default:
            suffix = " (default is %r)" % flag.default
        else:
            suffix = " (required)"
        return "\n".join([lines[0] + suffix] + lines[1:])
    else:
        return flag.description

def _print_cmd(op):
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
    flags = util.resolve_all_refs(op.opdef.flag_values(include_none=False))
    resources = op.resource_config
    prompt = (
        "You are about to run %s\n"
        "%s"
        "%s"
        "Continue?"
        % (op_desc, _format_op_flags(flags), _format_op_resources(resources)))
    return guild.cli.confirm(prompt, default=True)

def _format_op_flags(flags):
    if not flags:
        return ""
    return "\n".join([
        "  %s" % _format_flag(name, flags[name])
        for name in sorted(flags)
    ]) + "\n"

def _format_flag(name, val):
    if val is True:
        return "%s: (boolean switch)" % name
    else:
        return "%s: %s" % (name, val)

def _format_op_resources(resources):
    if not resources:
        return ""
    return "\n".join([
        "  %s: %s" % (spec, resources[spec])
        for spec in sorted(resources)
    ]) + "\n"
