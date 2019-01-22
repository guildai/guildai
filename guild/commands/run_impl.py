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

import csv
import logging
import os
import pipes

import click
import yaml

import guild.help
import guild.op
import guild.plugin

from guild import cli
from guild import click_util
from guild import cmd_impl_support
from guild import deps
from guild import model as modellib
from guild import model_proxies
from guild import op_util
from guild import resolver
from guild import run as runlib
from guild import util
from guild import var

from . import remote_impl_support
from . import runs_impl

log = logging.getLogger("guild")

###################################################################
# Main
###################################################################

def main(args):
    _maybe_shift_opspec(args)
    _apply_restart_or_rerun_args(args)
    model, op_name = _resolve_model_op(args.opspec)
    opdef = _resolve_opdef(model, op_name)
    _dispatch_cmd(args, opdef)

def _maybe_shift_opspec(args):
    """Moves opspec to flags if it looks like a flag assignment.
    """
    if args.opspec and "=" in args.opspec:
        args.flags = (args.opspec,) + args.flags
        args.opspec = None

###################################################################
# Apply args from existing runs (restart/rerun)
###################################################################

def _apply_restart_or_rerun_args(args):
    if not args.rerun and not args.restart:
        return
    _check_restart_rerun_args(args)
    run = _find_run(args.restart or args.rerun, args)
    _apply_run_args(run, args)
    if args.restart:
        if os.getenv("NO_RESTARTING_MSG") != "1":
            cli.out("Restarting {}".format(run.id))
        args.restart = run.id
        args._restart_run = run
    else:
        cli.out("Rerunning {}".format(run.id))
        args.rerun = run.id

def _check_restart_rerun_args(args):
    if args.rerun and args.restart:
        cli.error(
            "--rerun and --restart cannot both be used\n"
            "Try 'guild run --help' for more information.")

def _find_run(run_id_prefix, args):
    if args.remote:
        return remote_impl_support.one_run(run_id_prefix, args)
    else:
        return one_run(run_id_prefix)

def _apply_run_args(run, args):
    if _is_batch_run(run):
        _apply_batch_run_args(run, args)
    else:
        _apply_normal_run_args(run, args)

def _is_batch_run(run):
    return os.path.exists(run.guild_path("proto"))

def _apply_batch_run_args(run, args):
    _apply_batch_opspec(run, args)
    _apply_batch_proto_args(run, args)

def _apply_batch_opspec(run, args):
    batch_opspec, child_opspec = run.opref.op_name.split("+", 1)
    args.opspec = child_opspec
    args.optimizer = batch_opspec

def _apply_batch_proto_args(batch_run, args):
    proto_path = batch_run.guild_path("proto")
    assert os.path.exists(proto_path), proto_path
    proto = runlib.Run("", proto_path)
    _apply_run_flags(proto.get("flags", {}), args)

def _apply_run_flags(flags, args):
    # Prepend run flag args to user provided args - last values take
    # precedence in processing later
    args.flags = _flag_args(flags) + args.flags

def _flag_args(flags):
    return tuple([
        "{}={}".format(name, val)
        for name, val in sorted(flags.items())
        if val is not None
    ])

def _apply_normal_run_args(run, args):
    _apply_run_opspec(run, args)
    _apply_run_flags(run.get("flags", {}), args)

def _apply_run_opspec(run, args):
    args.opspec = run.opref.to_opspec()

def one_run(run_id_prefix):
    runs = [
        runlib.Run(id, path)
        for id, path in var.find_runs(run_id_prefix)
    ]
    return cmd_impl_support.one_run(runs, run_id_prefix)

###################################################################
# Model op (model, op_name tuple) from opspec
###################################################################

def _resolve_model_op(opspec):
    proxy_model_op = _proxy_model_op(opspec)
    try:
        model, op_name = _model_op(opspec)
    except SystemExit:
        # SystemExit raised by default model resolution process
        # (e.g. cli.error message). Before exiting, check for a model
        # proxy based on opspec (e.g. a local script). We do this to
        # give priority to Guild file defined operations over proxies.
        if proxy_model_op:
            return proxy_model_op
        raise
    else:
        # We have a model via the default lookup process, but it might
        # not have op_name operation or a default operation. If we
        # can't find an op matching op_name or a default op AND we
        # have a proxy_model_op, return proxy_model_op.
        opdef = (
            model.modeldef.get_operation(op_name) if op_name
            else model.modeldef.default_operation)
        if not opdef and proxy_model_op:
            return proxy_model_op
        if not opdef:
            _no_such_op_error(opspec)
        return model, opdef.name

def _proxy_model_op(opspec):
    if not opspec:
        return None
    try:
        return model_proxies.resolve_model_op(opspec)
    except model_proxies.NotSupported:
        return None

def _model_op(opspec):
    model_ref, op_name = _parse_opspec(opspec)
    model = _resolve_model(model_ref)
    if not model:
        _no_such_op_error(opspec)
    return model, op_name

def _parse_opspec(spec):
    if not spec:
        return None, None
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
        return None
    return _resolve_system_model(model_ref)

def _try_resolve_cwd_model(model_ref):
    cwd_guildfile = cmd_impl_support.cwd_guildfile()
    if not cwd_guildfile:
        return None
    path_save = modellib.get_path()
    modellib.set_path([cwd_guildfile.dir], clear_cache=True)
    model = _match_one_model(model_ref, cwd_guildfile)
    modellib.set_path(path_save)
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
    for model in modellib.iter_models():
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

def _no_such_op_error(opspec):
    if opspec:
        if ":" in opspec:
            cli.error(
                "cannot find operation %s\n"
                "Try 'guild operations' for a list of available operations."
                % opspec)
        else:
            cli.error(
                "cannot find operation %s\n"
                "You may need to include a model in the form MODEL:OPERATION. "
                "Try 'guild operations' for a list of available operations."
                % opspec)
    else:
        cli.error(
            "cannot find a default operation\n"
            "Try 'guild operations' for a list.")

###################################################################
# Opdef from model op (model, op_name tuple)
###################################################################

def _resolve_opdef(model, op_name):
    opdef = model.modeldef.get_operation(op_name)
    if opdef is None:
        opdef = _maybe_plugin_opdef(op_name, model.modeldef)
    elif opdef.plugin_op:
        opdef = _plugin_opdef(op_name, model.modeldef, opdef)
    if opdef is None:
        _no_such_operation_error(op_name, model)
    opdef.set_modelref(model.reference)
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

###################################################################
# Dispatch cmd
###################################################################

def _dispatch_cmd(args, opdef):
    if args.help_model:
        _print_model_help(opdef.modeldef)
    elif args.help_op:
        _print_op_help(opdef)
    else:
        _dispatch_op_cmd(opdef, args)

###################################################################
# Model help
###################################################################

def _print_model_help(modeldef):
    out = click.HelpFormatter()
    out.write_usage(
        "guild",
        "run [OPTIONS] {}:OPERATION [FLAG]...".format(modeldef.name))
    if modeldef.description:
        out.write_paragraph()
        out.write_text(modeldef.description.replace("\n", "\n\n"))
    out.write_paragraph()
    out.write_text(
        "Use 'guild run {}:OPERATION --help-op' for help on "
        "a particular operation.".format(modeldef.name))
    ops = _format_model_ops_dl(modeldef)
    if ops:
        _write_dl_section("Operations", ops, out)
    resources = _format_model_resources_dl(modeldef)
    if resources:
        _write_dl_section("Resources", resources, out)
    click.echo(out.getvalue(), nl=False)

def _format_model_ops_dl(modeldef):
    line1 = lambda s: s.split("\n")[0]
    return [
        (op.name, line1(op.description or ""))
        for op in modeldef.operations
    ]

def _format_model_resources_dl(modeldef):
    return [(res.name, res.description) for res in modeldef.resources]

def _write_dl_section(name, dl, out):
    out.write_paragraph()
    out.write_heading(name)
    out.indent()
    out.write_dl(dl, preserve_paragraphs=True)
    out.dedent()

###################################################################
# Op help
###################################################################

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

###################################################################
# Op command
###################################################################

def _dispatch_op_cmd(opdef, args):
    op = _init_op(opdef, args)
    if args.print_cmd:
        _print_cmd(op)
    elif args.print_env:
        _print_env(op)
    elif args.print_trials or args.save_trials:
        _print_or_save_trials(op, args)
    else:
        _maybe_run(op, args)

###################################################################
# Init op
###################################################################

def _init_op(opdef, args):
    (flag_vals,
     resource_config,
     batch_files) = _split_flag_args(args.flags, opdef)
    _apply_opdef_args(flag_vals, args, opdef)
    try:
        op = guild.op.Operation(
            opdef,
            _op_run_dir(args),
            resource_config,
            _op_extra_attrs(args),
            bool(args.stage),
            _op_gpus(args)
        )
    except guild.op.InvalidOpSpec as e:
        _invalid_op_spec_error(e, opdef)
    else:
        _apply_batch_op(op, batch_files, args)
        return op

def _split_flag_args(flag_args, opdef):
    batch_files, rest_args = _split_batch_files(flag_args)
    assigns = _parse_assigns(rest_args)
    flags, resources = _split_flags_and_resources(assigns, opdef)
    return flags, resources, batch_files

def _split_batch_files(flag_args):
    batch_files = []
    rest = []
    for arg in flag_args:
        if arg[:1] == "@":
            batch_files.append(arg[1:])
        else:
            rest.append(arg)
    return batch_files, rest

def _parse_assigns(assign_args):
    try:
        return op_util.parse_flags(assign_args)
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

###################################################################
# Update opdef with flag vals and applicable args
###################################################################

def _apply_opdef_args(flag_vals, args, opdef):
    _apply_flag_vals(flag_vals, opdef, args.force_flags)
    if not args.force_flags:
        _validate_opdef_flags(opdef)
    _apply_arg_disable_plugins(args, opdef)
    opdef.set_trace = args.set_trace

def _apply_flag_vals(vals, opdef, force):
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
    cli.out(
        "Operation requires the following missing flags:\n",
        err=True)
    cli.table(
        [{"name": flag.name, "desc": flag.description}
         for flag in e.missing],
        ["name", "desc"],
        indent=2,
        err=True)
    cli.out(
        "\nRun the command again with these flags specified "
        "as NAME=VAL.", err=True)
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
    cli.out(
        "\nRun the command again using one of these options.",
        err=True)
    cli.error()

def _invalid_flag_value_error(e):
    cli.error("invalid value for '%s': %s" % (e.flag.name, e.msg))

def _apply_arg_disable_plugins(args, opdef):
    if args.disable_plugins:
        opdef.disable_plugins.extend([
            name.strip() for name in args.disable_plugins.split(",")
        ])

###################################################################
# Other op attrs
###################################################################

def _op_run_dir(args):
    if args.run_dir and args.restart:
        cli.error(
            "--restart and --run-dir cannot both be used\n"
            "Try 'guild run --help' for more information")
    if args.run_dir and args.stage:
        cli.error(
            "--stage and --run-dir cannot both be used\n"
            "Try 'guild run --help' for more information")
    if args.run_dir:
        run_dir = os.path.abspath(args.run_dir)
        if os.getenv("NO_WARN_RUNDIR") != "1":
            cli.note(
                "Run directory is '%s' (results will not be "
                "visible to Guild)" % run_dir)
        return run_dir
    elif args.restart:
        assert hasattr(args, "_restart_run")
        return args._restart_run.path
    elif args.stage:
        return os.path.abspath(args.stage)
    else:
        return None

def _op_extra_attrs(args):
    attrs = {}
    if args.label:
        attrs["label"] = args.label
    if args.no_wait:
        attrs["_no_wait"] = True
    if args.max_trials is not None:
        attrs["_max_trials"] = args.max_trials
    if args.random_seed is not None:
        attrs["_random_seed"] = args.random_seed
    return attrs

def _op_gpus(args):
    if args.no_gpus and args.gpus is not None:
        cli.error(
            "--gpus and --no-gpus cannot both be used\n"
            "Try 'guild run --help' for more information.")
    if args.no_gpus:
        return ""
    elif args.gpus is not None:
        return args.gpus
    return None # use all available (default)

def _invalid_op_spec_error(e, opdef):
    cli.error("operation '%s' is not valid: %s" % (opdef.fullname, e))

###################################################################
# Batch op init
###################################################################

def _apply_batch_op(op, batch_files, args):
    """Applies batch_op attr to op.

    If we determine this is a batch run, resolve the batch opspec to
    an operation in its own right and set it as op.batch_op. This is
    used downstream to run the batch op as a parent of op.

    If we determine this is not a batch run, op.batch_op is None.
    """
    batch_opspec = _batch_opspec(op, batch_files, args)
    if not batch_opspec:
        op.batch_op = None
        return
    batch_opdef = _resolve_batch_opdef(batch_opspec)
    batch_args = _batch_op_init_args(batch_opdef, args)
    batch_op = _init_batch_op(batch_opdef, batch_args, batch_files)
    op.batch_op = batch_op

def _batch_opspec(op, batch_files, args):
    if args.optimizer:
        return args.optimizer
    if batch_files or _has_batch_flag_vals(op):
        return "+"
    return None

def _has_batch_flag_vals(op):
    for val in op.flag_vals.values():
        if isinstance(val, list):
            return True
    return False

def _resolve_batch_opdef(batch_opspec):
    try:
        model, op_name = _resolve_model_op(batch_opspec)
    except SystemExit as e:
        assert e.args[0].startswith("cannot find operation"), e
        cli.error(
            "cannot find optimizer %r\n"
            "Refer to Guild AI documentation for supported optimizers or "
            "verify a custom optimizer by running " "'guild operations'."
            % batch_opspec)
    else:
        return _resolve_opdef(model, op_name)

def _batch_op_init_args(opdef, args):
    """Returns run args suitable for initializing a batch op."""
    params = args.as_kw()
    params["opspec"] = opdef.opref.to_opspec()
    params["flags"] = params["opt_flags"]
    params["opt_flags"] = ()
    params["yes"] = True
    params["restart"] = None
    params["rerun"] = None
    params["optimizer"] = None
    params["needed"] = False
    params["minimize"] = None
    params["maximize"] = None
    args = click_util.Args(**params)
    return args

def _init_batch_op(opdef, args, batch_files):
    op = _init_op(opdef, args)
    op.batch_files = batch_files
    return op

###################################################################
# Print op cmd
###################################################################

def _print_cmd(op):
    formatted = " ".join(_preview_cmd(op))
    cli.out(formatted)

def _preview_cmd(op):
    return [pipes.quote(arg) for arg in op.cmd_args]

###################################################################
# Print op env
###################################################################

def _print_env(op):
    for name, val in sorted(op.cmd_env.items()):
        cli.out("export %s=%s" % (name, val))

###################################################################
# Print trials
###################################################################

def _print_or_save_trials(op, args):
    if op.batch_op:
        _print_or_save_batch_trials(op, args)
    else:
        _print_or_save_one_trial(op, args)

def _print_or_save_batch_trials(op, args):
    with util.TempDir() as batch_run_dir:
        op.set_run_dir(batch_run_dir)
        _init_batch_run(op)
        if args.print_trials:
            op.batch_op.cmd_env["PRINT_TRIALS"] = "1"
        else:
            assert args.save_trials
            op.batch_op.cmd_env["SAVE_TRIALS"] = args.save_trials
        _run_op(op.batch_op, args)

def _print_or_save_one_trial(op, args):
    flag_vals = op.opdef.flag_values(include_none=True)
    if args.print_trials:
        op_util.print_trials([flag_vals])
    else:
        assert args.save_trials
        cli.out("Saving 1 trial to %s" % args.save_trials)
        op_util.save_trials([flag_vals], args.save_trials)

###################################################################
# Prompt user and run
###################################################################

def _maybe_run(op, args):
    _maybe_warn_no_wait(op.opdef, args)
    if args.yes or _confirm_run(op, args):
        _run(op, args)

def _maybe_warn_no_wait(opdef, args):
    if args.no_wait and not (args.remote or opdef.remote):
        cli.note("Operation is local, ignoring --no-wait")

###################################################################
# Run confirmation prompt
###################################################################

def _confirm_run(op, args):
    prompt = (
        "You are about to {action} {op_desc}{opt_suffix}{remote_suffix}\n"
        "{flags}"
        "{resources}"
        "Continue?"
        .format(
            action=_action_desc(args),
            op_desc=_op_desc(op),
            opt_suffix=_opt_suffix(args),
            remote_suffix=_remote_suffix(args),
            flags=_format_op_flags(op),
            resources=_format_op_resources(op.resource_config)))
    return cli.confirm(prompt, default=True)

def _action_desc(args):
    if args.stage:
        return "stage"
    return "run"

def _op_desc(op):
    return op.opref.to_opspec()

def _opt_suffix(args):
    if not args.optimizer:
        return ""
    parts = [" with %s optimizer" % args.optimizer]
    if args.max_trials:
        parts.append(
            " for %i %s" %
            (args.max_trials,
             "trials" if args.max_trials > 1 else "trial"))
    return "".join(parts)

def _remote_suffix(args):
    if args.remote:
        return " on %s" % args.remote
    return ""

def _format_op_flags(op):
    flags = util.resolve_all_refs(op.opdef.flag_values(include_none=True))
    if not flags:
        return ""
    return "\n".join([
        "  %s" % _format_flag(name, flags[name], op.opdef)
        for name in sorted(flags)
    ]) + "\n"

def _format_flag(name, val, opdef):
    if val is None:
        formatted = _null_label(name, opdef)
    else:
        formatted = op_util.format_flag_val(val, use_nulls=True)
    return "%s: %s" % (name, formatted)

def _null_label(name, opdef):
    flag = opdef.get_flagdef(name)
    if flag and flag.null_label is not None:
        return op_util.format_flag_val(flag.null_label)
    return "default"

def _format_op_resources(resources):
    if not resources:
        return ""
    return "\n".join([
        "  %s: %s" % (spec, resources[spec])
        for spec in sorted(resources)
    ]) + "\n"

###################################################################
# Run dispatch - remote or local
###################################################################

def _run(op, args):
    if args.remote:
        _check_remote_batch_files(op)
        _run_remote(op, args)
    else:
        _run_local(op, args)

def _check_remote_batch_files(op):
    if op.batch_op.batch_files:
        cli.error("batch files are not supported with remote operations")

def _run_remote(op, args):
    args.opspec = op.opref.to_opspec()
    remote_impl_support.run(args)

###################################################################
# Run dispatch - batch or non-batch
###################################################################

def _run_local(op, args):
    if op.batch_op:
        _run_batch(op, args)
    else:
        _run_normal(op, args)

###################################################################
# Batch run
###################################################################

def _run_batch(op, args):
    _init_batch_run(op)
    return _run_op(op.batch_op, args)

def _init_batch_run(op):
    batches = _batches_attr(op.batch_op.batch_files)
    run = guild.op.init_run(op.run_dir)
    run.init_skel()
    op.batch_op.set_run_dir(run.path)
    _write_batch_proto(run, op, batches)

def _batches_attr(batch_files):
    batches = []
    for path in batch_files:
        batches.extend(_read_batches(path))
    return batches

def _read_batches(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in (".json", ".yml", ".yaml"):
        return _yaml_batches(path)
    elif ext in (".csv",):
        return _csv_batches(path)
    else:
        cli.error(
            "unsupported batch file extension for %s"
            % path)

def _yaml_batches(path):
    data = yaml.safe_load(open(path, "r"))
    if not isinstance(data, list):
        cli.error(
            "unsupported data type for batch file %s: %s"
            % (path, type(data)))
    for item in data:
        if not isinstance(item, dict):
            cli.error(
                "supported data for batch file %s trial: %r"
                % item)
    return data

def _csv_batches(path):
    reader = csv.reader(open(path, "r"))
    try:
        flag_names = next(reader)
    except StopIteration:
        return []
    else:
        return [
            dict(zip(flag_names, _flag_vals(row)))
            for row in reader
        ]

def _flag_vals(row):
    return [op_util.parse_arg_val(s) for s in row]

def _write_batch_proto(batch_run, proto_op, batches):
    proto_op.set_run_dir(batch_run.guild_path("proto"))
    proto_op.init()
    if batches:
        proto_op.write_run_attr("batches", batches)


###################################################################
# Non-batch run
###################################################################


def _run_normal(op, args):
    _check_needed(op, args)
    _check_restart_running(args)
    _run_op(op, args)

def _check_needed(op, args):
    if not args.needed:
        return
    matching = _find_matching_runs(op)
    if matching:
        cli.out(
            "Skipping because the following runs match "
            "this operation (--needed specified):")
        _print_matching_runs(matching)
        raise SystemExit(0)

def _find_matching_runs(op):
    return [
        run for run in resolver.matching_runs([op.opref])
        if _match_run_flags(run, op.flag_vals)
    ]

def _match_run_flags(run, target):
    run_flags = run.get("flags")
    log.debug(
        "comparing run %s flags %r to target %r",
        run.id, run_flags, target)
    return run_flags == target

def _print_matching_runs(runs):
    formatted = [runs_impl.format_run(run) for run in runs]
    cols = [
        "index", "operation", "started",
        "status_with_remote", "label"
    ]
    cli.table(formatted, cols=cols, indent=2)

def _check_restart_running(args):
    restart_run = getattr(args, "_restart_run", None)
    if restart_run and restart_run.status == "running":
        cli.error(
            "{id} is still running\n"
            "Wait for it to stop or try 'guild stop {id}' "
            "to stop it.".format(id=restart_run.id))

###################################################################
# Run op process
###################################################################

def _run_op(op, args):
    try:
        returncode = op.run(
            args.quiet,
            _op_pidfile(args),
            args.stop_after)
    except deps.DependencyError as e:
        _handle_dependency_error(e)
    except guild.op.ProcessError as e:
        _handle_process_error(e)
    else:
        _handle_run_exit(returncode, op)

def _op_pidfile(args):
    if args.pidfile:
        return args.pidfile
    elif args.background:
        with util.TempFile("guild-pid-", keep=True) as pidfile:
            return pidfile
    else:
        return None

def _handle_dependency_error(e):
    cli.error(
        "run failed because a dependency was not met: %s" % e)

def _handle_process_error(e):
    cli.error("run failed: %s" % e)

def _handle_run_exit(returncode, op):
    if op.stage_only:
        _print_staged_info(op)
    elif returncode != 0:
        cli.error(exit_status=returncode)

def _print_staged_info(op):
    cmd = " ".join(_preview_cmd(op))
    cli.out(
        "Operation is staged in %s\n"
        "To run the operation, use: "
        "(cd %s && source .guild/env && %s)"
        % (op.run_dir, op.run_dir, cmd)
    )
