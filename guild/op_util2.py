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

import six

from guild import config
from guild import guildfile
from guild import file_util
from guild import flag_util
from guild import model_proxy
from guild import run as runlib
from guild import util
from guild import var

# TEMP imports until promoted to op_util
from .op_util import NO_ARG_VALUE           # pylint: disable=unused-import
from .op_util import ArgValueError          # pylint: disable=unused-import
from .op_util import RunOutput              # pylint: disable=unused-import
from .op_util import args_to_flags          # pylint: disable=unused-import
from .op_util import mapped_flag_vals       # pylint: disable=unused-import
from .op_util import opdef_model_paths      # pylint: disable=unused-import
from .op_util import parse_flag_assigns     # pylint: disable=unused-import
from .op_util import parse_opspec           # pylint: disable=unused-import
from .op_util import split_cmd              # pylint: disable=unused-import

log = logging.getLogger("guild")

MAX_DEFAULT_SOURCECODE_FILE_SIZE = 1024 * 1024
MAX_DEFAULT_SOURCECODE_COUNT = 100

###################################################################
# Error classes
###################################################################

class InvalidOpSpec(Exception):

    def __init__(self, opspec):
        super(InvalidOpSpec, self).__init__(opspec)
        self.opspec = opspec

class NoSuchModel(Exception):

    def __init__(self, opspec):
        super(NoSuchModel, self).__init__(opspec)
        self.opspec = opspec

class NoSuchOperation(Exception):

    def __init__(self, model, op_name):
        super(NoSuchOperation, self).__init__(model, op_name)
        self.model = model
        self.op_name = op_name

class CwdGuildfileError(Exception):

    def __init__(self, guildfile_error):
        super(CwdGuildfileError, self).__init__(guildfile_error)
        self.msg = guildfile_error.msg
        self.path = guildfile_error.path

class MultipleMatchingModels(Exception):

    def __init__(self, model_ref, matches):
        super(MultipleMatchingModels, self).__init__(model_ref, matches)
        self.model_ref = model_ref
        self.matches = matches

class NoMatchingModel(Exception):

    def __init__(self, model_ref):
        super(NoMatchingModel, self).__init__(model_ref)
        self.model_ref = model_ref

###################################################################
# Resolve opspec
###################################################################

def opdef_for_opspec(opspec):
    try:
        return _model_opdef(opspec)
    except (NoSuchModel, NoSuchOperation):
        opdef = _try_model_proxy(opspec)
        if opdef:
            return opdef
        raise

def _model_opdef(opspec):
    model, op_name = _model_op(opspec)
    opdef = _opdef_for_model_op(model, op_name)
    if not opdef:
        raise NoSuchOperation(model, op_name)
    opdef.set_modelref(model.reference)
    return opdef

def _try_model_proxy(opspec):
    try:
        model, op_name = model_proxy.resolve_model_op(opspec)
    except model_proxy.NotSupported:
        return None
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
    return util.find_apply([
        _resolve_cwd_model,
        _resolve_system_model,
    ], model_ref)

def _resolve_cwd_model(model_ref):
    from guild import model as modellib # expensive
    cwd_guildfile = _cwd_guildfile()
    if not cwd_guildfile:
        return None
    with modellib.SetPath([cwd_guildfile.dir], clear_cache=True):
        return _match_one_model(model_ref, cwd_guildfile)

def _cwd_guildfile():
    try:
        return guildfile.from_dir(config.cwd())
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
    from guild import model as modellib # expensive
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
    return (default_model and
            default_model.guildfile.dir == model.modeldef.guildfile.dir and
            default_model.name == model.name)

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

def set_run_pending(run):
    open(run.guild_path("PENDING"), "w").close()

def clear_run_pending(run):
    util.ensure_deleted(run.guild_path("PENDING"))

def write_sourcecode_digest(run):
    digest = file_util.files_digest(run.guild_path("sourcecode"))
    run.write_attr("sourcecode_digest", digest)

###################################################################
# Op preview support
###################################################################

def preview_op_kw(op, indent=2):
    return {
        "action": preview_op_action(op),
        "op": preview_op_desc(op),
        "flags": preview_flags(op, indent),
    }

def preview_op_action(op):
    if op.stage:
        return "stage"
    else:
        return "run"

def preview_op_desc(op):
    opspec = op.opref.to_opspec()
    if os.path.isabs(opspec):
        opspec = os.path.relpath(opspec, config.cwd())
    return opspec

def preview_flags(op, indent=2):
    if not op.flag_vals:
        return ""
    return "\n".join([
        " " * indent +_format_flag(name, val, op.flag_null_labels)
        for name, val in sorted(op.flag_vals.items())
    ]) + "\n"

def _format_flag(name, val, null_labels):
    if val is None:
        formatted = _null_label(name, null_labels)
    else:
        formatted = util.find_apply([
            _try_format_function,
            flag_util.encode_flag_val], val)
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
        _base_sourcecode_select_rules() +
        _sourcecode_config_rules(opdef.modeldef.sourcecode, root) +
        _sourcecode_config_rules(opdef.sourcecode, root)
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
    return (
        op_config.disabled or
        model_config.disabled and not op_config.specs)

def opdef_sourcecode_root(opdef):
    return opdef.sourcecode.root or opdef.modeldef.sourcecode.root

def _base_sourcecode_select_rules():
    return [
        _rule_exclude_pycache_dirs(),
        _rule_exclude_dot_dirs(),
        _rule_exclude_nocopy_dirs(),
        _rule_exclude_venv_dirs(),
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

def _rule_include_limited_text_files():
    return file_util.include(
        "*",
        type="text",
        size_lt=MAX_DEFAULT_SOURCECODE_FILE_SIZE + 1,
        max_matches=MAX_DEFAULT_SOURCECODE_COUNT)

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

def copy_sourcecode(sourcecode_src, sourcecode_select, dest_dir,
                    handler_cls=None, config_help=None):
    if handler_cls is None:
        handler_cls = SourceCodeCopyHandler.handler_cls(config_help)
    file_util.copytree(
        dest_dir, sourcecode_select, sourcecode_src,
        handler_cls=handler_cls)

class SourceCodeCopyHandler(file_util.FileCopyHandler):
    """Handler to log warnings when soure code files are skipped.

    Only logs warnings when the default rules are in effect.
    """

    @classmethod
    def handler_cls(cls, config_help):
        def f(src_root, dest_root, select):
            handler = cls(src_root, dest_root, select)
            handler._config_help = config_help
            return handler
        return f

    _config_help = None
    _warned_max_matches = False

    def ignore(self, path, rule_results):
        fullpath = os.path.join(self.src_root, path)
        if self._ignored_max_matches(rule_results):
            self._warn_max_matches()
        if self._ignored_max_size(fullpath, rule_results):
            self._warn_max_size(fullpath)

    def _ignored_max_matches(self, results):
        matches_exceeded = lambda: (
            results[0][1].matches >= results[0][1].max_matches)
        return self._default_rules_in_effect(results) and matches_exceeded()

    @staticmethod
    def _default_rules_in_effect(results):
        return (
            len(results) == 1 and
            results[0][1].result is True and
            results[0][1].size_lt == MAX_DEFAULT_SOURCECODE_FILE_SIZE + 1 and
            results[0][1].max_matches == MAX_DEFAULT_SOURCECODE_COUNT)

    def _warn_max_matches(self):
        if self._warned_max_matches:
            return
        log.warning(
            "Found more than %i source code files but will only "
            "copy %i as a safety measure.%s",
            MAX_DEFAULT_SOURCECODE_COUNT,
            MAX_DEFAULT_SOURCECODE_COUNT,
            self._config_help_suffix())
        self._warned_max_matches = True

    def _ignored_max_size(self, path, results):
        if not self._default_rules_in_effect(results):
            return False
        size = util.safe_filesize(path)
        return size is not None and size >= results[0][1].size_lt

    def _warn_max_size(self, path):
        log.warning(
            "Skipping potential source code file %s because it's "
            "too big.%s", path, self._config_help_suffix())

    def _config_help_suffix(self):
        if not self._config_help:
            return ""
        return " %s" % self._config_help

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
