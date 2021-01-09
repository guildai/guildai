# Copyright 2017-2020 TensorHub, Inc.
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
import sys

import six

from guild import batch_util
from guild import cli
from guild import click_util
from guild import cmd_impl_support
from guild import config
from guild import flag_util
from guild import guildfile
from guild import help as helplib
from guild import op as oplib
from guild import op_cmd as op_cmd_lib
from guild import op_dep
from guild import op_util
from guild import remote
from guild import resolver as resolverlib
from guild import run as runlib
from guild import run_util
from guild import summary
from guild import util
from guild import var
from guild import yaml_util

from . import remote_impl_support

log = logging.getLogger("guild")

# Use Bayesian with gaussian process as default optimizer when opdef
# does not contain any optimizers.
#
DEFAULT_OPTIMIZER = "gp"
DEFAULT_OBJECTIVE = "loss"

FLAG_TEST_ATTRS = [
    "default",
    "type",
    "required",
    "arg_name",
    "arg_skip",
    "arg_switch",
    "arg_split",
    "env_name",
    "choices",
    "allow_other",
    "distribution",
    "max",
    "min",
    "null_label",
]


###################################################################
# State
###################################################################


class State(object):
    def __init__(self, args):
        self.args = args
        self.restart_run = None
        self.proto_run = None
        self.user_op = Operation()
        self.batch_op = None


class Operation(oplib.Operation):
    def __init__(self):
        super(Operation, self).__init__()
        self._run = None
        self._run_is_proto = False
        self._force_sourcecode = False
        self._opdef = None
        self._resource_flagdefs = []
        self._user_flag_vals = {}
        self._batch_trials = None
        self._op_flag_vals = {}
        self._flag_null_labels = {}
        self._op_cmd = None
        self._op_cmd_run_attrs = {}
        self._python_requires = None
        self._random_seed = None
        self._max_trials = None
        self._objective = None
        self._label_template = None
        self._label = None
        self._tags = []
        self._comment = None
        self._output_scalars = None
        self._sourcecode_root = None
        self._flags_extra = None


def _state_for_args(args):
    S = State(args)
    if S.args.help_op:
        _op_init_opdef(S.args.opspec, S.user_op, S.args)
    else:
        _state_init_restart_or_proto_run(S)
        _state_init_user_op(S)
        _state_init_batch_op(S)
    return S


def _op_config_data(op):
    return {
        "flag-null-labels": op._flag_null_labels,
        "op-cmd": op_cmd_lib.as_data(op._op_cmd),
        "python-requires": op._python_requires,
        "label-template": op._label_template,
        "output-scalars": op._output_scalars,
        "deps": op_util.op_deps_as_data(op.deps),
        "sourcecode-root": op._sourcecode_root,
        "flags-extra": op._flags_extra,
    }


def _apply_op_config_data(data, op):
    op._flag_null_labels = data.get("flag-null-labels")
    op._op_cmd = op_cmd_lib.for_data(data.get("op-cmd"))
    op._python_requires = data.get("python-requires")
    op._label_template = data.get("label-template")
    op._output_scalars = data.get("output-scalars")
    op._sourcecode_root = data.get("sourcecode-root")
    op._flags_extra = data.get("flags-extra")
    op.deps = op_util.op_deps_for_data(data.get("deps"))


# =================================================================
# State - restart / proto run
# =================================================================


def _state_init_restart_or_proto_run(S):
    assert not (S.args.restart and S.args.proto)
    if S.args.restart:
        _state_init_restart_run(S)
    elif S.args.proto:
        _state_init_proto_run(S)


def _state_init_restart_run(S):
    if S.args.remote:
        S.restart_run = _remote_run_for_spec(S.args.restart, S.args)
    else:
        S.restart_run = _local_run_for_spec(S.args.restart)


def _state_init_proto_run(S):
    if S.args.remote:
        S.proto_run = _remote_run_for_spec(S.args.proto, S.args)
    else:
        S.proto_run = _local_run_for_spec(S.args.proto)


def _remote_run_for_spec(spec, args):
    return remote_impl_support.one_run(spec, args)


def _local_run_for_spec(spec):
    return util.find_apply(
        [
            run_util.run_for_run_dir,
            run_util.marked_or_latest_run_for_opspec,
            one_run,
        ],
        spec,
    )


# =================================================================
# State - user op
# =================================================================


def _state_init_user_op(S):
    """Initialize state for user op."""
    _user_op_init_run(S)
    _op_init_force_sourcecode(S.args.force_sourcecode, S.user_op)
    _op_init_opdef(S.args.opspec, S.user_op, S.args)
    _op_init_user_flags(S.args.flags, S.user_op)
    _op_init_op_cmd(S.user_op)
    _op_init_op_flags(S.args, S.user_op)
    _op_init_config(
        S.args.label,
        S.args.tags,
        S.args.comment,
        S.args.edit_comment,
        S.user_op,
    )
    _op_init_core(S.args, S.user_op)


def _user_op_init_run(S):
    assert not (S.restart_run and S.proto_run)
    if S.restart_run:
        _user_op_init_run_(S, S.restart_run)
    elif S.proto_run:
        _user_op_init_run_(S, S.proto_run)
        S.user_op._run_is_proto = True


def _user_op_init_run_(S, run):
    if run.batch_proto:
        S.user_op._run = run.batch_proto
    else:
        S.user_op._run = run


def _op_init_force_sourcecode(force_sourcecode_arg, op):
    op._force_sourcecode = force_sourcecode_arg


# =================================================================
# Op - user flags
# =================================================================


def _op_init_user_flags(flag_args, op):
    op._user_flag_vals, batch_files = split_flag_args(flag_args, op._opdef)
    if batch_files:
        trials = _trials_for_batch_files(batch_files)
        if len(trials) == 1:
            _apply_single_trial_user_flags(trials[0], op)
        else:
            op._batch_trials = trials


def split_flag_args(flag_args, opdef):
    batch_files, rest_args = op_util.split_batch_files(flag_args)
    assigns = _parse_assigns(rest_args, opdef)
    return assigns, batch_files


def _parse_assigns(assign_args, opdef):
    try:
        return op_util.parse_flag_assigns(assign_args, opdef)
    except op_util.ArgValueError as e:
        _invalid_flag_arg_error(e.arg)


def _trials_for_batch_files(batch_files):
    batch_files = [_resolve_batch_file(path) for path in batch_files]
    try:
        return op_util.trials_for_batch_files(batch_files)
    except op_util.BatchFileError as e:
        _batch_file_error(e)


def _resolve_batch_file(path):
    resolved = os.path.join(config.cwd(), os.path.expanduser(path))
    if not os.path.exists(resolved):
        _no_such_batch_file_error(resolved)
    return resolved


def _apply_single_trial_user_flags(trial, op):
    for name, val in trial.items():
        if name not in op._user_flag_vals:
            op._user_flag_vals[name] = val


# =================================================================
# Op - opdef
# =================================================================


def _op_init_opdef(opspec, op, args):
    if opspec:
        op._opdef = opdef_for_opspec(opspec)
    elif op._run:
        if args.flags or args.force_sourcecode:
            # We need opdef for restart/run-with-proto when user specifies
            # flag values or when force-sourcecode is specified.
            op._opdef = _opdef_for_run(op._run)
    else:
        op._opdef = _default_opdef()


def _opdef_for_run(run):
    if isinstance(run, remote.RunProxy):
        return _opdef_for_remote_run(run)
    opspec = run.opref.to_opspec()
    return opdef_for_opspec(opspec, run)


def _opdef_for_remote_run(run):
    if _cwd_remote_run(run):
        return opdef_for_opspec(_cwd_opspec(run.opref))
    return opdef_for_opspec(run.opref.to_opspec(), run)


def _cwd_remote_run(run):
    try:
        gf = guildfile.for_dir(config.cwd())
    except:
        return False
    else:
        return gf.package and gf.package.name == run.opref.pkg_name


def _cwd_opspec(opref):
    return "%s:%s" % (opref.model_name, opref.op_name)


def opdef_for_opspec(opspec, for_run=None):
    try:
        return op_util.opdef_for_opspec(opspec)
    except op_util.InvalidOpSpec:
        _invalid_opspec_error(opspec)
    except op_util.CwdGuildfileError as e:
        _guildfile_error(e.path, str(e))
    except op_util.NoSuchModel:
        if for_run:
            _missing_run_opdef_error(opspec, for_run)
        else:
            _no_such_model_op_error(opspec)
    except op_util.MultipleMatchingModels as e:
        _multiple_models_error(e.model_ref, e.matches)
    except op_util.NoSuchOperation as e:
        _no_such_opdef_error(e.model, e.op_name)
    except op_util.ModelOpProxyError as e:
        _model_op_proxy_error(e)


def _default_opdef():
    return opdef_for_opspec(None)


# =================================================================
# Op - op cmd
# =================================================================


def _op_init_op_cmd(op):
    if op._opdef:
        op._op_cmd, run_attrs = _op_cmd_for_opdef(op._opdef)
        if run_attrs:
            op._op_cmd_run_attrs.update(run_attrs)


def _op_cmd_for_opdef(opdef):
    try:
        return op_util.op_cmd_for_opdef(opdef)
    except op_util.InvalidOpDef as e:
        _invalid_opdef_error(opdef, e.msg)


# =================================================================
# Op - op flags
# =================================================================


def _op_init_op_flags(args, op):
    if op._run:
        _apply_run_flags(op._run, op._op_flag_vals)
    if op._opdef:
        _apply_op_flags_vals_for_opdef(
            op._opdef,
            op._user_flag_vals,
            args.force_flags or op._batch_trials,
            op._op_cmd,
            args,
            op._resource_flagdefs,
            op._op_flag_vals,
        )
    if args.edit_flags:
        _edit_op_flags(op)


def _apply_run_flags(run, flag_vals):
    flag_vals.update(run.get("flags") or {})


def _apply_op_flags_vals_for_opdef(
    opdef,
    user_flag_vals,
    force_flags,
    op_cmd,
    args,
    resource_flagdefs,
    op_flag_vals,
):
    """Applies opdef and user-provided flags to `op_flag_vals`.

    Also applies resolved resource flag defs per flag vals
    `resource_flagdefs`.

    Attempts to resolve operation runs and use resolve run short
    IDs as applicable flag values.

    Opdef is used to provide missing default values, coerce flag vals,
    and validate vals. Opdef-provided flag vals are added to op flag
    vals only if they are not already in op flags, or if they are in
    user-provided flags. This maintains existing values (e.g. from a
    restart) unless a user explicitly provides a flag value.

    op_cmd is modified to include CmdFlag with arg-skip=yes for
    resolved run IDs provided a flag isn't defined for the resolved
    resource name. These flag values are used by Guild to resolve
    resources and should not be included in flag args unless the a
    flag def is explicitly provided.
    """
    flag_vals, resolved_resource_flagdefs = _flag_vals_for_opdef(
        opdef, user_flag_vals, force_flags
    )
    resource_flagdefs.extend(resolved_resource_flagdefs)
    _apply_default_dep_runs(opdef, op_cmd, args, flag_vals)
    for name, val in flag_vals.items():
        if name in user_flag_vals or name not in op_flag_vals:
            op_flag_vals[name] = val


def _flag_vals_for_opdef(opdef, user_flag_vals, force_flags):
    """Returns flag vals for opdef.

    Results includes defaults for opdef overridden by user flag vals
    where specified.
    """
    try:
        return op_util.flag_vals_for_opdef(opdef, user_flag_vals, force_flags)
    except op_util.MissingRequiredFlags as e:
        _missing_required_flags_error(e)
    except op_util.InvalidFlagChoice as e:
        _invalid_flag_choice_error(e)
    except op_util.InvalidFlagValue as e:
        _invalid_flag_value_error(e)
    except op_util.NoSuchFlagError as e:
        _no_such_flag_error(e.flag_name, opdef)


def _apply_default_dep_runs(opdef, op_cmd, args, flag_vals):
    """Applies default run IDs to flag_vals for dependencies."""
    resolver_factory = _resolver_factory(args)
    for run, dep in op_dep.resolved_op_runs_for_opdef(
        opdef, flag_vals, resolver_factory
    ):
        dep_flag_name = _dep_flag_name(dep)
        _ensure_dep_flag_op_cmd_arg_skip(dep_flag_name, opdef, op_cmd)
        _apply_dep_run_id(run.id, dep_flag_name, flag_vals)


def _resolver_factory(args):
    if args.remote:
        return _remote_resolver_for_source_f(args.remote)
    else:
        # Use default.
        return None


def _dep_flag_name(dep):
    return dep.resdef.flag_name or dep.resdef.name


def _ensure_dep_flag_op_cmd_arg_skip(flag_name, opdef, op_cmd):
    """Ensures that a dep flag does not appear as an op cmd arg.

    An exception is made if the flag is defined in the opdef, which
    which case the opdef flag is used to control op cmd args.
    """
    if opdef.get_flagdef(flag_name):
        return
    cmd_flag = op_cmd.cmd_flags.setdefault(flag_name, op_cmd_lib.CmdFlag())
    cmd_flag.flag_name = flag_name
    cmd_flag.arg_skip = True


def _apply_dep_run_id(run_id, dep_flag_name, flag_vals):
    """Applies a full run ID to a flag value.

    If the current flag value is unset or None, run ID is set without
    further checks.

    If the current flag value is a string and is a prefix of run_id,
    the value is replaced with the full run ID.

    If the current flag value is a list, the first item in the list
    that is a prefix of the run ID is updated with the full run ID.

    If the current flag value is neither a string nor a list, function
    raises an assertion error.
    """
    val = flag_vals.get(dep_flag_name)
    if val is None:
        flag_vals[dep_flag_name] = run_id
    elif isinstance(val, six.string_types):
        if run_id.startswith(val):
            flag_vals[dep_flag_name] = run_id
    elif isinstance(val, list):
        _apply_dep_run_id_to_list(run_id, val)
        flag_vals[dep_flag_name] = val
    else:
        assert False, (type(val), dep_flag_name, flag_vals)


def _apply_dep_run_id_to_list(run_id, l):
    for i, x in enumerate(l):
        if run_id.startswith(x):
            l[i] = run_id
            break


def _edit_op_flags(op):
    encoded_flags = _encode_flags_with_help(op._op_flag_vals, op._opdef)
    while True:
        # Loop to let user re-edit on error.
        edited = util.edit(encoded_flags, extension=".yml")
        if edited is None or not edited.strip():
            break
        try:
            flag_vals = yaml_util.decode_yaml(edited)
        except ValueError as e:
            cli.out("Error reading flags: %s" % e, err=True)
            if not cli.confirm("Would you like to re-edit these flags?", default=True):
                cli.error()
        else:
            op._op_flag_vals = flag_vals
            break


def _encode_flags_with_help(vals, opdef):
    if not opdef:
        return yaml_util.encode_yaml(vals)
    lines = []
    prev_help = None
    for name, val in sorted(vals.items()):
        flag_help = _format_flag_help(opdef.get_flagdef(name))
        if prev_help or flag_help and lines:
            lines.append("")
        lines.append(
            "%s: %s" % (yaml_util.encode_yaml(name), yaml_util.encode_yaml(val))
        )
        if flag_help:
            lines.extend(["  # %s" % line for line in flag_help.split("\n")])
        prev_help = flag_help
    return "\n".join(lines)


def _format_flag_help(flagdef):
    if not flagdef:
        return None
    return helplib.flag_edit_help(flagdef)


# =================================================================
# Remote run resolver lookup support
# =================================================================


def _remote_resolver_for_source_f(remote):
    """Returns a function used to resolve a source.

    We install a hook to handle remote cases. The base
    OperationResolver doesn't handle remote lookups. We implement a
    remote version that uses a customized callback for returning a
    remote 'latest or marked' run matching the op requirements.
    """

    def f(source, dep):
        scheme = source.parsed_uri.scheme
        assert scheme == "operation", source
        resource = op_dep.ResourceProxy(dep.res_location, dep.config)
        modeldef = source.resdef.modeldef
        return _RemoteOperationResolver(remote, source, resource, modeldef)

    return f


class _RemoteOperationResolver(resolverlib.OperationResolver):
    """Customized operation resolver that handles remote cases.

    Overrides `resolve_op_run` to lookup remote runs instead of the
    default resolver's lookup of local runs.
    """

    def __init__(self, remote, source, resource, modeldef):
        super(_RemoteOperationResolver, self).__init__(source, resource, modeldef)
        self.remote = remote

    def resolve_op_run(self, run_id_prefix=None, include_staged=False):
        """Remote version of default `resolve_op_run`.

        Uses a remote-enabled callback for resolving a candidate run
        the the op dependency.
        """
        return self._resolve_op_run(
            run_id_prefix, include_staged, _remote_marked_or_latest_run_f(self.remote)
        )


def _remote_marked_or_latest_run_f(remote):
    """Returns a remote-enabled lookup function for 'marked or latest run'."""

    def f(oprefs, run_id_prefix=None, status=None):
        runs = _remote_runs_for_marked_or_latest(remote, oprefs, run_id_prefix, status)
        log.debug("remote runs for %s: %s", oprefs, runs)
        if not runs:
            return None
        for run in runs:
            if run.get("marked"):
                return run
        return runs[0]

    return f


def _remote_runs_for_marked_or_latest(remote, oprefs, run_id_prefix, status):
    """Returns a list of candidate runs for 'marked or latest' consideration.

    Uses `remote_impl_support.filtered_runs` to get remote runs
    matching the specified opdef list, run ID prefix, and status list.
    """
    from .runs_list import list_runs

    args = click_util.Args(**list_runs.make_context("", []).params)
    args.remote = remote
    args.filter_ops = [op.to_opspec() for op in oprefs]
    args.status_completed = "completed" in status
    args.status_running = "running" in status
    args.status_terminated = "terminated" in status
    args.status_staged = "staged" in status
    log.debug("filtered runs params for remote list: %r", args.as_kw())
    return _filter_by_run_id_prefix(
        remote_impl_support.filtered_runs(args), run_id_prefix
    )


def _filter_by_run_id_prefix(runs, run_id_prefix):
    if not run_id_prefix:
        return runs
    return [run for run in runs if run.id.startswith(run_id_prefix)]


# =================================================================
# Op - config
# =================================================================


def _op_init_config(
    label_arg,
    tags_arg,
    comments_arg,
    edit_comment_arg,
    op,
    is_batch=False,
):
    label_template = _label_template(label_arg, tags_arg)
    if op._run:
        _op_init_config_for_run(op._run, label_template, tags_arg, comments_arg, op)
    else:
        assert op._opdef
        _op_init_config_for_opdef(
            op._opdef,
            label_template,
            tags_arg,
            comments_arg,
            edit_comment_arg,
            op,
            is_batch,
        )


def _label_template(label_arg, tags_arg):
    if label_arg is not None:
        return label_arg
    if tags_arg:
        return "%s ${default_label}" % _format_tags_for_label(tags_arg)
    return None


def _format_tags_for_label(tags):
    return " ".join(tags)


def _op_init_config_for_run(run, label_template, tags, comment, op):
    config = run.get("op")
    if not config:
        _missing_op_config_for_restart_error(run)
    if not config.get("op-cmd"):
        _invalid_op_config_for_restart_error(run)
    _apply_op_config_data(config, op)
    if label_template is not None:
        op._label_template = label_template
    if tags:
        op._tags = tags
    if comment:
        op._comment = comment


def _op_init_config_for_opdef(
    opdef,
    label_template,
    tags,
    comment,
    edit_comment,
    op,
    is_batch,
):
    op._flag_null_labels = _flag_null_labels_for_opdef(opdef, op._resource_flagdefs)
    op._python_requires = _python_requires_for_opdef(opdef)
    op._label_template = label_template if label_template is not None else opdef.label
    op._output_scalars = opdef.output_scalars
    op._sourcecode_root = _opdef_sourcecode_dest(opdef)
    op._flags_extra = _opdef_flags_extra(opdef)
    op._tags = list(tags) + opdef.tags
    op._comment = _init_op_comment(comment, edit_comment, is_batch)


def _flag_null_labels_for_opdef(opdef, resource_flagdefs):
    return {
        f.name: f.null_label
        for f in opdef.flags + resource_flagdefs
        if f.null_label is not None
    }


def _python_requires_for_opdef(opdef):
    return opdef.python_requires or opdef.modeldef.python_requires


def _opdef_sourcecode_dest(opdef):
    return _opdef_explicit_sourcecode_dest(opdef) or _opdef_default_sourcecode_dest(
        opdef
    )


def _opdef_explicit_sourcecode_dest(opdef):
    return opdef.sourcecode.dest or opdef.modeldef.sourcecode.dest


def _opdef_default_sourcecode_dest(opdef):
    if _sourcecode_empty(opdef):
        return None
    return _default_sourcecode_path()


def _sourcecode_empty(opdef):
    return opdef.sourcecode.disabled or (
        opdef.sourcecode.empty_def and opdef.modeldef.sourcecode.disabled
    )


def _default_sourcecode_path():
    return os.path.join(".guild", "sourcecode")


def _opdef_flags_extra(opdef):
    return {flag.name: flag.extra for flag in opdef.flags if flag.extra}


def _init_op_comment(comment, edit_comment, is_batch):
    run_type = "batch" if is_batch else "run"
    if edit_comment:
        msg_lines = [
            comment or "",
            "# Type a comment for the %s. Lines starting with '#' are ignored."
            % run_type,
            "# An empty comment aborts the command.",
        ]
        comment = util.edit(
            "\n".join(msg_lines),
            extension=".GUILD_COMMENT",
            strip_comment_lines=True,
        )
        if not comment:
            cli.out("Aborting due to an empty comment.", err=True)
            cli.error()
    return comment


# =================================================================
# Op - core
# =================================================================


def _op_init_core(args, op):
    _op_init_opref(op)
    _op_init_cmd(args, op)
    _op_init_private_env(op)
    _op_init_sourcecode_paths(args, op)
    _op_init_run_dir(args, op)
    _op_init_label(op)
    _op_init_random_seed(args.random_seed, op)
    _op_init_deps(op)
    _op_init_run_attrs(args, op)
    _op_init_callbacks(op)


# =================================================================
# Op - opref
# =================================================================


def _op_init_opref(op):
    if op._opdef:
        op.opref = op._opdef.opref
    else:
        assert op._run
        op.opref = op._run.opref


# =================================================================
# Op - cmd args / env
# =================================================================


def _op_init_cmd(args, op):
    assert op._op_cmd
    op.cmd_args, op.cmd_env = _generate_op_cmd(
        op._op_cmd, op._op_flag_vals, op._python_requires
    )
    _apply_gpu_arg_env(args, op.cmd_env)
    _apply_break_args_env(args, op.cmd_env)


def _generate_op_cmd(op_cmd, flag_vals, python_requires):
    resolve_params = _op_cmd_resolve_params(flag_vals, python_requires)
    try:
        return op_cmd_lib.generate(op_cmd, flag_vals, resolve_params)
    except util.UndefinedReferenceError as e:
        _op_cmd_error(
            "invalid setting for operation: command contains "
            "invalid reference '%s'" % e.args[0]
        )


def _op_cmd_resolve_params(flag_vals, python_requires):
    params = dict(flag_vals)
    params["python_exe"] = _proc_python_exe(python_requires)
    return params


def _proc_python_exe(python_requires):
    if not python_requires:
        return config.python_exe()
    matching = util.find_python_interpreter(python_requires)
    if not matching:
        _op_cmd_error(
            "cannot find a python interpreter for " "requirement %r" % python_requires
        )
    path, _ver = matching
    return path


def _apply_gpu_arg_env(args, env):
    if args.no_gpus:
        log.info("Masking available GPUs (CUDA_VISIBLE_DEVICES='')")
        env["CUDA_VISIBLE_DEVICES"] = ""
    elif args.gpus is not None:
        log.info("Masking available GPUs (CUDA_VISIBLE_DEVICES='%s')", args.gpus)
        env["CUDA_VISIBLE_DEVICES"] = args.gpus


def _apply_break_args_env(args, env):
    if args.break_on_error:
        env["BREAK_ON_ERROR"] = "1"
    if args.break_:
        env["PDB_BREAKS"] = _encode_pdb_breaks(args.break_)


def _encode_pdb_breaks(breaks):
    return " ".join([util.shlex_quote(b) for b in breaks])


def _op_init_private_env(op):
    if op._opdef:
        op.private_env = op._opdef.env_secrets or []


# =================================================================
# Op - sourcecode paths
# =================================================================


def _op_init_sourcecode_paths(args, op):
    op.sourcecode_paths = _sourcecode_paths(op, args)


def _sourcecode_paths(op, args):
    if args.debug_sourcecode:
        return _resolve_sourcecode_paths(args.debug_sourcecode)
    return _op_sourcecode_paths(op)


def _resolve_sourcecode_paths(s):
    cwd = config.cwd()
    return [
        os.path.abspath(os.path.join(cwd, part)) for part in s.split(os.path.pathsep)
    ]


def _op_sourcecode_paths(op):
    if op._sourcecode_root is None:
        return []
    return [op._sourcecode_root]


# =================================================================
# Op - run dir
# =================================================================


def _op_init_run_dir(args, op):
    if op._run and not op._run_is_proto:
        op.run_dir = op._run.dir
    else:
        op.run_dir = _op_run_dir_for_args(args)


def _op_run_dir_for_args(args):
    if args.run_id:
        return os.path.join(var.runs_dir(), args.run_id)
    if not args.run_dir:
        return None
    run_dir = os.path.abspath(args.run_dir)
    if not args.stage and os.getenv("NO_WARN_RUNDIR") != "1":
        cli.note(
            "Run directory is '%s' (results will not be " "visible to Guild)" % run_dir
        )
    return run_dir


# =================================================================
# Op - run label
# =================================================================


def _op_init_label(op):
    op._label = op_util.run_label(op._label_template, op._op_flag_vals)


# =================================================================
# Op - random seed
# =================================================================


def _op_init_random_seed(random_seed_arg, op):
    if random_seed_arg:
        op._random_seed = random_seed_arg
    elif op._run:
        op._random_seed = _random_seed_for_run(op._run)
    else:
        op._random_seed = runlib.random_seed()


def _random_seed_for_run(run):
    return run.get("random_seed") or runlib.random_seed()


# =================================================================
# Op - run deps
# =================================================================


def _op_init_deps(op):
    if op._run:
        _check_flags_for_resolved_deps(op._user_flag_vals, op._run)
    if op._opdef:
        op.deps = _op_deps_for_opdef(op._opdef, op._op_flag_vals)


def _check_flags_for_resolved_deps(flag_vals, run):
    """Generate an error if flags contain vals for resolved deps in run.

    Used to prevent redefinition of dependencies for a run.
    """
    resolved_deps = run.get("deps") or {}
    for name in flag_vals:
        if name in resolved_deps:
            _flag_for_resolved_dep_error(name, run)


def _op_deps_for_opdef(opdef, flag_vals):
    try:
        return op_dep.deps_for_opdef(opdef, flag_vals)
    except op_dep.OpDependencyError as e:
        _invalid_opdef_error(opdef, e)


# =================================================================
# Op - run attrs
# =================================================================


def _op_init_run_attrs(args, op):
    attrs = op.run_attrs
    if op._label:
        attrs["label"] = op._label
    if op._tags:
        attrs["tags"] = op._tags
    if op._comment:
        attrs["comments"] = _init_comments(op._comment)
    if op._batch_trials:
        attrs["trials"] = op._batch_trials
    attrs["flags"] = op._op_flag_vals
    attrs["user_flags"] = op._user_flag_vals
    attrs["run_params"] = args.as_kw()
    attrs["random_seed"] = op._random_seed
    if op._max_trials:
        attrs["max_trials"] = op._max_trials
    if op._objective:
        attrs["objective"] = op._objective
    attrs["op"] = _op_config_data(op)
    _apply_system_attrs(op, attrs)
    attrs.update(op._op_cmd_run_attrs)


def _init_comments(comment):
    return [
        {
            "user": util.user(),
            "host": util.hostname(),
            "body": comment,
            "time": comment_timestamp(),
        }
    ]


def comment_timestamp():
    return runlib.timestamp()


def _apply_system_attrs(op, attrs):
    # Don't reapply system attrs to existing runs.
    if op._run:
        return
    assert op._opdef
    attrs["host"] = util.hostname()
    attrs["user"] = util.user()
    attrs["platform"] = util.platform_info()
    if _pip_freeze_required(op):
        attrs["pip_freeze"] = _pip_freeze()


def _pip_freeze_required(op):
    return (
        op._opdef.pip_freeze is not False
        and os.getenv("NO_PIP_FREEZE") != "1"
        and _is_python_op(op)
    )


def _is_python_op(op):
    return "python" in " ".join(op.cmd_args)


def _pip_freeze():
    from guild import pip_util

    return pip_util.freeze()


# =================================================================
# Op - run callbacks
# =================================================================


def _op_init_callbacks(op):
    if op._run:
        if op._run_is_proto:
            _op_init_callbacks_for_run_with_proto(op)
        else:
            _op_init_callbacks_for_restart(op)
    else:
        assert op._opdef
        _op_init_callbacks_for_opdef(op._opdef, op)


def _op_init_callbacks_for_restart(op):
    op.callbacks = oplib.OperationCallbacks(init_output_summary=_init_output_summary)


def _init_output_summary(op, run):
    if _output_scalars_disabled(op):
        return None
    return _output_scalars_summary(op._output_scalars, op._op_flag_vals, run)


def _output_scalars_disabled(op):
    return op._output_scalars is not None and not op._output_scalars


def _output_scalars_summary(output_scalars, flag_vals, run):
    if output_scalars is None:
        output_scalars = summary.DEFAULT_OUTPUT_SCALARS
        ignore = flag_vals.keys()
    else:
        ignore = None
    summary_path = run.guild_path()
    return summary.OutputScalars(output_scalars, summary_path, ignore)


def _op_init_callbacks_for_opdef(opdef, op):
    op.callbacks = oplib.OperationCallbacks(
        init_output_summary=_init_output_summary,
        run_initialized=_run_init_cb_for_opdef(opdef),
    )


def _run_init_cb_for_opdef(opdef):
    def f(op, run):
        _copy_opdef_sourcecode(opdef, op, run)
        _write_run_sourcecode_digest(op, run)
        _write_run_vcs_commit(opdef, run)

    return f


def _copy_opdef_sourcecode(opdef, op, run):
    if os.getenv("NO_SOURCECODE") == "1":
        log.debug("NO_SOURCECODE=1, skipping sourcecode copy")
        return
    sourcecode_src = opdef.guildfile.dir
    if not sourcecode_src:
        log.debug("no sourcecode source, skipping sourcecode copy")
        return
    sourcecode_select = op_util.sourcecode_select_for_opdef(opdef)
    if not sourcecode_select:
        log.debug("no sourcecode rules, skipping sourcecode copy")
        return
    dest = _sourcecode_dest(run, op)
    log.debug(
        "copying source code files for run %s from %s to %s",
        run.id,
        sourcecode_src,
        dest,
    )
    op_util.copy_sourcecode(sourcecode_src, sourcecode_select, dest)


def _sourcecode_dest(run, op):
    return os.path.join(run.dir, op._sourcecode_root or _default_sourcecode_path())


def _write_run_sourcecode_digest(op, run):
    if op._sourcecode_root:
        op_util.write_sourcecode_digest(run, op._sourcecode_root)


def _write_run_vcs_commit(opdef, run):
    if os.getenv("NO_VCS_COMMIT") == "1":
        log.debug("NO_VCS_COMMIT=1, skipping VCS commit")
        return

    op_util.write_vcs_commit(opdef, run)


def _op_init_callbacks_for_run_with_proto(op):
    if op._force_sourcecode:
        assert op._opdef
        _op_init_callbacks_for_opdef(op._opdef, op)
    else:
        op.callbacks = oplib.OperationCallbacks(
            init_output_summary=_init_output_summary,
            run_initialized=_run_init_cb_for_run_with_proto(op),
        )


def _run_init_cb_for_run_with_proto(op):
    def f(_op, run):
        _copy_run_proto_sourcecode(op._run, op, run)
        _copy_run_proto_attrs(op._run, run)

    return f


def _copy_run_proto_sourcecode(proto_run, proto_op, dest_run):
    if os.getenv("NO_SOURCECODE") == "1":
        log.debug("NO_SOURCECODE=1, skipping sourcecode copy")
        return
    src = os.path.join(proto_run.dir, proto_op._sourcecode_root)
    if not os.path.exists(src):
        log.debug("no sourcecode source (%s), skipping sourcecode copy", src)
        return
    dest = os.path.join(dest_run.dir, proto_op._sourcecode_root)
    log.debug(
        "copying source code files for run %s from %s to %s",
        dest_run.id,
        src,
        dest,
    )
    util.copytree(src, dest)


def _copy_run_proto_attrs(proto_run, dest_run):
    run_proto_attrs = [
        "sourcecode_digest",
        "vcs_commit",
        "host",
        "user",
        "platform",
        "pip_freeze",
    ]
    for attr in run_proto_attrs:
        if not proto_run.has_attr(attr):
            continue
        dest_run.write_attr(attr, proto_run.get(attr))


# =================================================================
# State - batch op
# =================================================================


def _state_init_batch_op(S):
    """Initialize state for batch op.

    A batch is initialized for an operation if batch-triggering flag
    values are specified or if an optimizer is specified. Once
    triggered, a batch op is initialized similarly to a user op
    (e.g. see `_state_init_user_op`).

    If a batch is initialized by this function, `S.batch_op` will be
    non-None.
    """
    _batch_op_init_run(S)
    _batch_op_init_opdef(S)
    _check_opt_flags_for_missing_batch_opdef(S)
    _check_batch_args_for_missing_batch_op(S)
    if S.batch_op:
        _op_init_op_cmd(S.batch_op)
        _op_init_user_flags(S.args.opt_flags, S.batch_op)
        _op_init_op_flags(S.args, S.batch_op)
        _op_init_config(
            S.args.batch_label,
            S.args.batch_tags,
            S.args.batch_comment,
            S.args.edit_batch_comment,
            S.batch_op,
            is_batch=True,
        )
        _op_init_batch_config(S.args, S.user_op, S.batch_op)
        _apply_batch_flag_encoder(S.batch_op, S.user_op)
        _op_init_core(S.args, S.batch_op)
    else:
        _check_unused_batch_args(S.args)


def _batch_op_init_run(S):
    assert not (S.restart_run and S.proto_run)
    if S.restart_run and S.restart_run.batch_proto:
        _batch_op_init_run_(S, S.restart_run)
    elif S.proto_run and S.proto_run.batch_proto:
        _batch_op_init_run_(S, S.proto_run)
        S.batch_op._run_is_proto = True


def _batch_op_init_run_(S, run):
    if S.batch_op is None:
        S.batch_op = Operation()
    S.batch_op._run = run


def _batch_op_init_opdef(S):
    if S.batch_op and S.batch_op._run:
        assert not S.args.optimizer and not S.args.optimize
        # As with user op, we need opdef for restart/run-with-proto
        # when user specifies flags valuesor when force-sourcecode is
        # specified. We check args here rather than S.batch_op because
        # we can't process batch user flags until we know we have a
        # batch op, which is determined in part by this function.
        if S.args.opt_flags or S.args.force_sourcecode:
            S.batch_op._opdef = _opdef_for_run(S.batch_op._run)
    elif S.user_op._opdef:
        _batch_op_init_for_opdef(S.user_op._opdef, S)


def _batch_op_init_for_opdef(opdef, S):
    if S.args.optimizer:
        _batch_op_init_for_named_optimizer(S.args.optimizer, opdef, S)
    elif S.args.optimize:
        _batch_op_init_for_opdef_default_optimizer(opdef, S)
    else:
        _try_implied_batch_op_init(S.user_op, S)


def _batch_op_init_for_named_optimizer(name, opdef, S):
    assert not S.batch_op
    optdef = opdef.get_optimizer(name)
    S.batch_op = Operation()
    if optdef:
        _op_init_for_optimizer(optdef, S.batch_op)
    else:
        _op_init_for_optimizer_opspec(name, S.batch_op)


def _op_init_for_optimizer(optdef, op):
    op._opdef = opdef_for_opspec(optdef.opspec)
    if optdef.flags:
        op._op_flag_vals.update(optdef.flags)


def _op_init_for_optimizer_opspec(opspec, op):
    op._opdef = opdef_for_opspec(opspec)


def _batch_op_init_for_opdef_default_optimizer(opdef, S):
    assert not S.batch_op
    S.batch_op = Operation()
    optdef = util.find_apply(
        [
            lambda: opdef.default_optimizer,
            lambda: _default_optimizer(opdef),
        ]
    )
    _op_init_for_optimizer(optdef, S.batch_op)


def _default_optimizer(opdef):
    return guildfile.OptimizerDef.for_name(DEFAULT_OPTIMIZER, opdef)


def _try_implied_batch_op_init(user_op, S):
    batch_opspec = util.find_apply(
        [
            lambda: _batch_opspec_for_flags(user_op._op_flag_vals),
            lambda: _batch_opspec_for_trials(user_op._batch_trials),
        ]
    )
    if batch_opspec:
        assert not S.batch_op
        S.batch_op = Operation()
        S.batch_op._opdef = opdef_for_opspec(batch_opspec)


def _batch_opspec_for_flags(flag_vals):
    has_list = False
    for val in flag_vals.values():
        if flag_util.is_flag_function(val):
            return "random"
        has_list = has_list or isinstance(val, list)
    if has_list:
        return "+"
    return None


def _batch_opspec_for_trials(trials):
    return "+" if trials else None


def _check_opt_flags_for_missing_batch_opdef(S):
    if S.args.opt_flags and not (S.batch_op and S.batch_op._opdef):
        _opt_flags_for_missing_batch_opdef_error(S.args.opt_flags)


def _check_batch_args_for_missing_batch_op(S):
    if S.batch_op:
        return
    if S.args.max_trials:
        log.warning("not a batch run - ignoring --max-trials")


def _op_init_batch_config(args, user_op, batch_op):
    _op_init_max_trials(args, batch_op)
    _op_init_objective(args, user_op, batch_op)
    _op_init_batch_cmd_run_attrs(args, batch_op)


def _op_init_max_trials(args, op):
    if op._run:
        op._max_trials = args.max_trials or op._run.get("max_trials")
    else:
        op._max_trials = args.max_trials or _default_max_trials_for_op(op)


def _default_max_trials_for_op(op):
    if not op._opdef:
        return None
    return op._opdef.default_max_trials


def _op_init_objective(args, user_op, batch_op):
    assert not (args.minimize and args.maximize)
    if args.minimize:
        batch_op._objective = args.minimize
    elif args.maximize:
        batch_op._objective = "-" + args.maximize
    elif user_op._opdef:
        batch_op._objective = _objective_for_opdef(user_op._opdef)


def _objective_for_opdef(opdef):
    obj = opdef.objective
    if isinstance(obj, six.string_types):
        return obj
    elif isinstance(obj, dict):
        if "maximize" in obj:
            return "-" + obj["maximize"]
        elif "minimize" in obj:
            return obj["minimize"]
    return DEFAULT_OBJECTIVE


def _op_init_batch_cmd_run_attrs(args, op):
    if op._run:
        _apply_stage_trials(
            args.stage_trials or op._run.get("stage_trials"), op._op_cmd_run_attrs
        )
        op._op_cmd_run_attrs["stage_trials"] = args.stage_trials or op._run.get(
            "stage_trials"
        )
    else:
        _apply_stage_trials(args.stage_trials, op._op_cmd_run_attrs)


def _apply_stage_trials(flag, attrs):
    if flag:
        attrs["stage_trials"] = flag


def _apply_batch_flag_encoder(batch_op, user_op):
    """Allow a batch op to encode child op flag vals.

    Applies only when starting a new run (i.e. is not a restart or
    run-with-proto) and opdefs are available for the batch and user
    ops.

    Encoded values are applies when a batch wants to represent a flag
    value using additional configuration. For example, an optimizer
    will encode search parameters into a value so that search spec can
    be used downstream by the optimizer by decoding the flag value.

    If a flag is specified in `user_flags` it is always accepted as
    is - it is never encoded.
    """
    if (
        batch_op._run
        or not batch_op._opdef
        or not batch_op._opdef.flag_encoder
        or not user_op._opdef
    ):
        return
    encode_flag_val = op_util.op_flag_encoder(batch_op._opdef.flag_encoder)
    if not encode_flag_val:
        return
    for flag_name, flag_val in user_op._op_flag_vals.items():
        if flag_name in user_op._user_flag_vals:
            continue
        flagdef = user_op._opdef.get_flagdef(flag_name)
        if not flagdef:
            continue
        encoded_val = encode_flag_val(flag_val, flagdef)
        user_op._op_flag_vals[flag_name] = encoded_val


def _check_unused_batch_args(args):
    if args.batch_comment or args.edit_batch_comment:
        log.warning("operation is not a batch - ignoring batch comment")


###################################################################
# Main
###################################################################


def main(args):
    _init_env(args)
    S = _init_state(args)
    _dispatch_op(S)


def _init_env(args):
    if args.test_flags:
        os.environ["FLAGS_TEST"] = "1"
        os.environ["NO_IMPORT_FLAGS_CACHE"] = "1"


def _init_state(args):
    _maybe_shift_opspec(args)
    _validate_args(args)
    return _state_for_args(args)


def _maybe_shift_opspec(args):
    # Moves opspec to flags if it looks like a flag assignment
    if args.opspec and "=" in args.opspec:
        args.flags = (args.opspec,) + args.flags
        args.opspec = None


def _validate_args(args):
    _check_incompatible_options(args)
    _check_incompatible_with_restart(args)
    _check_platform_compatibility(args)


def _check_incompatible_options(args):
    incompatible = [
        ("minimize", "maximize"),
        ("no_gpus", "gpus"),
        ("optimize", "optimizer"),
        ("print_cmd", "print_env"),
        ("print_trials", "stage_trials"),
        ("stage", "background"),
        ("stage", "pidfile"),
        ("remote", "background"),
        ("remote", "pidfile"),
        ("remote", "edit_flags"),
        ("remote", "edit_comment"),
        ("remote", "break_"),
        ("remote", "break_on_error"),
    ]
    for a, b in incompatible:
        if getattr(args, a) and getattr(args, b):
            _incompatible_options_error(a, b)


def _check_incompatible_with_restart(args):
    if not args.restart:
        return
    incompatible = [
        ("help_model", "--help-model"),
        ("help_op", "--help-op"),
        ("opspec", "OPERATION"),
        ("optimize", "--optimize"),
        ("optimizer", "--optimizer"),
        ("proto", "--proto"),
        ("run_dir", "--run-dir"),
        ("test_output_scalars", "--test-output-scalars"),
        ("test_sourcecode", "--test-sourcecode"),
        ("test_flags", "--test-flags"),
    ]
    for name, desc in incompatible:
        if getattr(args, name):
            restart_option = "restart" if args.restart else "start"
            _incompatible_with_restart_error(desc, restart_option)


def _check_platform_compatibility(args):
    if (
        (args.background or args.pidfile)
        and util.get_platform() == "Windows"
        and os.getenv("FORCE_RUN_IN_BACKGROUND") != "1"
    ):
        _background_on_windows_error()


###################################################################
# Dispatch op
###################################################################


def _dispatch_op(S):
    if S.args.help_model:
        _print_model_help(S)
    elif S.args.help_op:
        _print_op_help(S)
    elif S.args.test_output_scalars:
        _test_output_scalars(S)
    elif S.args.test_sourcecode:
        _test_sourcecode(S)
    elif S.args.test_flags:
        _test_flags(S)
    else:
        _dispatch_op_cmd(S)


###################################################################
# Model / op help
###################################################################


def _print_model_help(S):
    assert S.user_op._opdef
    helplib.print_model_help(S.user_op._opdef.modeldef)


def _print_op_help(S):
    assert S.user_op._opdef
    helplib.print_op_help(S.user_op._opdef)


###################################################################
# Test output scalars
###################################################################


class TestOutputLogger(summary.TestOutputLogger):
    @staticmethod
    def line(line):
        cli.out(line)

    def pattern_no_matches(self, pattern):
        msg = self._format_pattern_no_matches(pattern)
        cli.out(cli.style(msg, dim=True))

    def pattern_matches(self, pattern, matches, vals):
        msg = self._format_pattern_matches(pattern, matches, vals)
        cli.out(cli.style(msg, fg="yellow"))


def _test_output_scalars(S):
    if _output_scalars_disabled(S.user_op):
        cli.out("Output scalars disabled, nothing to test", err=True)
        return
    output_scalars = S.user_op._output_scalars or summary.DEFAULT_OUTPUT_SCALARS
    input_path = S.args.test_output_scalars
    logger = TestOutputLogger()
    if input_path == "-" and sys.stdin.isatty():
        cli.note(
            "Type patterns and press Enter to test. "
            "Use Ctrl-c or empty line to exit."
        )
    with _open_output(input_path) as f:
        summary.test_output(f, output_scalars, logger)


def _open_output(path):
    if path == "-":
        return util.StdinReader(stop_on_blank_line=sys.stdin.isatty())
    try:
        return open(path, "rb")
    except (IOError, OSError) as e:
        if e.errno == 2:
            cli.error("%s does not exist" % path)
        else:
            cli.error("error opening %s: %s" % (path, e))


###################################################################
# Test source code
###################################################################


def _test_sourcecode(S):
    opdef = S.user_op._opdef
    assert opdef
    logger = _CopyLogger()
    sourcecode_src = opdef.guildfile.dir
    sourcecode_select = op_util.sourcecode_select_for_opdef(opdef)
    op_util.copy_sourcecode(
        sourcecode_src, sourcecode_select, None, handler_cls=logger.handler_cls
    )
    cli.out("Copying from %s" % cmd_impl_support.cwd_desc(logger.root))
    cli.out("Rules:")
    for rule in logger.select.rules:
        cli.out("  %s" % _format_file_select_rule(rule))
    if logger.select.disabled:
        assert not logger.selected, logger.selected
        assert not logger.skipped, logger.skipped
        cli.out("Source code copy disabled")
    else:
        cli.out("Selected for copy:")
        for path in logger.selected:
            cli.out(cli.style("  %s" % path, fg="yellow"))
        cli.out("Skipped:")
        for path in logger.skipped:
            cli.out(cli.style("  %s" % path, dim=True))


class _CopyLogger(object):

    root = None
    select = None

    def __init__(self):
        self.selected = []
        self.skipped = []

    def handler_cls(self, src_root, dest_root, select):
        assert dest_root is None, dest_root
        self.root = os.path.relpath(src_root)
        self.select = select
        return self

    def copy(self, path, _results):
        self.selected.append(os.path.join(self.root, path))

    def ignore(self, path, _results):
        self.skipped.append(os.path.join(self.root, path))


def _format_file_select_rule(rule):
    parts = ["include" if rule.result else "exclude"]
    if rule.type:
        parts.append(rule.type)
    parts.append(", ".join([repr(p) for p in rule.patterns]))
    extras = _format_file_select_rule_extras(rule)
    if extras:
        parts.append(extras)
    return " ".join(parts)


def _format_file_select_rule_extras(rule):
    parts = []
    if rule.regex:
        parts.append("regex")
    if rule.sentinel:
        parts.append("with %r" % rule.sentinel)
    if rule.size_gt:
        parts.append("size > %s" % rule.size_gt)
    if rule.size_lt:
        parts.append("size < %s" % rule.size_lt)
    if rule.max_matches:
        parts.append("max match %s" % rule.max_matches)
    return ", ".join(parts)


###################################################################
# Test flags
###################################################################


def _test_flags(S):
    opdef = S.user_op._opdef
    assert opdef

    def out(parent, attr, indent=0):
        val = getattr(parent, attr)
        prefix = "%s%s:" % (" " * indent, attr.replace("_", "-"))
        if val is None:
            cli.out(prefix)
        else:
            if attr == "choices":
                val = [flag_util.encode_flag_val(c.value) for c in val]
            cli.out("%s %s" % (prefix, flag_util.encode_flag_val(val)))

    out(opdef, "flags_dest")
    out(opdef, "flags_import")
    cli.out("flags:")
    for f in opdef.flags:
        cli.out("  %s:" % f.name)
        for attr in FLAG_TEST_ATTRS:
            out(f, attr, 4)


###################################################################
# Dispatch op command
###################################################################


def _dispatch_op_cmd(S):
    if S.args.print_cmd:
        _print_cmd(S)
    elif S.args.print_env:
        _print_env(S)
    elif S.args.print_trials:
        _print_trials(S)
    elif S.args.save_trials:
        _save_trials(S)
    else:
        _confirm_and_run(S)


###################################################################
# Print op info / save trials
###################################################################


def _print_cmd(S):
    if S.batch_op:
        _print_op_cmd_args(S.batch_op.cmd_args)
        _print_batch_trials_cmd_args(S)
    else:
        _print_op_cmd_args(S.user_op.cmd_args)


def _print_op_cmd_args(args):
    cli.out(" ".join([util.shlex_quote(arg) for arg in args]))


def _print_batch_trials_cmd_args(S):
    _run_tmp_batch(S, {"PRINT_TRIALS_CMD": "1"})


def _run_tmp_batch(S, extra_env):
    assert S.batch_op
    with util.TempDir() as tmp:
        _init_batch_run(S, tmp.path)
        _run_op(S.batch_op, S.args, extra_env)


def _print_env(S):
    _print_op_cmd_env(S.user_op.cmd_env)


def _print_op_cmd_env(env):
    for name, val in sorted(env.items()):
        cli.out("%s=%s" % (name, util.env_var_quote(val)))


def _print_trials(S):
    if not S.batch_op:
        _print_trials_for_non_batch_error()
    _run_tmp_batch(S, {"PRINT_TRIALS": "1"})


def _save_trials(S):
    if not S.batch_op:
        _save_trials_for_non_batch_error()
    path = _save_trials_path(S.args.save_trials)
    cli.out("Saving trials to %s" % util.format_dir(path))
    _run_tmp_batch(S, {"SAVE_TRIALS": os.path.abspath(os.path.expanduser(path))})


def _save_trials_path(save_trials_arg):
    _check_trials_path(save_trials_arg)
    cwd = config.cwd()
    return (
        os.path.join(cwd, save_trials_arg) if cwd not in (".", "") else save_trials_arg
    )


def _check_trials_path(path):
    _, ext = os.path.splitext(path)
    if ext.lower() not in (".csv", ".json", ""):
        cli.error(
            "Unsupported extension '%s' - use '.csv', '.json', or no extension" % ext
        )


###################################################################
# Run
###################################################################


def _confirm_and_run(S):
    if S.args.yes or _confirm_run(S):
        _run(S)


# =================================================================
# Confirm op
# =================================================================


def _confirm_run(S):
    prompt = (
        "You are about to {action} {subject}"
        "{batch_suffix}{remote_suffix}{flags_note}\n"
        "{user_flags}"
        "{optimizer_flags}"
        "Continue?".format(
            action=_preview_op_action(S),
            subject=_preview_op_subject(S),
            batch_suffix=_preview_batch_suffix(S),
            remote_suffix=_preview_remote_suffix(S),
            flags_note=_preview_flags_note(S),
            user_flags=_preview_user_flags(S),
            optimizer_flags=_preview_optimizer_flags(S),
        )
    )
    return cli.confirm(prompt, default=True)


def _preview_op_action(S):
    if S.args.stage:
        return "stage"
    elif S.args.restart:
        return "start"
    else:
        return "run"


def _preview_op_subject(S):
    op_desc = _fmt_opref(S.user_op.opref)
    if S.restart_run:
        return "%s (%s)" % (S.restart_run.id, op_desc)
    else:
        return op_desc


def _fmt_opref(opref):
    return opref.to_opspec(config.cwd())


def _preview_batch_suffix(S):
    if not S.batch_op:
        return ""
    return "".join(
        [
            _batch_desc_preview_part(S.batch_op),
            _batch_qualifier_preview_part(S),
        ]
    )


def _batch_desc_preview_part(op):
    opt_name = op.opref.to_opspec(config.cwd())
    if opt_name == "+":
        return " as a batch"
    elif opt_name in ("random", "skopt:random"):
        return " with random search"
    else:
        return " with '%s' optimizer" % opt_name


def _batch_qualifier_preview_part(S):
    batch_op = S.batch_op
    parts = []
    if batch_op.opref.op_name == "+":
        parts.append(_preview_trials_count(S))
    elif batch_op._max_trials:
        parts.append("max %i trials" % batch_op._max_trials)
    if _is_likey_optimizer(batch_op) and batch_op._objective:
        parts.append(_objective_preview_part(batch_op._objective))
    if not parts:
        return ""
    return " (%s)" % ", ".join(parts)


def _preview_trials_count(S):
    trials_count = _trials_count(S)
    if trials_count == 1:
        return "1 trial"
    else:
        return "%i trials" % trials_count


def _trials_count(S):
    count = len(_op_trials(S.user_op))
    if S.batch_op._max_trials is not None:
        count = min(count, S.batch_op._max_trials)
    return count


def _op_trials(op):
    if op._batch_trials:
        return batch_util.expand_trial_flags(
            op._batch_trials, op._op_flag_vals, op._user_flag_vals, op._random_seed
        )
    else:
        return batch_util.expand_flags(op._op_flag_vals, op._random_seed)


def _is_likey_optimizer(op):
    """Return True if op is likely an optimizer.

    All operations are considered likely except those known to NOT be
    optimizers. These are '+' (the general batch op) and 'random'.

    Ideally the operation would indicate if it is an optimizer but
    Guild doesn't support an interface for this.
    """
    return op.opref.op_name not in ("+", "random")


def _objective_preview_part(obj):
    if obj[:1] == "-":
        return "maximize %s" % obj[1:]
    else:
        return "minimize %s" % obj


def _preview_remote_suffix(S):
    if S.args.remote:
        return " on %s" % S.args.remote
    return ""


def _preview_flags_note(S):
    if S.user_op._op_flag_vals and S.user_op._batch_trials:
        return " (flags below used unless specified in batch trial)"
    return ""


def _preview_user_flags(S):
    return _preview_flags(S.user_op._op_flag_vals, S.user_op._flag_null_labels)


def _preview_flags(flag_vals, null_labels):
    if not flag_vals:
        return ""
    return (
        "\n".join(
            [
                "  %s" % _format_flag(name, val, null_labels)
                for name, val in sorted(flag_vals.items())
            ]
        )
        + "\n"
    )


def _format_flag(name, val, null_labels):
    if val is None:
        formatted = _null_label(name, null_labels)
    else:
        formatted = util.find_apply(
            [_try_format_function, flag_util.encode_flag_val], val
        )
    return "%s: %s" % (name, formatted)


def _try_format_function(val):
    if not isinstance(val, six.string_types):
        return None
    try:
        flag_util.decode_flag_function(val)
    except ValueError:
        return None
    else:
        return val


def _null_label(name, null_labels):
    null_label = null_labels.get(name, "default")
    return flag_util.encode_flag_val(null_label)


def _preview_optimizer_flags(S):
    if not S.batch_op or not S.batch_op._op_flag_vals:
        return ""
    flags_preview = _preview_flags(
        S.batch_op._op_flag_vals, S.batch_op._flag_null_labels
    )
    preview = "Optimizer flags:\n%s" % flags_preview
    return cli.style(preview, dim=True)


# =================================================================
# Run / stage
# =================================================================


def _run(S):
    if S.args.remote:
        _run_remote(S)
    else:
        _run_local(S)


def _run_remote(S):
    _check_remote_script(S.user_op.opref)
    remote_impl_support.run(_remote_args(S))


def _check_remote_script(opref):
    if opref.pkg_type == "script":
        cli.error(
            "cannot run scripts remotely\n"
            "Define an operation in guild.yml that uses %s as the main "
            "module and run that operation instead." % opref.to_opspec(config.cwd())
        )


def _remote_args(S):
    params = S.args.as_kw()
    params["opspec"] = S.user_op.opref.to_opspec()
    if S.restart_run:
        params["restart"] = S.restart_run.id
    return click_util.Args(**params)


def _run_local(S):
    _check_run_needed(S)
    op = _init_op_for_run(S)
    if S.args.stage:
        _stage_op(op, S.args)
    else:
        _run_op(op, S.args)


def _check_run_needed(S):
    if not S.args.needed:
        return
    matching = _remove_failed_runs(_find_matching_runs(S))
    if matching:
        if _restarting_match(matching, S):
            _skip_needed_unchanged_flags_info()
        else:
            _skip_needed_matches_info(matching)
        raise SystemExit(0)


def _find_matching_runs(S):
    if S.batch_op:
        matching = op_util.find_matching_runs(
            S.batch_op.opref, S.batch_op._op_flag_vals
        )
        return _filter_matching_batch_runs(matching, S.user_op)
    else:
        return op_util.find_matching_runs(S.user_op.opref, S.user_op._op_flag_vals)


def _filter_matching_batch_runs(batch_runs, user_op):
    return [
        run
        for run in batch_runs
        if (
            run.batch_proto
            and op_util.is_matching_run(
                run.batch_proto,
                user_op.opref,
                user_op._op_flag_vals,
                include_pending=True,
            )
        )
    ]


def _remove_failed_runs(runs):
    return [run for run in runs if run.status != "error"]


def _restarting_match(matches, S):
    restart_run = S.batch_op._run if S.batch_op else S.user_op._run
    return restart_run and restart_run.id in (run.id for run in matches)


def _init_op_for_run(S):
    if S.batch_op:
        _init_batch_run(S)
        return S.batch_op
    return S.user_op


def _init_batch_run(S, run_dir=None):
    batch_run = oplib.init_run(S.batch_op, run_dir)
    S.batch_op.run_dir = batch_run.dir
    oplib.init_run(S.user_op, batch_run.guild_path("proto"))


def _stage_op(op, args):
    try:
        run = oplib.stage(op, continue_on_deps_error=args.force_deps)
    except op_dep.OpDependencyError as e:
        _op_dependency_error(e)
    else:
        if not args.quiet:
            _print_staged_info(run)


def _print_staged_info(run):
    if _staged_outside_guild_home(run):
        _print_staged_dir_instructions(run)
    else:
        _print_stage_pending_instructions(run)


def _staged_outside_guild_home(run):
    return not util.compare_paths(os.path.dirname(run.dir), var.runs_dir())


def _print_staged_dir_instructions(run):
    cmd_args = run.get("cmd") or []
    cmd = " ".join([util.shlex_quote(arg) for arg in cmd_args])
    cli.out(
        "{op} staged in '{dir}'\n"
        "To start the operation, use "
        "\"(cd '{dir}' && source .guild/ENV && {cmd})\"".format(
            op=run_util.format_operation(run), dir=run.dir, cmd=cmd
        )
    )


def _print_stage_pending_instructions(run):
    cli.out(
        "{op} staged as {run_id}\n"
        "To start the operation, use 'guild run --start {run_id}'".format(
            op=run_util.format_operation(run), run_id=run.id
        )
    )


def _run_op(op, args, extra_env=None):
    try:
        _, exit_status = oplib.run(
            op,
            quiet=args.quiet,
            pidfile=_op_pidfile(args),
            stop_after=args.stop_after,
            extra_env=extra_env,
            continue_on_deps_error=args.force_deps,
        )
    except op_dep.OpDependencyError as e:
        _op_dependency_error(e)
    except oplib.ProcessError as e:
        _op_process_error(op, e)
    else:
        _handle_run_exit(exit_status)


def _op_pidfile(args):
    if args.pidfile:
        return args.pidfile
    elif args.background:
        return util.TempFile("guild-pid-").path
    else:
        return None


def _handle_run_exit(exit_status):
    sys.stdout.flush()
    if exit_status != 0:
        cli.error(exit_status=exit_status)


###################################################################
# Error handlers / user messages
###################################################################


def _incompatible_options_error(a, b):
    cli.error(
        "--%s and --%s cannot both be used\n"
        "Try 'guild run --help' for more information."
        % (a.replace("_", "-"), b.replace("_", "-"))
    )


def _incompatible_with_restart_error(option, restart_option):
    cli.error(
        "%s cannot be used with --%s\n"
        "Try 'guild run --help' for more information." % (option, restart_option)
    )


def _background_on_windows_error():
    cli.error("Run in background is not supported on Windows.")


def _invalid_opspec_error(opspec):
    cli.error(
        "invalid operation '%s'\n"
        "Try 'guild operations' for a list of available operations." % opspec
    )


def _guildfile_error(gf_path, msg):
    log.error(msg)
    if os.path.basename(gf_path) == "guild.yml":
        gf_path = os.path.dirname(gf_path)
    cli.error(
        "guildfile in %s contains an error (see above for details)"
        % cmd_impl_support.cwd_desc(gf_path)
    )


def _missing_run_opdef_error(opspec, run):
    cli.error(
        "cannot find definition for operation '%s' in run %s\n"
        "The definition is required when setting flags for start or restart."
        "" % (opspec, run.id)
    )


def _no_such_model_op_error(opspec):
    if opspec:
        if ":" in opspec:
            cli.error(
                "cannot find operation %s\n"
                "Try 'guild operations' for a list of available operations." % opspec
            )
        else:
            cli.error(
                "cannot find operation %s\n"
                "You may need to include a model in the form MODEL:OPERATION. "
                "Try 'guild operations' for a list of available operations." % opspec
            )
    else:
        cli.error(
            "cannot find a default operation\n" "Try 'guild operations' for a list."
        )


def _multiple_models_error(model_ref, models):
    models_list = "\n".join(
        ["  %s" % name for name in sorted([m.fullname for m in models])]
    )
    cli.error(
        "there are multiple models that match '%s'\n"
        "Try specifying one of the following:\n"
        "%s" % (model_ref, models_list)
    )


def _no_such_opdef_error(model, op_name):
    op = "operation '{0}'".format(op_name) if op_name else "a default operation"
    if model.name:
        cli.error(
            "{op} is not defined for model '{model}'\n"
            "Try 'guild operations {model}' for a list of available "
            "operations.".format(op=op, model=model.name)
        )
    else:
        cli.error(
            "{op} is not defined for this project\n"
            "Try 'guild operations' for a list of available operations.".format(op=op)
        )


def _invalid_flag_arg_error(arg):
    cli.error("invalid argument '%s' - expected NAME=VAL" % arg)


def _no_such_flag_error(name, opdef):
    cli.error(
        "unsupported flag '%s'\n"
        "Try 'guild run %s --help-op' for a list of "
        "flags or use --force-flags to skip this check." % (name, opdef.fullname)
    )


def _coerce_flag_val_error(e):
    cli.error("cannot apply %r to flag '%s': %s" % (e.value, e.flag_name, e.error))


def _missing_required_flags_error(e):
    cli.out("Operation requires the following missing flags:\n", err=True)
    line1 = lambda s: s.split("\n")[0]
    cli.table(
        [{"name": flag.name, "desc": line1(flag.description)} for flag in e.missing],
        ["name", "desc"],
        indent=2,
        err=True,
    )
    cli.out(
        "\nRun the command again with these flags specified " "as NAME=VAL.", err=True
    )
    cli.error()


def _invalid_flag_choice_error(e):
    cli.out(
        "Unsupported value for '%s' - supported values are:\n" % e.flag.name, err=True
    )
    cli.table(
        [
            {"val": choice.value, "desc": choice.description}
            for choice in e.flag.choices
        ],
        ["val", "desc"],
        indent=2,
        err=True,
    )
    cli.out("\nRun the command again using one of these options.", err=True)
    cli.error()


def _invalid_flag_value_error(e):
    cli.error("invalid value %s for %s: %s" % (e.value, e.flag.name, e.msg))


def _invalid_opdef_error(opdef, msg):
    cli.error("invalid definition for operation '%s': %s" % (opdef.fullname, msg))


def _model_op_proxy_error(e):
    cli.error("cannot run '%s': %s" % (e.opspec, e.msg))


def _op_cmd_error(msg):
    cli.error(msg)


def _op_dependency_error(e):
    cli.error("run failed because a dependency was not met: %s" % e)


def _op_process_error(op, e):
    cli.error("error running %s: %s" % (_fmt_opref(op.opref), e))


def _opt_flags_for_missing_batch_opdef_error(args):
    assert args
    cli.error("invalid optimizer flag %s: no optimizer specified" % args[0])


def _missing_op_config_for_restart_error(run):
    cli.error(
        "cannot restart run in %s: missing op configuration\n"
        "The run may not have been initialized correctly. Try starting "
        "the operation without the --start/--restart flag." % run.dir
    )


def _invalid_op_config_for_restart_error(run):
    cli.error(
        "cannot restart run in %s: invalid op configuration\n"
        "This may be an internal error. Please open an issue "
        "https://github.com/guildai/guildai/issues." % run.dir
    )


def _no_such_batch_file_error(path):
    cli.error("batch file %s does not exist" % path)


def _batch_file_error(e):
    cli.error(e)


def _flag_for_resolved_dep_error(flag_name, run):
    cli.error(
        "cannot specify a value for '%s' when restarting %s - "
        "resource has already been resolved" % (flag_name, run.short_id)
    )


def _print_trials_for_non_batch_error():
    cli.error("cannot print trials for a non-batch operation")


def _save_trials_for_non_batch_error():
    cli.error("cannot save trials for a non-batch operation")


def _skip_needed_unchanged_flags_info():
    cli.out("Skipping run because flags have not changed " "(--needed specified)")


def _skip_needed_matches_info(matching_runs):
    cli.out(
        "Skipping because the following runs match "
        "this operation (--needed specified):"
    )
    formatted = [run_util.format_run(run) for run in matching_runs]
    cols = ["index", "operation", "started", "status_with_remote", "label"]
    cli.table(formatted, cols=cols, indent=2)


###################################################################
# Cmd impl API
###################################################################


def run(start=None, **kw):
    from .run import run as run_cmd

    if start is not None:
        raise ValueError("start kw not supported, use restart instead")
    ctx = run_cmd.make_context("", [])
    ctx.params.update(kw)
    ctx.params["yes"] = True
    args = click_util.Args(**ctx.params)
    main(args)


def one_run(run_id_prefix):
    runs = [runlib.Run(id, path) for id, path in var.find_runs(run_id_prefix)]
    return cmd_impl_support.one_run(runs, run_id_prefix)
