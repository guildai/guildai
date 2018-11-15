# Copyright 2017-2018 TensorHub, Inc.
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
import pipes
import re

import click

import guild.help
import guild.model
import guild.op
import guild.plugin

from guild import cli
from guild import click_util
from guild import cmd_impl_support
from guild import deps
from guild import op_util
from guild import util
from guild import var

from . import remote_impl_support
from . import runs_impl

def main(args, ctx):
    _check_opspec_args(args, ctx)
    _apply_restart_or_rerun_args(args, ctx)
    assert args.opspec
    model_ref, op_name = _parse_opspec(args.opspec)
    model = _resolve_model(model_ref)
    opdef = _resolve_opdef(op_name, model)
    _apply_opdef_args(opdef, args)
    _dispatch_cmd(args, opdef, model, ctx)

def _check_opspec_args(args, ctx):
    if not (args.opspec or args.rerun or args.restart):
        cli.error(
            "missing [MODEL:]OPERATION or --rerun/--restart RUN\n"
            "Try 'guild ops' for a list of operations or '%s' "
            "for more information." % click_util.cmd_help(ctx))

def _apply_restart_or_rerun_args(args, ctx):
    if not args.rerun and not args.restart:
        return
    if args.rerun and args.restart:
        cli.error(
            "--rerun and --restart cannot both be used\n"
            "Try '%s' for more information."
            % click_util.cmd_help(ctx))
    if (args.rerun or args.restart) and args.opspec:
        # treat opspec as flag
        args.flags = (args.opspec,) + args.flags
        args.opspec = None
    run, flag_args = _run_args(args.rerun or args.restart, args, ctx)
    args.flags = flag_args + args.flags
    if args.restart:
        cli.out("Restarting {}".format(run.id))
        args.restart = run.id
        args._restart_run = run
    else:
        args.rerun = run.id
        cli.out("Rerunning {}".format(run.id))

def _run_args(run_id_prefix, args, ctx):
    if args.remote:
        run = remote_impl_support.one_run(run_id_prefix, args)
    else:
        run = one_run(run_id_prefix, ctx)
    if not args.opspec:
        args.opspec = "{}:{}".format(run.opref.model_name, run.opref.op_name)
    flag_args = [
        "{}={}".format(name, val)
        for name, val in run.get("flags", {}).items()
        if val is not None
    ]
    return run, tuple(flag_args)

def one_run(run_id_prefix, ctx):
    runs = [
        guild.run.Run(id, path)
        for id, path in var.find_runs(run_id_prefix)
    ]
    run = cmd_impl_support.one_run(runs, run_id_prefix, ctx)
    runs_impl.init_opref_attr(run)
    return run

def _apply_opdef_args(opdef, args):
    if args.set_trace:
        opdef.set_trace = True

def _dispatch_cmd(args, opdef, model, ctx):
    if args.help_model:
        _print_model_help(model)
    elif args.help_op:
        _print_op_help(opdef)
    else:
        _dispatch_op_cmd(opdef, model, args, ctx)

def _dispatch_op_cmd(opdef, model, args, ctx):
    try:
        op = _init_op(opdef, model, args, ctx)
    except guild.op.InvalidMain as e:
        _invalid_main_error(e, opdef)
    else:
        if args.print_cmd:
            _print_cmd(op)
        elif args.print_env:
            _print_env(op)
        elif args.workflow:
            # TEMP facility to dev/test workflow features
            from guild.commands import workflow_impl
            workflow_impl.run(op, args)
        else:
            _maybe_run(op, model, args)

def _invalid_main_error(e, opdef):
    cmd, msg = e.args
    cmd = re.sub(r"\s+", " ", cmd).strip()
    cli.error(
        "invalid main spec '%s' for operation '%s': %s"
        % (cmd, opdef.name, msg))

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
    cwd_guildfile = cmd_impl_support.cwd_guildfile()
    if not cwd_guildfile:
        return None
    path_save = guild.model.get_path()
    guild.model.set_path([cwd_guildfile.dir], clear_cache=True)
    model = _match_one_model(model_ref, cwd_guildfile)
    guild.model.set_path(path_save)
    return model

def _resolve_system_model(model_ref):
    model = _match_one_model(model_ref)
    if not model:
        _no_model_error(model_ref)
    return model

def _match_one_model(model_ref, cwd_guildfile=None):
    matches = list(_iter_matching_models(model_ref, cwd_guildfile))
    if not matches:
        return None
    elif len(matches) > 1:
        complete_match = _model_by_name(model_ref, matches)
        if complete_match:
            return complete_match
        _multiple_models_error(model_ref, matches)
    else:
        return matches[0]

def _iter_matching_models(model_ref, cwd_guildfile):
    for model in guild.model.iter_models():
        if model_ref is None:
            if cwd_guildfile and _is_default_cwd_model(model, cwd_guildfile):
                yield model
                break
        else:
            if _match_model_ref(model_ref, model):
                yield model

def _is_default_cwd_model(model, cwd_guildfile):
    default_model = cwd_guildfile.default_model
    return (default_model and
            default_model.guildfile.dir == model.modeldef.guildfile.dir and
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
        opdef = _maybe_plugin_opdef(name, model.modeldef)
    elif opdef.plugin_op:
        opdef = _plugin_opdef(name, model.modeldef, opdef)
    if opdef is None:
        _no_such_operation_error(name, model)
    return opdef

def _maybe_plugin_opdef(name, modeldef, parent_opdef=None):
    for _name, plugin in guild.plugin.iter_plugins():
        opdef = plugin.get_operation(name, modeldef, parent_opdef)
        if opdef:
            return opdef
    return None

def _plugin_opdef(name, modeldef, parent_opdef):
    opdef = _maybe_plugin_opdef(name, modeldef, parent_opdef)
    if opdef is None:
        cli.error(
            "plugin-op '%s' specified by %s is not defined"
            % (parent_opdef.plugin_op, parent_opdef.fullname))
    return opdef

def _no_such_operation_error(name, model):
    cli.error(
        "operation '%s' is not defined for model '%s'\n"
        "Try 'guild operations %s' for a list of available operations."
        % (name, model.name, model.name))

def _init_op(opdef, model, args, ctx):
    parsed = _parse_args(args)
    flag_vals, resource_vals = _split_flags_and_resources(parsed, opdef)
    _apply_flag_vals(flag_vals, opdef, args.force_flags)
    if not args.force_flags:
        _validate_opdef_flags(opdef)
    _apply_arg_disable_plugins(args, opdef)
    return guild.op.Operation(
        model.reference,
        opdef,
        _op_run_dir(args, ctx),
        resource_vals,
        _op_extra_attrs(args),
        args.stage,
        _op_gpus(args, ctx)
    )

def _parse_args(args):
    try:
        return op_util.parse_flags(args.flags)
    except op_util.ArgValueError as e:
        cli.error("invalid argument '%s' - expected NAME=VAL" % e.arg)

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

def _apply_flag_vals(vals, opdef, force=False):
    for name, val in vals.items():
        flag = opdef.get_flagdef(name)
        if not force and not flag:
            cli.error(
                "unsupported flag '%s'\n"
                "Try 'guild run %s --help-op' for a list of "
                "flags or use --force-flags to skip this check."
                % (name, opdef.fullname))
        try:
            coerced = op_util.coerce_flag_value(val, flag)
        except ValueError as e:
            cli.error(
                "cannot apply %r to flag '%s': %s"
                % (val, name, e))
        else:
            opdef.set_flag_value(name, coerced)

def _validate_opdef_flags(opdef):
    try:
        op_util.validate_opdef_flags(opdef)
    except op_util.MissingRequiredFlags as e:
        _missing_required_flags_error(e)
    except op_util.InvalidFlagChoice as e:
        _invalid_flag_choice_error(e)
    except op_util.InvalidFlagValue as e:
        _invalid_flag_value_error(e)

def _missing_required_flags_error(e):
    cli.out("Operation requires the following missing flags:\n", err=True)
    cli.table(
        [{"name": flag.name, "desc": flag.description} for flag in e.missing],
        ["name", "desc"],
        indent=2,
        err=True)
    cli.out(
        "\nRun the command again with these flags specified as NAME=VAL.",
        err=True)
    cli.error()

def _invalid_flag_choice_error(e):
    cli.out(
        "Unsupported value for '%s' - supported values are:\n"
        % e.flag.name, err=True)
    cli.table(
        [{"val": choice.value, "desc": choice.description}
         for choice in e.flag.choices],
        ["val", "desc"],
        indent=2,
        err=True)
    cli.out("\nRun the command again using one of these options.", err=True)
    cli.error()

def _invalid_flag_value_error(e):
    cli.error("invalid value for '%s': %s" % (e.flag.name, e.msg))

def _apply_arg_disable_plugins(args, opdef):
    if args.disable_plugins:
        opdef.disabled_plugins.extend([
            name.strip() for name in args.disable_plugins.split(",")
        ])

def _init_resource_config(args):
    return dict(args.resource_config)

def _op_extra_attrs(args):
    attrs = {}
    if args.label:
        attrs["label"] = args.label
    if args.no_wait:
        attrs["_no-wait"] = True
    return attrs

def _op_run_dir(args, ctx):
    if args.run_dir and args.restart:
        cli.error(
            "--restart and --run-dir cannot both be used\n"
            "Try '%s' for more information"
            % click_util.cmd_help(ctx))
    if args.run_dir and args.stage:
        cli.error(
            "--stage and --run-dir cannot both be used\n"
            "Try '%s' for more information"
            % click_util.cmd_help(ctx))
    if args.run_dir:
        run_dir = os.path.abspath(args.run_dir)
        if os.getenv("NO_WARN_RUNDIR") != "1":
            cli.note(
                "Run directory is '%s' (results will not be visible to Guild)"
                % run_dir)
        return run_dir
    elif args.restart:
        assert hasattr(args, "_restart_run")
        return args._restart_run.path
    elif args.stage:
        return os.path.abspath(args.stage)
    else:
        return None

def _op_gpus(args, ctx):
    if args.no_gpus and args.gpus:
        cli.error(
            "--gpus and --no-gpus cannot both be used\n"
            "Try '%s' for more information."
            % click_util.cmd_help(ctx))
    if args.no_gpus:
        return ""
    elif args.gpus:
        return args.gpus
    else:
        return None # use all available (default)

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
    out.write_dl(dl, preserve_paragraphs=True)
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
    seen = set()
    flags = []
    for flag in opdef.flags:
        if flag.name in seen:
            continue
        seen.add(flag.name)
        flags.append(flag)
    return guild.help.flags_dl(flags)

def _print_cmd(op):
    formatted = " ".join([
        _maybe_quote_arg(arg)
        for arg in op.cmd_args
        if arg != "guild.op_main"])
    cli.out(formatted)

def _maybe_quote_arg(arg):
    if arg == "" or " " in arg:
        return '"%s"' % arg
    else:
        return arg

def _print_env(op):
    for name, val in sorted(op.cmd_env.items()):
        cli.out("export %s=%s" % (name, val))

def _maybe_run(op, model, args):
    _maybe_warn_no_wait(op.opdef, args)
    if args.yes or _confirm_run(op, model, args):
        _run(op, model, args)

def _run(op, model, args):
    if args.remote:
        args.opspec = "%s:%s" % (model.name, op.opdef.name)
        remote_impl_support.run(args)
    else:
        _check_restart_running(args)
        _run_op(op, args)

def _check_restart_running(args):
    restart_run = getattr(args, "_restart_run", None)
    if restart_run and restart_run.status == "running":
        cli.error(
            "{id} is still running\n"
            "Wait for it to stop or try 'guild stop {id}' "
            "to stop it.".format(id=restart_run.id))

def _run_op(op, args):
    try:
        result = op.run(args.quiet, args.background)
    except deps.DependencyError as e:
        _handle_dependency_error(e)
    else:
        _handle_run_result(result, op)

def _handle_dependency_error(e):
    cli.error(
        "run failed because a dependency was not met: %s" % e)

def _handle_run_result(exit_status, op):
    if op.stage_only:
        _print_staged_info(op)
    elif exit_status != 0:
        cli.error(exit_status=exit_status)

def _print_staged_info(op):
    cmd = " ".join([pipes.quote(arg) for arg in op.cmd_args])
    cli.out(
        "Operation is staged in %s\n"
        "To run the operation, use: "
        "(cd %s && source .guild/env && %s)"
        % (op.run_dir, op.run_dir, cmd)
    )

def _confirm_run(op, model, args):
    if args.stage:
        action = "stage"
    else:
        action = "run"
    op_desc = "%s:%s" % (model.fullname, op.opdef.name)
    if args.remote:
        remote_suffix = " on %s" % args.remote
    else:
        remote_suffix = ""
    flags = util.resolve_all_refs(op.opdef.flag_values(include_none=True))
    resources = op.resource_config
    prompt = (
        "You are about to {action} {op_desc}{remote_suffix}\n"
        "{flags}"
        "{resources}"
        "Continue?"
        .format(
            action=action,
            op_desc=op_desc,
            remote_suffix=remote_suffix,
            flags=_format_op_flags(flags, op.opdef),
            resources=_format_op_resources(resources)))
    return cli.confirm(prompt, default=True)

def _format_op_flags(flags, opdef):
    if not flags:
        return ""
    return "\n".join([
        "  %s" % _format_flag(name, flags[name], opdef)
        for name in sorted(flags)
    ]) + "\n"

def _format_flag(name, val, opdef):
    if val is True:
        formatted = "yes"
    elif val is False:
        formatted = "no"
    elif val is None:
        formatted = _null_label(name, opdef)
    else:
        formatted = str(val)
    return "%s: %s" % (name, formatted)

def _null_label(name, opdef):
    flag = opdef.get_flagdef(name)
    if flag:
        return flag.null_label or "default"
    else:
        return "default"

def _format_op_resources(resources):
    if not resources:
        return ""
    return "\n".join([
        "  %s: %s" % (spec, resources[spec])
        for spec in sorted(resources)
    ]) + "\n"

def _maybe_warn_no_wait(opdef, args):
    if args.no_wait and not (args.remote or opdef.remote):
        cli.note("Operation is local, ignoring --no-wait")
