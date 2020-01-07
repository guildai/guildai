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

import csv
import importlib
import logging
import os

import yaml

from guild import config
from guild import guildfile
from guild import file_util
from guild import flag_util
from guild import model_proxy
from guild import op_cmd as op_cmd_lib
from guild import op_dep
from guild import plugin as pluginlib
from guild import run as runlib
from guild import util
from guild import var
from guild import vcs_util

# TEMP imports until promoted to op_util
from .op_util_legacy import ArgValueError  # pylint: disable=unused-import
from .op_util_legacy import FlagError  # pylint: disable=unused-import
from .op_util_legacy import InvalidFlagChoice  # pylint: disable=unused-import
from .op_util_legacy import InvalidFlagValue  # pylint: disable=unused-import
from .op_util_legacy import MissingRequiredFlags  # pylint: disable=unused-import
from .op_util_legacy import NO_ARG_VALUE  # pylint: disable=unused-import
from .op_util_legacy import RunOutput  # pylint: disable=unused-import
from .op_util_legacy import args_to_flags  # pylint: disable=unused-import
from .op_util_legacy import coerce_flag_value  # pylint: disable=unused-import
from .op_util_legacy import flag_assign  # pylint: disable=unused-import
from .op_util_legacy import flag_assigns  # pylint: disable=unused-import
from .op_util_legacy import flags_desc  # pylint: disable=unused-import
from .op_util_legacy import global_dest  # pylint: disable=unused-import
from .op_util_legacy import init_logging  # pylint: disable=unused-import
from .op_util_legacy import mapped_flag_vals  # pylint: disable=unused-import
from .op_util_legacy import opdef_model_paths  # pylint: disable=unused-import
from .op_util_legacy import parse_flag_assigns  # pylint: disable=unused-import
from .op_util_legacy import parse_opspec  # pylint: disable=unused-import
from .op_util_legacy import print_trials  # pylint: disable=unused-import
from .op_util_legacy import restart_needed  # pylint: disable=unused-import
from .op_util_legacy import run_params_for_restart  # pylint: disable=unused-import
from .op_util_legacy import save_trials  # pylint: disable=unused-import
from .op_util_legacy import split_args_for_flags  # pylint: disable=unused-import
from .op_util_legacy import split_cmd  # pylint: disable=unused-import
from .op_util_legacy import split_main  # pylint: disable=unused-import
from .op_util_legacy import validate_flag_vals  # pylint: disable=unused-import

log = logging.getLogger("guild")

MAX_DEFAULT_SOURCECODE_FILE_SIZE = 1024 * 1024
MAX_DEFAULT_SOURCECODE_COUNT = 100

DEFAULT_EXEC = "${python_exe} -um guild.op_main ${main_args} -- ${flag_args}"
STEPS_EXEC = "${python_exe} -um guild.steps_main"

###################################################################
# Error classes
###################################################################


class OpDefLookupError(LookupError):
    pass


class InvalidOpSpec(OpDefLookupError):
    def __init__(self, opspec):
        super(InvalidOpSpec, self).__init__(opspec)
        self.opspec = opspec


class NoSuchModel(OpDefLookupError):
    def __init__(self, opspec):
        super(NoSuchModel, self).__init__(opspec)
        self.opspec = opspec


class NoSuchOperation(OpDefLookupError):
    def __init__(self, model, op_name):
        super(NoSuchOperation, self).__init__(model, op_name)
        self.model = model
        self.op_name = op_name


class CwdGuildfileError(OpDefLookupError):
    def __init__(self, guildfile_error):
        super(CwdGuildfileError, self).__init__(guildfile_error)
        self.msg = guildfile_error.msg
        self.path = guildfile_error.path


class MultipleMatchingModels(OpDefLookupError):
    def __init__(self, model_ref, matches):
        super(MultipleMatchingModels, self).__init__(model_ref, matches)
        self.model_ref = model_ref
        self.matches = matches


class NoMatchingModel(OpDefLookupError):
    def __init__(self, model_ref):
        super(NoMatchingModel, self).__init__(model_ref)
        self.model_ref = model_ref


class ModelOpProxyError(Exception):
    def __init__(self, opspec, msg):
        super(ModelOpProxyError, self).__init__(opspec, msg)
        self.opspec = opspec
        self.msg = msg


class NoSuchFlagError(FlagError):
    def __init__(self, flag_name):
        super(NoSuchFlagError, self).__init__(flag_name)
        self.flag_name = flag_name


class InvalidOpDef(ValueError):
    def __init__(self, opdef, msg):
        super(InvalidOpDef, self).__init__(opdef, msg)
        self.opdef = opdef
        self.msg = msg

    def __str__(self):
        return "invalid definition for %s: %s" % (self.opdef.fullname, self.msg)


class OpCmdError(Exception):
    pass


class BatchFileError(Exception):
    def __init__(self, path, msg):
        super(BatchFileError, self).__init__(path, msg)
        self.path = path
        self.msg = msg

    def __str__(self):
        return "cannot read trials for %s: %s" % (self.path, self.msg)


###################################################################
# OpDef for spec
###################################################################


def opdef_for_opspec(opspec):
    try:
        return _model_opdef(opspec)
    except OpDefLookupError:
        opdef = _try_model_proxy(opspec)
        if not opdef:
            raise
        return opdef


def _model_opdef(opspec):
    model, op_name = _model_op(opspec)
    opdef = _opdef_for_model_op(model, op_name)
    if not opdef:
        raise NoSuchOperation(model, op_name)
    opdef.set_modelref(model.reference)
    return opdef


def _try_model_proxy(opspec):
    if not opspec:
        return None
    try:
        model, op_name = model_proxy.resolve_model_op(opspec)
    except model_proxy.NotSupported:
        return None
    except model_proxy.OpSpecError as e:
        raise ModelOpProxyError(opspec, str(e))
    else:
        opdef = model.modeldef.get_operation(op_name)
        if opdef:
            opdef.set_modelref(model.reference)
        return opdef


def _model_op(opspec):
    model_ref, op_name = _parse_opspec(opspec)
    model = _resolve_model(model_ref)
    if not model:
        raise NoSuchModel(opspec)
    return model, op_name


def _parse_opspec(opspec):
    parsed = parse_opspec(opspec)
    if parsed is None:
        raise InvalidOpSpec(opspec)
    return parsed


def _resolve_model(model_ref):
    return util.find_apply([_resolve_cwd_model, _resolve_system_model,], model_ref)


def _resolve_cwd_model(model_ref):
    from guild import model as modellib  # expensive

    cwd_guildfile = _cwd_guildfile()
    if not cwd_guildfile:
        return None
    with modellib.SetPath([cwd_guildfile.dir], clear_cache=True):
        return _match_one_model(model_ref, cwd_guildfile)


def _cwd_guildfile():
    try:
        return guildfile.for_dir(config.cwd())
    except guildfile.NoModels as e:
        return None
    except guildfile.GuildfileError as e:
        raise CwdGuildfileError(e)


def _resolve_system_model(model_ref):
    return _match_one_model(model_ref)


def _match_one_model(model_ref, cwd_guildfile=None):
    matches = list(_iter_matching_models(model_ref, cwd_guildfile))
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 0 and model_ref:
        return _complete_match_one_model(model_ref, matches)
    return None


def _iter_matching_models(model_ref, cwd_guildfile):
    from guild import model as modellib  # expensive

    for model in modellib.iter_models():
        if model_ref:
            if _match_model_ref(model_ref, model):
                yield model
        else:
            if cwd_guildfile and _is_default_cwd_model(model, cwd_guildfile):
                yield model
                break
            if not model.name:
                yield model


def _is_default_cwd_model(model, cwd_guildfile):
    default_model = cwd_guildfile.default_model
    return (
        default_model
        and default_model.guildfile.dir == model.modeldef.guildfile.dir
        and default_model.name == model.name
    )


def _match_model_ref(model_ref, model):
    if "/" in model_ref:
        return model_ref in model.fullname
    else:
        return model_ref in model.name


def _complete_match_one_model(model_ref, matches):
    complete_match = _model_by_name(model_ref, matches)
    if complete_match:
        return complete_match
    raise MultipleMatchingModels(model_ref, matches)


def _model_by_name(name, models):
    for model in models:
        if model.name == name:
            return model
    return None


def _maybe_no_model_error(model_ref):
    if model_ref:
        raise NoMatchingModel(model_ref)
    return None


def _opdef_for_model_op(model, op_name):
    if op_name:
        return model.modeldef.get_operation(op_name)
    return model.modeldef.default_operation


###################################################################
# Run support
###################################################################


def init_run(path=None):
    if not path:
        run_id = runlib.mkid()
        path = os.path.join(var.runs_dir(), run_id)
    else:
        run_id = os.path.basename(path)
    return runlib.Run(run_id, path)


def set_run_marker(run, marker):
    open(run.guild_path(marker), "w").close()


def clear_run_marker(run, marker):
    util.ensure_deleted(run.guild_path(marker))


def set_run_pending(run):
    set_run_marker(run, "PENDING")


def clear_run_pending(run):
    clear_run_marker(run, "PENDING")


def write_sourcecode_digest(run):
    digest = file_util.files_digest(run.guild_path("sourcecode"))
    run.write_attr("sourcecode_digest", digest)


def write_vcs_commit(opdef, run):
    if not opdef.guildfile.dir:
        return
    try:
        commit, status = vcs_util.commit_for_dir(opdef.guildfile.dir)
    except vcs_util.NoCommit:
        pass
    except vcs_util.CommitReadError as e:
        log.warning("error reading VCS commit: %s", e)
    else:
        run.write_attr("vcs_commit", _format_vcs_commit(commit, status))


def _format_vcs_commit(commit, status):
    if status:
        return commit + "*"
    return commit


def set_run_started(run):
    started = runlib.timestamp()
    run.write_attr("started", started)


def set_run_staged(run):
    set_run_marker(run, "STAGED")
    clear_run_pending(run)
    set_run_started(run)


def run_label(label_template, user_flag_vals, all_flag_vals=None):
    all_flag_vals = all_flag_vals or user_flag_vals
    if not label_template:
        return _default_run_label(all_flag_vals)
    return _render_label_template(label_template, all_flag_vals)


def _default_run_label(flag_vals):
    non_null = {name: val for name, val in flag_vals.items() if val is not None}
    return " ".join(
        flag_util.format_flags(non_null, truncate_floats=True, shorten_paths=True)
    )


def _render_label_template(label_template, flag_vals):
    resolve_vals = {
        name: flag_util.encode_flag_val(val)
        for name, val in flag_vals.items()
        if val is not None
    }
    return util.resolve_refs(label_template, resolve_vals, "")


###################################################################
# Source code support
###################################################################


def sourcecode_select_for_opdef(opdef):
    root = _opdef_sourcecode_root(opdef)
    rules = _select_rules_for_opdef(opdef)
    return file_util.FileSelect(root, rules)


def _opdef_sourcecode_root(opdef):
    return opdef.sourcecode.root or opdef.modeldef.sourcecode.root


def _select_rules_for_opdef(opdef):
    if _sourcecode_disabled(opdef):
        return [file_util.exclude("*")]
    root = _opdef_select_rules_root(opdef)
    return (
        _base_sourcecode_select_rules()
        + _sourcecode_config_rules(opdef.modeldef.sourcecode, root)
        + _sourcecode_config_rules(opdef.sourcecode, root)
    )


def _opdef_select_rules_root(opdef):
    root_base = opdef.guildfile.dir
    sourcecode_root = opdef_sourcecode_root(opdef)
    if not sourcecode_root:
        return root_base
    return os.path.join(root_base, sourcecode_root)


def _sourcecode_disabled(opdef):
    op_config = opdef.sourcecode
    model_config = opdef.modeldef.sourcecode
    return op_config.disabled or model_config.disabled and not op_config.specs


def opdef_sourcecode_root(opdef):
    return opdef.sourcecode.root or opdef.modeldef.sourcecode.root


def _base_sourcecode_select_rules():
    return [
        _rule_exclude_pycache_dirs(),
        _rule_exclude_dot_dirs(),
        _rule_exclude_nocopy_dirs(),
        _rule_exclude_venv_dirs(),
        _rule_exclude_build_dirs(),
        _rule_exclude_egg_info_dirs(),
        _rule_include_limited_text_files(),
    ]


def _rule_exclude_pycache_dirs():
    return file_util.exclude("__pycache__", type="dir")


def _rule_exclude_dot_dirs():
    return file_util.exclude(".*", type="dir")


def _rule_exclude_nocopy_dirs():
    return file_util.exclude("*", type="dir", sentinel=".guild-nocopy")


def _rule_exclude_venv_dirs():
    return file_util.exclude("*", type="dir", sentinel="bin/activate")


def _rule_exclude_build_dirs():
    return file_util.exclude("build", type="dir")


def _rule_exclude_egg_info_dirs():
    return file_util.exclude("*.egg-info", type="dir")


def _rule_include_limited_text_files():
    return file_util.include(
        "*",
        type="text",
        size_lt=MAX_DEFAULT_SOURCECODE_FILE_SIZE + 1,
        max_matches=MAX_DEFAULT_SOURCECODE_COUNT,
    )


def _sourcecode_config_rules(config, root):
    return [_rule_for_select_spec(spec, root) for spec in config.specs]


def _rule_for_select_spec(spec, root):
    if spec.type == "include":
        return _file_util_rule(file_util.include, spec, root)
    elif spec.type == "exclude":
        return _file_util_rule(file_util.exclude, spec, root)
    else:
        assert False, spec.type


def _file_util_rule(rule_f, spec, root):
    patterns = _spec_patterns(spec, root)
    return rule_f(patterns, type=spec.patterns_type)


def _spec_patterns(spec, root):
    """Returns patterns for spec.

    If spec patterns_type is not specified, applies glob to and
    existing patterns that reference directories relative to root. For
    example, if a pattern is 'foo' and root is '/' and the directory
    '/foo' exists, the pattern is returned as 'foo/*'. This is a
    convenience so that un-globbed directories match all files as a
    user might expect.
    """
    if spec.patterns_type:
        return spec.patterns
    return [_apply_dir_glob(root, p) for p in spec.patterns]


def _apply_dir_glob(root, pattern):
    if os.path.isdir(os.path.join(root, pattern)):
        pattern = os.path.join(pattern, "*")
    return pattern


def copy_sourcecode(sourcecode_src, sourcecode_select, dest_dir, handler_cls=None):
    handler_cls = handler_cls or SourceCodeCopyHandler
    file_util.copytree(
        dest_dir, sourcecode_select, sourcecode_src, handler_cls=handler_cls
    )


class SourceCodeCopyHandler(file_util.FileCopyHandler):
    """Handler to log warnings when soure code files are skipped.

    Only logs warnings when the default rules are in effect.
    """

    _warned_max_matches = False

    _warning_help_suffix = (
        " To control which files are copied, define 'sourcecode' "
        "for the operation in a Guild file."
    )

    def ignore(self, path, rule_results):
        fullpath = os.path.join(self.src_root, path)
        if self._default_rules_in_effect(rule_results):
            assert len(rule_results) == 1, rule_results
            (_path, failed_test), _rule = rule_results[0]
            if failed_test.name == "max matches":
                self._warn_max_matches()
            elif failed_test.name == "size":
                self._warn_max_size(fullpath)

    @staticmethod
    def _default_rules_in_effect(results):
        return (
            len(results) == 1
            and results[0][1].result is True
            and results[0][1].size_lt == MAX_DEFAULT_SOURCECODE_FILE_SIZE + 1
            and results[0][1].max_matches == MAX_DEFAULT_SOURCECODE_COUNT
        )

    def _warn_max_matches(self):
        if self._warned_max_matches:
            return
        log.warning(
            "Found more than %i source code files but will only "
            "copy %i as a safety measure.%s",
            MAX_DEFAULT_SOURCECODE_COUNT,
            MAX_DEFAULT_SOURCECODE_COUNT,
            self._warning_help_suffix,
        )
        self._warned_max_matches = True

    def _warn_max_size(self, path):
        log.warning(
            "Skipping potential source code file %s because it's " "too big.%s",
            path,
            self._warning_help_suffix,
        )


###################################################################
# Op command support
###################################################################


def op_cmd_for_opdef(opdef, extra_cmd_env=None):
    """Returns tuple of op cmd for opdef and associated run attrs.

    Some operations require additional information from the opdef,
    which is returned as the second element of the two-tuple.
    """
    extra_cmd_env = extra_cmd_env or {}
    cmd_args, run_attrs = _op_cmd_args_and_run_attrs(opdef)
    cmd_env = _op_cmd_env(opdef, extra_cmd_env)
    cmd_flags = _op_cmd_flags(opdef)
    op_cmd = op_cmd_lib.OpCmd(cmd_args, cmd_env, cmd_flags)
    return op_cmd, run_attrs


def _op_cmd_args_and_run_attrs(opdef):
    main_args = split_cmd(opdef.main or "")
    exec_str, run_attrs = _opdef_exec_and_run_attrs(opdef)
    exec_args = split_cmd(exec_str)
    _apply_main_args(main_args, exec_args)
    _apply_flag_args_marker(exec_args)
    return exec_args, run_attrs


def _opdef_exec_and_run_attrs(opdef):
    """Returns exec template for opdef with required run attrs for opdef.

    If exec is specified explicitly, it's returned, otherwise main or
    steps are used to generate a template.
    """
    if opdef.exec_:
        if opdef.main:
            log.warning(
                "operation 'exec' and 'main' both specified, " "ignoring 'main'"
            )
        if opdef.steps:
            log.warning(
                "operation 'exec' and 'steps' both specified, " "ignoring 'steps'"
            )
        return opdef.exec_, None
    elif opdef.main:
        if opdef.steps:
            log.warning(
                "operation 'main' and 'steps' both specified, " "ignoring 'steps'"
            )
        return DEFAULT_EXEC, None
    elif opdef.steps:
        return STEPS_EXEC, _run_attrs_for_steps(opdef)
    else:
        raise InvalidOpDef(opdef, "must define either exec, main, or steps")


def _run_attrs_for_steps(opdef):
    return {
        "steps": opdef.steps,
    }


def _apply_main_args(main_args, exec_args):
    i = 0
    while i < len(exec_args):
        if exec_args[i] == "${main_args}":
            exec_args[i : i + 1] = main_args
            i += len(main_args)
        i += 1


def _apply_flag_args_marker(exec_args):
    for i, val in enumerate(exec_args):
        if val == "${flag_args}":
            exec_args[i] = "__flag_args__"


def _op_cmd_env(opdef, extra_env):
    env = dict(opdef.env or {})
    env.update(extra_env or {})
    env["GUILD_OP"] = opdef.fullname
    env["GUILD_PLUGINS"] = _op_plugins(opdef)
    env["PROJECT_DIR"] = opdef.guildfile.dir or ""
    if opdef.flags_dest:
        env["FLAGS_DEST"] = opdef.flags_dest
    if opdef.handle_keyboard_interrupt:
        env["HANDLE_KEYBOARD_INTERRUPT"] = "1"
    return env


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
                name,
                " (%s)" % reason if reason else "",
            )
            continue
        log.debug(
            "plugin '%s' enabled for operation%s",
            name,
            " (%s)" % reason if reason else "",
        )
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


def _op_cmd_flags(opdef):
    return {flagdef.name: _flag_cmd_for_flagdef(flagdef) for flagdef in opdef.flags}


def _flag_cmd_for_flagdef(flagdef):
    return op_cmd_lib.CmdFlag(
        arg_name=flagdef.arg_name,
        arg_skip=_flagdef_arg_skip(flagdef),
        arg_switch=flagdef.arg_switch,
        env_name=flagdef.env_name,
    )


def _flagdef_arg_skip(flagdef):
    if flagdef.arg_skip is not None:
        return flagdef.arg_skip
    return flagdef.opdef.default_flag_arg_skip


###################################################################
# Flags support
###################################################################


def flag_vals_for_opdef(opdef, user_flag_vals=None, force=False):
    flag_vals = dict(user_flag_vals)
    _apply_default_flag_vals(opdef.flags, flag_vals)
    _apply_coerce_flag_vals(opdef.flags, force, flag_vals)
    resource_flagdefs = _resource_flagdefs(opdef, flag_vals)
    _apply_coerce_flag_vals(resource_flagdefs, force, flag_vals)
    _apply_default_flag_vals(resource_flagdefs, flag_vals)
    all_flagdefs = opdef.flags + resource_flagdefs
    if not force:
        _check_no_such_flags(flag_vals, all_flagdefs)
        _check_flag_vals(flag_vals, all_flagdefs)
        _check_required_flags(flag_vals, all_flagdefs)
    _apply_choices_flag_vals(opdef.flags, user_flag_vals, flag_vals)
    return flag_vals, resource_flagdefs


def _apply_coerce_flag_vals(flagdefs, force, vals):
    flagdef_lookup = {flagdef.name: flagdef for flagdef in flagdefs}
    for name, val in vals.items():
        try:
            coerced = _coerce_flag_value(name, val, flagdef_lookup)
        except InvalidFlagValue:
            if not force:
                raise
        else:
            vals[name] = coerced


def _coerce_flag_value(name, val, flagdefs):
    flagdef = flagdefs.get(name)
    if not flagdef:
        return val
    try:
        return coerce_flag_value(val, flagdef)
    except (ValueError, TypeError) as e:
        raise InvalidFlagValue(val, flagdef, str(e))


def _resource_flagdefs(opdef, flag_vals):
    return list(_iter_resource_flagdefs(opdef, flag_vals))


def _iter_resource_flagdefs(opdef, flag_vals):
    for dep in opdef.dependencies:
        try:
            resdef, _location = op_dep.resource_def(dep, flag_vals)
        except op_dep.OpDependencyError:
            pass
        else:
            if resdef.flag_name:
                yield _ResourceFlagDefProxy(resdef.flag_name, opdef)
            else:
                op_name = _required_operation_name(resdef)
                if op_name:
                    yield _ResourceFlagDefProxy(op_name, opdef)


def _required_operation_name(resdef):
    for source in resdef.sources:
        if source.uri.startswith("operation:"):
            return resdef.name
    return None


def _ResourceFlagDefProxy(name, opdef):
    data = {
        "arg-skip": True,
        "type": "string",
        "null-label": "unspecified",
    }
    return guildfile.FlagDef(name, data, opdef)


def _check_no_such_flags(flag_vals, flagdefs):
    flagdef_names = set([flagdef.name for flagdef in flagdefs])
    for name in flag_vals:
        if name not in flagdef_names:
            raise NoSuchFlagError(name)


def _check_flag_vals(vals, flagdefs):
    for flag in flagdefs:
        val = vals.get(flag.name)
        _check_flag_val(val, flag)


def _check_flag_val(val, flag):
    if isinstance(val, list):
        for x in val:
            _check_flag_val(x, flag)
    elif flag_util.is_flag_function(val):
        pass
    else:
        _check_flag_choice(val, flag)
        _check_flag_type(val, flag)
        _check_flag_range(val, flag)


def _check_flag_choice(val, flag):
    if (
        val
        and flag.choices
        and not flag.allow_other
        and val not in [choice.value for choice in flag.choices]
    ):
        raise InvalidFlagChoice(val, flag)


def _check_flag_type(val, flag):
    if flag.type == "existing-path":
        if val and not os.path.exists(val):
            raise InvalidFlagValue(val, flag, "%s does not exist" % val)


def _check_flag_range(val, flag):
    if val is None:
        return
    if flag.min is not None and val < flag.min:
        raise InvalidFlagValue(val, flag, "out of range (less than min %s)" % flag.min)
    if flag.max is not None and val > flag.max:
        raise InvalidFlagValue(
            val, flag, "out of range (greater than max %s)" % flag.max
        )


def _apply_choices_flag_vals(flagdefs, user_vals, target_vals):
    for flagdef in flagdefs:
        if not flagdef.choices:
            continue
        flag_val = target_vals.get(flagdef.name)
        if flag_val is None:
            continue
        for choice in flagdef.choices:
            if choice.flags and choice.value == flag_val:
                _apply_choice_flags(choice.flags, user_vals, target_vals)


def _apply_choice_flags(choice_flags, user_vals, target_vals):
    for flag_name, flag_val in choice_flags.items():
        if user_vals.get(flag_name) is None:
            target_vals[flag_name] = flag_val


def _check_required_flags(vals, flagdefs):
    missing = _missing_flags(vals, flagdefs)
    if missing:
        raise MissingRequiredFlags(missing)


def _missing_flags(vals, flagdefs):
    return [
        flag
        for flag in flagdefs
        if flag.required and _flag_missing(vals.get(flag.name))
    ]


def _flag_missing(val):
    if val is None or val == "":
        return True
    return False


def _apply_default_flag_vals(flagdefs, flag_vals):
    for flagdef in flagdefs:
        if flag_vals.get(flagdef.name) is None:
            flag_vals[flagdef.name] = flagdef.default


###################################################################
# Op deps IO
###################################################################


def op_deps_as_data(deps):
    return [_op_dep_as_data(dep) for dep in deps or []]


def _op_dep_as_data(dep):
    data = _resdef_data(dep.resdef)
    if dep.res_location:
        data["location"] = dep.res_location
    if dep.config:
        data["config"] = dep.config
    return data


def _resdef_data(resdef):
    data = dict(resdef._data)
    data["name"] = resdef.name
    return data


def op_deps_for_data(data):
    return [_op_dep_for_data(item_data) for item_data in data or []]


def _op_dep_for_data(data):
    resdef = _resdef_from_data(data)
    location = data.get("location")
    config = data.get("config")
    return op_dep.OpDependency(resdef, location, config)


def _resdef_from_data(data):
    name = data.get("name")
    return guildfile.ResourceDef(name, data, _ModelDefProxy())


class _ModelDefProxy(object):
    name = ""
    guildfile = None
    parents = []


###################################################################
# Trials support
###################################################################


def trials_for_batch_files(files):
    trials = []
    for path in files:
        trials.extend(_read_trials(path))
    return trials


def _read_trials(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in (".json", ".yml", ".yaml"):
        return _yaml_trials(path)
    elif ext in ("", ".csv",):
        return _csv_trials(path)
    else:
        raise BatchFileError(path, "unsupported extension")


def _yaml_trials(path):
    try:
        data = yaml.safe_load(open(path, "r"))
    except Exception as e:
        raise BatchFileError(path, str(e))
    else:
        return _coerce_trials_data(data, path)


def _coerce_trials_data(data, path):
    if not isinstance(data, list):
        if not isinstance(data, dict):
            raise BatchFileError(
                path,
                "invalid data type for trials: expected list or dict"
                ", got %s" % type(data).__name__,
            )
        data = [data]
    for item in data:
        if not isinstance(item, dict):
            raise BatchFileError(
                path, "invalid data type for trial %r: expected dict" % item
            )
    return data


def _csv_trials(path):
    reader = csv.reader(open(path, "r"))
    try:
        flag_names = next(reader)
    except StopIteration:
        return []
    else:
        return [dict(zip(flag_names, _flag_vals(row))) for row in reader]


def _flag_vals(row):
    return [flag_util.decode_flag_val(s) for s in row]


###################################################################
# Utils
###################################################################


def split_batch_files(flag_args):
    batch_files = []
    rest = []
    for arg in flag_args:
        if arg[:1] == "@":
            batch_files.append(arg[1:])
        else:
            rest.append(arg)
    return batch_files, rest


def format_label(label, flag_vals):
    formatted_flags = _format_flags_for_label(flag_vals)
    return util.render_label(label, formatted_flags)


def _format_flags_for_label(flag_vals):
    return {name: _format_flag_for_label(val) for name, val in flag_vals.items()}


def _format_flag_for_label(val):
    return flag_util.FormattedValue(val, truncate_floats=True)


def find_matching_runs(opref, flag_vals, include_pending=False):
    return [
        run
        for run in var.runs()
        if is_matching_run(run, opref, flag_vals, include_pending)
    ]


def is_matching_run(run, opref, flag_vals, include_pending=False):
    return (
        run.opref == opref
        and run.get("flags") == flag_vals
        and (include_pending or run.status != "pending")
    )


def op_flag_encoder(flag_encoder):
    if not flag_encoder:
        return None
    parts = flag_encoder.split(":")
    if len(parts) != 2:
        log.warning("invalid flag decoder %r - must be MODULE:FUNCTION", flag_encoder)
        return None
    mod_name, fun_name = parts
    try:
        mod = importlib.import_module(mod_name)
    except Exception as e:
        if log.getEffectiveLevel() <= logging.DEBUG:
            log.exception("importing %s", mod_name)
        else:
            log.warning("cannot load flag decoder %r: %s", flag_encoder, e)
        return None
    fun = getattr(mod, fun_name, None)
    if fun is None:
        log.warning(
            "cannot load flag decoder %r: no such attribute in %s",
            flag_encoder,
            mod_name,
        )
        return None
    return fun
