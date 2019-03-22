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
import random

import click
import six
import yaml

import guild.help
import guild.op
import guild.plugin

from guild import cli
from guild import click_util
from guild import cmd_impl_support
from guild import deps
from guild import guildfile
from guild import model as modellib
from guild import model_proxy
from guild import op_util
from guild import opref as opreflib
from guild import resolver
from guild import run as runlib
from guild import util
from guild import var

from . import remote_impl_support
from . import runs_impl

log = logging.getLogger("guild")

# Use Bayesian with gaussian process as default optimizer when opdef
# does not contain any optimizers.
#
DEFAULT_OPTIMIZER = "gp"

###################################################################
# Main
###################################################################

def main(args):
    _maybe_shift_opspec(args)
    _validate_args(args)
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
# Validate run args
###################################################################

def _validate_args(args):
    if args.rerun and args.restart:
        cli.error(
            "--rerun and --restart cannot both be used\n"
            "Try 'guild run --help' for more information.")
    if args.run_dir and args.restart:
        cli.error(
            "--restart and --run-dir cannot both be used\n"
            "Try 'guild run --help' for more information")
    if args.run_dir and args.stage:
        cli.error(
            "--stage and --run-dir cannot both be used\n"
            "Try 'guild run --help' for more information")
    if args.no_gpus and args.gpus is not None:
        cli.error(
            "--gpus and --no-gpus cannot both be used\n"
            "Try 'guild run --help' for more information.")
    if args.print_trials and args.init_trials:
        cli.error(
            "--print-trials and --init-trials cannot both be used\n"
            "Try 'guild run --help' for more information.")
    if args.minimize and args.maximize:
        cli.error(
            "--minimize and --maximize cannot both be used\n"
            "Try 'guild run --help' for more information.")
    if args.optimize and args.optimizer:
        cli.error(
            "--optimize and --optimizer cannot both be used\n"
            "Try 'guild run --help' for more information.")

###################################################################
# Apply args from existing runs (restart/rerun)
###################################################################

def _apply_restart_or_rerun_args(args):
    if not args.rerun and not args.restart:
        return
    assert not (args.rerun and args.restart)
    run = _find_run(args.restart or args.rerun, args)
    _apply_run_args(run, args)
    run_desc = _run_desc_for_restart(run)
    if args.restart:
        if not args.quiet and os.getenv("NO_RESTARTING_MSG") != "1":
            cli.out("Restarting {}".format(run_desc))
        args.restart = run.id
        args._restart_run = run
    else:
        cli.out("Rerunning {}".format(run_desc))
        args.rerun = run.id

def _run_desc_for_restart(run):
    rel_to_runs_dir = os.path.relpath(run.path, var.runs_dir())
    if rel_to_runs_dir == run.id:
        return run.id
    return "run in %s" % run.path

def _find_run(run_spec, args):
    if args.remote:
        return remote_impl_support.one_run(run_spec, args)
    else:
        return util.find_apply([
            _run_from_dir,
            _marked_or_latest_run_from_spec,
            one_run,
        ], run_spec)

def _run_from_dir(run_dir):
    if not os.path.isdir(run_dir):
        return None
    run_id = os.path.basename(run_dir)
    return runlib.Run(run_id, run_dir)

def _marked_or_latest_run_from_spec(spec):
    try:
        opref = opreflib.OpRef.from_string(spec)
    except opreflib.OpRefError:
        return None
    else:
        return resolver.marked_or_latest_run([opref])

def one_run(run_id_prefix):
    runs = [
        runlib.Run(id, path)
        for id, path in var.find_runs(run_id_prefix)
    ]
    return cmd_impl_support.one_run(runs, run_id_prefix)

def _apply_run_args(run, args):
    if _is_batch_run(run):
        _apply_batch_run_args(run, args)
    else:
        _gen_apply_run_args(run, args)

def _is_batch_run(run):
    return os.path.exists(run.guild_path("proto"))

def _apply_batch_run_args(run, args):
    proto_path = run.guild_path("proto")
    if not os.path.exists(proto_path):
        cli.error(
            "cannot find operation proto in %s"
            % proto_path)
    proto = runlib.Run("", proto_path)
    _gen_apply_run_args(proto, args)
    if not args.optimizer:
        args.optimizer = run.opref.to_opspec()

def _gen_apply_run_args(run, args):
    _apply_run_params(run, args)
    _apply_run_opspec(run, args)
    _apply_run_flags(run, args)
    _apply_run_random_seed(run, args)

def _apply_run_params(run, args):
    """Loads applicable run params attr and applies them to args.

    A run param value is applied only the current value in arg is
    equal to the default value for the run command.
    """
    run_params = op_util.run_params_for_restart(run, args.as_kw())
    for name, val in run_params.items():
        # Special handling for mutually exclusive args
        if ((name == "no_gpus" and args.gpus) or
            (name == "gpus" and args.no_gpus)):
            continue
        # args repeated params are tuples so restore as expected.
        if isinstance(val, list):
            val = tuple(val)
        setattr(args, name, val)

def _apply_run_opspec(run, args):
    args.opspec = run.opref.to_opspec()

def _apply_run_flags(run, args):
    flags = run.get("flags", {})
    # Prepend run flag args to user provided args - last values take
    # precedence in processing later
    args.flags = _flag_args(flags) + args.flags

def _flag_args(flags):
    return tuple([
        op_util.format_flag_arg(name, val)
        for name, val in sorted(flags.items())
        if val is not None
    ])

def _apply_run_random_seed(run, args):
    if args.random_seed is None:
        args.random_seed = run.get("random_seed")

###################################################################
# Model op (model, op_name tuple) from opspec
###################################################################

def _resolve_model_op(opspec):
    try:
        model, op_name = _model_op(opspec)
    except SystemExit:
        # SystemExit raised by default model resolution process
        # (e.g. cli.error message). Before exiting, check for a model
        # proxy based on opspec (e.g. a local script). We do this to
        # give priority to Guild file defined operations over proxies.
        proxy_model_op = _proxy_model_op(opspec)
        if proxy_model_op:
            return proxy_model_op
        raise
    else:
        # We have a model via the default lookup process, but it might
        # not have op_name operation or a default operation. If we
        # can't find an op matching op_name or a default op try
        # proxy_model_op. Otherwise error.
        opdef = (
            model.modeldef.get_operation(op_name) if op_name
            else model.modeldef.default_operation)
        if opdef:
            return model, opdef.name
        proxy_model_op = _proxy_model_op(opspec)
        if proxy_model_op:
            return proxy_model_op
        _no_such_op_error(opspec)

def _proxy_model_op(opspec):
    if not opspec:
        return None
    try:
        return model_proxy.resolve_model_op(opspec)
    except model_proxy.NotSupported:
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
        _no_such_operation_error(op_name, model)
    opdef.set_modelref(model.reference)
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
        _print_cmd(op, args)
    elif args.print_env:
        _print_env(op)
    elif args.print_trials or args.save_trials:
        _print_or_save_trials(op, args)
    else:
        _maybe_run(op, args)

###################################################################
# Init op
###################################################################

def _init_op(opdef, args, is_batch=False):
    (flag_vals,
     resource_config,
     batch_files) = _split_flag_args(args.flags, opdef)
    _apply_opdef_args(flag_vals, batch_files, args, opdef, is_batch)
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
    except guild.op.OpInitError as e:
        _op_init_error(e, opdef)
    else:
        _apply_batch_op(opdef.batch_opspec, batch_files, flag_vals, args, op)
        if not op.batch_op and not args.force_flags:
            _validate_op_flags(op)
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
        resolved_spec = util.resolve_refs(dep.name, ref_vars, undefined=None)
        if resolved_spec == name:
            return True
    return False

###################################################################
# Update opdef with flag vals and applicable args
###################################################################

def _apply_opdef_args(flag_vals, batch_files, args, opdef, is_batch):
    _apply_optimizer(flag_vals, opdef, args)
    _apply_flag_vals(flag_vals, opdef, args)
    _apply_arg_disable_plugins(args, opdef)
    _apply_arg_objective(args, opdef)
    _apply_arg_set_trace(args, opdef)
    if not is_batch:
        opdef.batch_opspec = _batch_opspec(flag_vals, batch_files, args)
    else:
        opdef.batch_opspec = None

def _apply_optimizer(flag_vals, opdef, args):
    if args.optimizer:
        _apply_named_optimizer(args.optimizer, opdef, args)
    elif args.optimize:
        _apply_default_optimizer(opdef, args)
    else:
        _maybe_apply_random_optimizer(flag_vals, args)

def _apply_named_optimizer(opt_name, opdef, args):
    optdef = opdef.get_optimizer(opt_name)
    if not optdef:
        optdef = guildfile.OptimizerDef.from_name(opt_name, opdef)
    _apply_optimizer_and_flags(optdef, args)

def _apply_optimizer_and_flags(optdef, args):
    args.optimizer = optdef.opspec
    default_opt_flags = tuple([
        op_util.format_flag_arg(name, val)
        for name, val in sorted(optdef.flags.items())
    ])
    args.opt_flags = default_opt_flags + args.opt_flags

def _apply_default_optimizer(opdef, args):
    optdef = opdef.default_optimizer
    if not optdef:
        if opdef.optimizers:
            optimizers_desc = ", ".join([opt.name for opt in opdef.optimizers])
            cli.error(
                "no default optimizer for %s\n"
                "Try 'guild run %s --optimize NAME' where NAME is one of: %s"
                % (opdef.name, opdef.fullname, optimizers_desc))
        optdef = guildfile.OptimizerDef.from_name(DEFAULT_OPTIMIZER, opdef)
    _apply_optimizer_and_flags(optdef, args)

def _maybe_apply_random_optimizer(flag_vals, args):
    for val in flag_vals.values():
        if _is_function(val):
            args.optimizer = "random"
            break

def _is_function(val):
    if not isinstance(val, six.string_types):
        return False
    try:
        op_util.parse_function(val)
    except ValueError:
        return False
    else:
        return True

def _apply_flag_vals(vals, opdef, args):
    joined_vals = _join_user_vals_and_defaults(vals, opdef)
    for name, val in sorted(joined_vals.items()):
        flagdef = opdef.get_flagdef(name)
        if not args.force_flags and not flagdef:
            cli.error(
                "unsupported flag '%s'\n"
                "Try 'guild run %s --help-op' for a list of "
                "flags or use --force-flags to skip this check."
                % (name, opdef.fullname))
        if not args.optimizer:
            val = _coerce_flag_val(val, flagdef)
        opdef.set_flag_value(name, val)

def _join_user_vals_and_defaults(user_vals, opdef):
    joined = {}
    # Apply defaults first, then user_vals so user_vals take precedence.
    joined.update({flagdef.name: flagdef.default for flagdef in opdef.flags})
    joined.update(user_vals)
    return joined

def _coerce_flag_val(val, flagdef):
    try:
        return op_util.coerce_flag_value(val, flagdef)
    except (ValueError, TypeError) as e:
        cli.error(
            "cannot apply %r to flag '%s': %s"
            % (val, flagdef.name, e))

def _apply_arg_disable_plugins(args, opdef):
    if args.disable_plugins:
        opdef.disable_plugins.extend([
            name.strip() for name in args.disable_plugins.split(",")
        ])

def _apply_arg_objective(args, opdef):
    if args.minimize:
        opdef.objective = args.minimize
    elif args.maximize:
        opdef.objective = {
            "maximize": args.maximize
        }

def _apply_arg_set_trace(args, opdef):
    opdef.set_trace = args.set_trace

def _batch_opspec(flag_vals, batch_files, args):
    if args.optimizer:
        return args.optimizer
    elif batch_files or _has_batch_flag_vals(flag_vals):
        return "+"
    else:
        return None

def _has_batch_flag_vals(flag_vals):
    for val in flag_vals.values():
        if isinstance(val, list):
            return True
    return False

###################################################################
# Other op attrs
###################################################################

def _op_run_dir(args):
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
    attrs = {
        "run_params": args.as_kw(),
        "random_seed": _random_seed(args),
        "host": util.hostname(),
        "user": util.user(),
    }
    if args.label:
        attrs["label"] = args.label
    if args.max_trials:
        attrs["max_trials"] = args.max_trials
    return attrs

def _random_seed(args):
    if args.random_seed is not None:
        return args.random_seed
    return random.randint(0, pow(2, 32))

def _op_gpus(args):
    assert not (args.no_gpus and args.gpus)
    if args.no_gpus:
        return ""
    elif args.gpus is not None:
        return args.gpus
    return None # use all available (default)

def _invalid_op_spec_error(e, opdef):
    cli.error("operation %s is not valid: %s" % (opdef.fullname, e))

def _op_init_error(e, opdef):
    cli.error("cannot start %s: %s" % (opdef.fullname, e))

###################################################################
# Apply batch op
###################################################################

def _apply_batch_op(batch_opspec, batch_files, user_flags, args, op):
    """Applies batch_op attrs to op.

    If we determine this is a batch run, resolve the batch opspec to
    an operation in its own right and set it as op.batch_op. This is
    used downstream to run the batch op as a parent of op.

    If we determine this is not a batch run, op.batch_op is None.

    If this is a batch run, the associated optimizer has an
    opportunity to modify op's flag vals to encode values that require
    search space info or other metadata.
    """
    if batch_opspec:
        batch_opdef = _resolve_batch_opdef(batch_opspec)
        batch_args = _batch_op_init_args(batch_opdef, args)
        op.batch_op = _init_batch_op(batch_opdef, batch_args, batch_files)
        _apply_optimizer_attr(op)
        _apply_batch_random_seed(op)
        _apply_batch_flag_encoder(op, user_flags)
    else:
        op.batch_op = None

def _resolve_batch_opdef(batch_opspec):
    try:
        model, op_name = _resolve_model_op(batch_opspec)
    except SystemExit as e:
        assert e.args[0].startswith("cannot find operation"), e
        cli.error(
            "cannot find optimizer '%s'\n"
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
    args = click_util.Args(**params)
    return args

def _init_batch_op(opdef, args, batch_files):
    op = _init_op(opdef, args, is_batch=True)
    op.batch_files = batch_files
    if args.init_trials:
        op.cmd_env.update({"INIT_TRIALS_ONLY": "1"})
    return op

def _apply_optimizer_attr(op):
    assert op.batch_op
    op.extra_attrs["optimizer"] = op.batch_op.opref.to_opspec()

def _apply_batch_random_seed(op):
    """Applies batch op random seed to op.

    random_seed is conveyed to each operation via `extra_attrs`, which
    are saved when the operation is initialized. As a rule, the batch
    and proto ops use the same random seed to ensure consistent
    behavior across restarts.
    """
    assert op.batch_op
    assert "random_seed" in op.batch_op.extra_attrs
    op.extra_attrs["random_seed"] = op.batch_op.extra_attrs["random_seed"]

def _apply_batch_flag_encoder(op, user_flags):
    """Allow a batch op to encode child op flag vals.

    Encoded values are applies when a batch wants to represent a flag
    value using additional configuration. For example, an optimizer
    will encode search parameters into a value so that search spec can
    be used downstream by the optimizer by decoding the flag value.

    If a flag is specified in `user_flags` it is always accepted as
    is - it is never encoded.
    """
    assert op.batch_op
    encode_flag_val = op_util.op_flag_encoder(op.batch_op)
    if not encode_flag_val:
        return
    for flag_name in op.flag_vals:
        if flag_name in user_flags:
            continue
        flagdef = op.opdef.get_flagdef(flag_name)
        if not flagdef:
            continue
        op.flag_vals[flag_name] = encode_flag_val(
            op.flag_vals[flag_name], flagdef)

###################################################################
# Validate op flags
###################################################################

def _validate_op_flags(op):
    try:
        op_util.validate_flag_vals(op.flag_vals, op.opdef)
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
    cli.error("invalid value for %s: %s" % (e.flag.name, e.msg))

###################################################################
# Print op cmd
###################################################################

def _print_cmd(op, args):
    if op.batch_op:
        formatted = " ".join(_preview_cmd(op.batch_op))
        cli.out(formatted)
        _print_batch_trials_cmd(op, args)
    else:
        formatted = " ".join(_preview_cmd(op))
        cli.out(formatted)

def _preview_cmd(op):
    return [pipes.quote(arg) for arg in op.cmd_args]

def _print_batch_trials_cmd(op, args):
    _run_batch_tmp_with_env(op, {"PRINT_TRIALS_CMD": "1"}, args)

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
    if args.print_trials:
        _run_batch_tmp_with_env(op, {"PRINT_TRIALS": "1"}, args)
    else:
        assert args.save_trials
        _run_batch_tmp_with_env(op, {"SAVE_TRIALS": args.save_trials}, args)

def _run_batch_tmp_with_env(op, cmd_env, args):
    with util.TempDir() as batch_run_dir:
        op.set_run_dir(batch_run_dir)
        op.batch_op.cmd_env.update(cmd_env)
        _init_batch_run(op)
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
        "You are about to {action} {op_desc}{batch_suffix}{remote_suffix}\n"
        "{flags}"
        "{resources}"
        "Continue?"
        .format(
            action=_action_desc(args),
            op_desc=_op_desc(op),
            batch_suffix=_batch_suffix(op, args),
            remote_suffix=_remote_suffix(args),
            flags=_format_op_flags(op),
            resources=_format_op_resources(op.resource_config)))
    return cli.confirm(prompt, default=True)

def _action_desc(args):
    if args.stage:
        return "stage"
    elif args.init_trials:
        return "initialize trials for"
    return "run"

def _op_desc(op):
    return op.opref.to_opspec()

def _batch_suffix(op, args):
    if not op.batch_op:
        return ""
    parts = []
    if op.batch_op.opdef.name == "+":
        parts.append(" in a batch")
    else:
        parts.append(" with %s optimizer" % op.batch_op.opdef.name)
        max_trials = args.max_trials or op.batch_op.opdef.default_max_trials
        if max_trials is None:
            parts.append(" (unknown number of trials)")
        elif max_trials == 1:
            parts.append(" (max 1 trial)")
        else:
            parts.append(" (max %s trials)" % max_trials)
    return "".join(parts)

def _remote_suffix(args):
    if args.remote:
        return " on %s" % args.remote
    return ""

def _format_op_flags(op):
    if not op.flag_vals:
        return ""
    return "\n".join([
        "  %s" % _format_flag(name, val, op.opdef)
        for name, val in sorted(op.flag_vals.items())
    ]) + "\n"

def _format_flag(name, val, opdef):
    if val is None:
        formatted = _null_label(name, opdef)
    else:
        formatted = _strip_quotes(op_util.format_flag_val(val))
    return "%s: %s" % (name, formatted)

def _null_label(name, opdef):
    flag = opdef.get_flagdef(name)
    if flag and flag.null_label is not None:
        return op_util.format_flag_val(flag.null_label)
    return "default"

def _strip_quotes(s):
    if s[:1] == "'" and s[-1:] == "'":
        return s[1:-1]
    return s

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
    if op.batch_op and op.batch_op.batch_files:
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
# Non-batch run
###################################################################

def _run_normal(op, args):
    _check_normal_needed(op, args)
    _check_restart_running(args)
    _run_op(op, args)

def _check_normal_needed(op, args):
    if not args.needed:
        return
    if args.restart:
        _check_needed_restart(op, args)
    else:
        _check_needed_matching_runs(op)

###################################################################
# Batch run
###################################################################

def _run_batch(op, args):
    _check_batch_needed(op, args)
    _check_restart_running(args)
    _init_batch_run(op)
    _run_op(op.batch_op, args)

def _check_batch_needed(op, args):
    """Check whether or not a batch op is needed.

    `op` must be the proto op - not the batch op.

    The needed check for batch runs is the same as for normal runs
    when restart is not specified - the run will proceed only if
    another batch op with the same name does not exist.

    Needed checks for batch restarts are different - the batch is run
    with run_params containing the needed flag and is allowed to
    restart generated trials only if they are needed (i.e. the
    applicable trial is not in an error or pending state).
    """
    assert op.batch_op
    if not args.needed:
        return
    if args.restart:
        # Run the batch but indicate only needed trials.
        op.batch_op.cmd_env["NEEDED_TRIALS_ONLY"] = "1"
    else:
        _check_needed_matching_runs(op)

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
    proto_op.extra_attrs["run_params"]["optimizer"] = None
    proto_op.init()
    if batches:
        proto_op.write_run_attr("batches", batches)

###################################################################
# Needed check support
###################################################################

def _check_needed_restart(op, args):
    # Assert that we're restarting something that exists.
    assert os.path.exists(op.run_dir), op.run_dir
    run_id = os.path.basename(op.run_dir)
    assert run_id.startswith(args.restart), (run_id, args.restart)
    run = runlib.Run(run_id, op.run_dir)
    if not op_util.restart_needed(run, op.flag_vals):
        cli.out(
            "Skipping run because flags have not changed "
            "(--needed specified)")
        raise SystemExit(0)

def _check_needed_matching_runs(op):
    matching = _find_matching_runs(op)
    if matching:
        cli.out(
            "Skipping because the following runs match "
            "this operation (--needed specified):")
        _print_matching_runs(matching)
        raise SystemExit(0)

def _find_matching_runs(op):
    if op.batch_op:
        to_match = op.batch_op
    else:
        to_match = op
    matching = [
        run for run in resolver.matching_runs([to_match.opref])
        if _match_run_flags(run, to_match.flag_vals)
    ]
    if op.batch_op:
        matching = [run for run in matching if _match_proto_run(run, op)]
    return matching

def _match_run_flags(run, target):
    run_flags = run.get("flags")
    log.debug(
        "comparing run %s flags %r to target %r",
        run.id, run_flags, target)
    return run_flags == target

def _match_proto_run(batch_run, proto_op):
    proto_run = runlib.Run("", batch_run.guild_path("proto"))
    return (
        proto_op.opref.is_op_run(proto_run) and
        _match_run_flags(proto_run, proto_op.flag_vals))

def _print_matching_runs(runs):
    formatted = [runs_impl.format_run(run) for run in runs]
    cols = [
        "index", "operation", "started",
        "status_with_remote", "label"
    ]
    cli.table(formatted, cols=cols, indent=2)

###################################################################
# Check for request to restart a running op
###################################################################

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
        _handle_run_exit(returncode, op, args)

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

def _handle_run_exit(returncode, op, args):
    if op.stage_only:
        _print_staged_info(op)
    if args.init_trials:
        op.set_pending()
    if returncode != 0:
        cli.error(exit_status=returncode)

def _print_staged_info(op):
    cmd = " ".join(_preview_cmd(op))
    cli.out(
        "Operation is staged in %s\n"
        "To run the operation, use: "
        "(cd %s && source .guild/env && %s)"
        % (op.run_dir, op.run_dir, cmd)
    )
