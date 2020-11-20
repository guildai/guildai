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
import io
import logging
import os
import re
import struct
import sys
import threading
import time

import six
import yaml

from guild import _api
from guild import config
from guild import guildfile
from guild import file_util
from guild import flag_util
from guild import log as loglib
from guild import op_cmd as op_cmd_lib
from guild import op_dep
from guild import run as runlib
from guild import util
from guild import var
from guild import vcs_util

log = logging.getLogger("guild")

MAX_DEFAULT_SOURCECODE_FILE_SIZE = 1024 * 1024
MAX_DEFAULT_SOURCECODE_COUNT = 100

DEFAULT_EXEC = "${python_exe} -um guild.op_main ${main_args} -- ${flag_args}"
STEPS_EXEC = "${python_exe} -um guild.steps_main"

LABEL_TOKENS_P = re.compile(r"(\${.+?})")
LABEL_FLAG_REF_P = re.compile(r"\${(.+?)}")

RUN_OUTPUT_STREAM_BUFFER = 4096

RESTART_NEEDED_STATUS = ("pending",)

DEFAULT_PROC_POLL_INTERVAL = 5
DEFAULT_PROC_KILL_DELAY = 30

try:
    bytes('')
except TypeError:
    # Python 3
    LF = 10
    BYTES_JOIN = bytes
else:
    # Python 2
    LF = b"\n"
    BYTES_JOIN = lambda l: b"".join(l)


###################################################################
# Error classes
###################################################################


class ArgValueError(ValueError):
    def __init__(self, arg):
        super(ArgValueError, self).__init__(arg)
        self.arg = arg


class FlagError(Exception):
    pass


class MissingRequiredFlags(FlagError):
    def __init__(self, missing):
        super(MissingRequiredFlags, self).__init__(missing)
        self.missing = missing


class InvalidFlagChoice(FlagError):
    def __init__(self, val, flag):
        super(InvalidFlagChoice, self).__init__(val, flag)
        self.val = val
        self.flag = flag


class InvalidFlagValue(FlagError):
    def __init__(self, value, flag, msg):
        super(InvalidFlagValue, self).__init__(value, flag, msg)
        self.value = value
        self.flag = flag
        self.msg = msg


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


class ProcessError(Exception):
    pass


###################################################################
# Run output
###################################################################


class RunOutput(object):

    DEFAULT_WAIT_TIMEOUT = 10

    def __init__(self, run, quiet=False, output_cb=None):
        """Creates a run output object.

        Run output is not automatically opened. Use `open(proc)` to
        open output for a process.
        """
        assert run
        self._run = run
        self._quiet = quiet
        self._output_cb = output_cb
        self._output_lock = threading.Lock()
        self._open = False
        self._proc = None
        self._output = None
        self._index = None
        self._out_tee = None
        self._err_tee = None

    @property
    def closed(self):
        return not self._open

    def open(self, proc):
        """Opens output.

        When open, threads are started for reading from proc.stdout
        and proc.stderr and writing to sys.stdout and sys.stderr
        respectively.

        Generates an error if run output is closed.

        """
        self._assert_closed()
        if proc.stdout is None:
            raise RuntimeError("proc stdout must be a PIPE")
        if proc.stderr is None:
            raise RuntimeError("proc stderr must be a PIPE")
        self._proc = proc
        self._output = self._open_output()
        self._index = self._open_index()
        self._out_tee = threading.Thread(target=self._out_tee_run)
        self._err_tee = threading.Thread(target=self._err_tee_run)
        self._out_tee.start()
        self._err_tee.start()
        self._open = True

    def _assert_closed(self):
        if self._open:
            raise RuntimeError("already open")
        assert self._proc is None
        assert self._output is None
        assert self._index is None
        assert self._out_tee is None
        assert self._err_tee is None

    def _open_output(self):
        path = self._run.guild_path("output")
        return open(path, "wb")

    def _open_index(self):
        path = self._run.guild_path("output.index")
        return open(path, "wb")

    def _out_tee_run(self):
        assert self._proc
        self._gen_tee_run(self._proc.stdout, sys.stdout, 0)

    def _err_tee_run(self):
        assert self._proc
        self._gen_tee_run(self._proc.stderr, sys.stderr, 1)

    def _gen_tee_run(self, input_stream, output_stream, stream_type):
        assert self._output
        assert self._index
        os_read = os.read
        os_write = os.write
        input_fileno = input_stream.fileno()
        if not self._quiet and hasattr(output_stream, "fileno"):
            try:
                stream_fileno = output_stream.fileno()
            except io.UnsupportedOperation:
                stream_fileno = None
        else:
            stream_fileno = None
        output_fileno = self._output.fileno()
        index_fileno = self._index.fileno()
        time_ = time.time
        lock = self._output_lock
        line = []
        while True:
            buf = os_read(input_fileno, RUN_OUTPUT_STREAM_BUFFER)
            if not buf:
                break
            with lock:
                if stream_fileno is not None:
                    os_write(stream_fileno, buf)
                os_write(output_fileno, buf)
                for b in buf:
                    if b < 9:  # non-printable
                        continue
                    line.append(b)
                    if b == LF:
                        line_bytes = BYTES_JOIN(line)
                        del line[:]
                        entry = struct.pack("!QB", int(time_() * 1000), stream_type)
                        os_write(index_fileno, entry)
                        if self._output_cb:
                            try:
                                self._output_cb.write(line_bytes)
                            except Exception:
                                log.exception(
                                    "error in output callback (will be " "removed)"
                                )
                                self._output_cb = None

    def wait(self, timeout=DEFAULT_WAIT_TIMEOUT):
        self._assert_open()
        self._out_tee.join(timeout)
        self._err_tee.join(timeout)

    def _assert_open(self):
        if not self._open:
            raise RuntimeError("not open")
        assert self._proc
        assert self._output
        assert self._index
        assert self._out_tee
        assert self._err_tee

    def close(self):
        lock = self._acquire_output_lock()
        try:
            self._close()
        finally:
            lock.release()

    def _acquire_output_lock(self, timeout=60):
        """Polling verison of acquire to support timeouts on Python 2."""
        timeout_at = time.time() + timeout
        while time.time() < timeout_at:
            if self._output_lock.acquire(False):
                return self._output_lock
            time.sleep(1)
        raise RuntimeError("timeout")

    def _close(self):
        self._assert_open()
        self._output.close()
        self._index.close()
        if self._output_cb:
            try:
                self._output_cb.close()
            except Exception:
                log.exception("closing output callback")
        assert not self._out_tee.is_alive()
        assert not self._err_tee.is_alive()
        self._proc = None
        self._output = None
        self._index = None
        self._out_tee = None
        self._err_tee = None
        self._open = False

    def wait_and_close(self, timeout=DEFAULT_WAIT_TIMEOUT):
        self.wait(timeout)
        self.close()


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
    from guild import model_proxy

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
    model_ref, op_name = _parsed_opspec(opspec)
    model = _resolve_model(model_ref)
    if not model:
        raise NoSuchModel(opspec)
    return model, op_name


def _parsed_opspec(opspec):
    parsed = parse_opspec(opspec)
    if parsed is None:
        raise InvalidOpSpec(opspec)
    return parsed


###################################################################
# Opdef for model paths
###################################################################


def opdef_model_paths(opdef):
    return _opdef_paths(opdef) + _model_parent_paths(opdef.modeldef)


def _opdef_paths(opdef):
    if not opdef.guildfile.dir:
        return []
    abs_gf_dir = os.path.abspath(opdef.guildfile.dir)
    if opdef.python_path is not None:
        return [os.path.join(abs_gf_dir, p) for p in opdef.python_path]
    if opdef.sourcecode and opdef.sourcecode.root:
        return [os.path.join(abs_gf_dir, opdef.sourcecode.root)]
    return [abs_gf_dir]


def _model_parent_paths(modeldef):
    return [os.path.abspath(parent.dir) for parent in modeldef.parents]


###################################################################
# Parse opspec
###################################################################


def parse_opspec(spec):
    return util.find_apply(
        [
            _empty_spec,
            _op_spec,
            _model_op_spec,
            _package_model_op_spec,
            _package_op_spec,
        ],
        spec,
    )


def _empty_spec(spec):
    if spec:
        return None
    return None, None


def _op_spec(spec):
    if "/" in spec or ":" in spec:
        return None
    return None, spec


def _model_op_spec(spec):
    m = re.match(r"([^/:]*):([^/:]+)$", spec)
    if not m:
        return None
    return m.groups()


def _package_model_op_spec(spec):
    m = re.match(r"([^/:]+/[^/:?]+):([^/:]+)$", spec)
    if not m:
        return None
    return m.groups()


def _package_op_spec(spec):
    m = re.match(r"([^/:]+/):?([^/:]+)$", spec)
    if not m:
        return None
    return m.groups()


def _resolve_model(model_ref):
    return util.find_apply(
        [
            _resolve_cwd_model,
            _resolve_system_model,
        ],
        model_ref,
    )


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


def write_sourcecode_digest(run, sourcecode_root):
    src = os.path.join(run.dir, sourcecode_root)
    digest = file_util.files_digest(src)
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


###################################################################
# Run labels
###################################################################


def run_label(label_template, flag_vals):
    """Returns a run label for template and flag vals."""
    default_label = _default_run_label(flag_vals)
    if label_template is None:
        return default_label
    return _render_label_template(label_template, flag_vals, default_label)


def _default_run_label(flag_vals):
    """Returns a default run label for a map of flag values.

    The default label is a string containing flag assign as NAME=VALUE.
    """
    non_null = {name: val for name, val in flag_vals.items() if val is not None}
    return " ".join(
        flag_util.flag_assigns(non_null, truncate_floats=True, shorten_paths=True)
    )


def _render_label_template(label_template, flag_vals, default_label):
    """Returns a rendered label template.

    `label_template` is a string containing flag references. Flag
    references are resolved with values defined in `flag_values.`

    `default_label` is provided as an additional supported value,
    which may be referenced using the name 'default_label' in the
    template.
    """
    formatted_vals = _render_template_formatted_vals(flag_vals, default_label)
    return _render_label_template_formatted(label_template, formatted_vals)


def _render_template_formatted_vals(flag_vals, default_label):
    formatted_vals = {
        "default_label": default_label,
    }
    formatted_vals.update(
        {
            name: FormattedValue(val)
            for name, val in flag_vals.items()
            if val is not None
        }
    )
    return formatted_vals


class FormattedValue(object):
    def __init__(self, value):
        self._value = value
        self._str = None

    @property
    def wrapped_value(self):
        return self._value

    @wrapped_value.setter
    def wrapped_value(self, value):
        self._value = value
        self._str = None

    def __str__(self):
        if self._str is None:
            self._str = flag_util.format_flag(
                self._value, truncate_floats=True, shorten_paths=True
            )
        return self._str


def _render_label_template_formatted(label_template, formatted_vals):
    """Renders a label template with formatted values.

    `formatted_vals` is a map of names to formatted values. A
    formatted value is a value wrapped as a `FormattedValue` instance.

    This function supports value filters in form
    ``${NAME|FILTER:ARG1,ARG2}``, which require values to be be
    wrapped with `FormattedValue`.
    """
    tokens = LABEL_TOKENS_P.split(label_template)
    return "".join([_rendered_str(_render_token(t, formatted_vals)) for t in tokens])


def _render_token(token, vals):
    m = LABEL_FLAG_REF_P.match(token)
    if not m:
        return token
    ref_parts = m.group(1).split("|")
    name = ref_parts[0]
    transforms = ref_parts[1:]
    val = vals.get(name)
    for t in transforms:
        val = _apply_template_transform(t, val)
    return val


def _apply_template_transform(t, val):
    if hasattr(val, "wrapped_value"):
        val = val.wrapped_value
    parts = t.split(":", 1)
    if len(parts) == 1:
        name, arg = parts[0], None
    else:
        name, arg = parts
    if name[:1] == "%":
        return _t_python_format(val, name)
    elif name == "default":
        return _t_default(val, arg)
    elif name == "basename":
        if arg:
            log.warning("ignoring argment to baseline in %r", t)
        return _t_basename(val)
    elif name == "unquote":
        return _t_unquote(val)
    else:
        log.warning("unsupported template transform: %r", t)
        return "#error#"


def _t_python_format(val, fmt):
    try:
        return fmt % val
    except ValueError as e:
        log.warning("error formatting %r with %r: %s", val, fmt, e)
        return val
    except TypeError:
        # Silently ignore type errors. ValueErrors (logged above)
        # indicate an invalid formatting string, which is of
        # interest. Running into an unexpected value type should let
        # that value pass through.
        return val


def _t_default(val, arg):
    if val is None:
        return arg or ""
    return val


def _t_basename(val):
    if not val:
        return ""
    return os.path.basename(util.strip_trailing_sep(val))


def _t_unquote(val):
    if (
        isinstance(val, six.string_types)
        and len(val) >= 2
        and val[0] == "'"
        and val[-1] == "'"
    ):
        return val[1:-1]
    return val


def _rendered_str(s):
    if s is None:
        return ""
    return str(s)


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
    cmd_args, run_attrs = _op_cmd_args_and_run_attrs(opdef)
    cmd_env = _op_cmd_env(opdef, extra_cmd_env or {})
    cmd_flags = _op_cmd_flags(opdef)
    cmd_flags_dest = opdef.flags_dest or "args"
    op_cmd = op_cmd_lib.OpCmd(cmd_args, cmd_env, cmd_flags, cmd_flags_dest)
    return op_cmd, run_attrs


def _op_cmd_args_and_run_attrs(opdef):
    main_args = split_cmd(opdef.main or "")
    exec_str, run_attrs = _opdef_exec_and_run_attrs(opdef)
    exec_args = split_cmd(exec_str)
    _apply_main_args(main_args, exec_args)
    _apply_flag_args_marker(exec_args)
    return exec_args, run_attrs


def split_cmd(cmd):
    if isinstance(cmd, list):
        return cmd
    return util.shlex_split(cmd or "")


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
    env["GUILD_PLUGINS"] = _op_plugins(opdef)
    env["PROJECT_DIR"] = opdef.guildfile.dir or ""
    if opdef.flags_dest:
        env["FLAGS_DEST"] = opdef.flags_dest
    if opdef.handle_keyboard_interrupt:
        env["HANDLE_KEYBOARD_INTERRUPT"] = "1"
    return env


def _op_plugins(opdef):
    from guild import plugin as pluginlib  # expensive

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
        arg_split=flagdef.arg_split,
        env_name=flagdef.env_name,
    )


def _flagdef_arg_skip(flagdef):
    if flagdef.arg_skip is not None:
        return flagdef.arg_skip
    return flagdef.opdef.default_flag_arg_skip


###################################################################
# Flag vals for opdef
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
    _apply_choice_vals(opdef.flags, user_flag_vals, flag_vals)
    return flag_vals, resource_flagdefs


def _apply_coerce_flag_vals(flagdefs, force, vals):
    flagdef_lookup = {flagdef.name: flagdef for flagdef in flagdefs}
    for name, val in vals.items():
        try:
            coerced = _coerced_flag_value(name, val, flagdef_lookup)
        except InvalidFlagValue:
            if not force:
                raise
        else:
            vals[name] = coerced


def _coerced_flag_value(name, val, flagdefs):
    flagdef = flagdefs.get(name)
    if not flagdef:
        return val
    try:
        return coerce_flag_value(val, flagdef)
    except (ValueError, TypeError) as e:
        raise InvalidFlagValue(val, flagdef, str(e))


def coerce_flag_value(val, flagdef):
    """Coerces a flag value based on flagdef settings."""
    if (
        val is None
        or not flagdef
        or not flagdef.type
        or flagdef.type == "auto"
        or flag_util.is_flag_function(val)
    ):
        return val
    if isinstance(val, list):
        return [coerce_flag_value(x, flagdef) for x in val]
    elif flagdef.arg_split:
        return _coerce_flag_val_split_parts(val, flagdef)
    else:
        return _coerce_typed_flag_value(val, flagdef)


def _coerce_typed_flag_value(val, flagdef):
    assert flagdef.type is not None
    if flagdef.type == "string":
        return _try_coerce_flag_val(val, str, flagdef)
    elif flagdef.type == "int":
        if isinstance(val, float):
            raise ValueError("invalid value for type 'int'")
        return _try_coerce_flag_val(val, int, flagdef)
    elif flagdef.type == "float":
        return _try_coerce_flag_val(val, float, flagdef)
    elif flagdef.type == "boolean":
        return _try_coerce_flag_val(val, bool, flagdef)
    elif flagdef.type == "number":
        if isinstance(val, (float, int)):
            return val
        return _try_coerce_flag_val(val, (int, float), flagdef)
    elif flagdef.type in ("path", "existing-path"):
        return _resolve_rel_path(val)
    else:
        log.warning(
            "unknown flag type '%s' for %s - cannot coerce",
            flagdef.type,
            flagdef.name,
        )
        return val


def _coerce_flag_val_split_parts(val, flagdef):
    assert flagdef.type is not None
    encoded = _ensure_encoded_flag_val(val)
    parts = flag_util.split_encoded_flag_val(encoded, flagdef.arg_split)
    coerced = [_coerce_typed_flag_value(part, flagdef) for part in parts]
    return flag_util.join_splittable_flag_vals(coerced, flagdef.arg_split)


def _ensure_encoded_flag_val(val):
    if isinstance(val, six.string_types):
        return val
    return flag_util.encode_flag_val(val)


def _try_coerce_flag_val(val, funs, flagdef):
    if not isinstance(funs, tuple):
        funs = (funs,)
    for f in funs:
        try:
            return f(val)
        except ValueError as e:
            log.debug("value error applying %s to %r: %s", f, val, e)
    raise ValueError("invalid value for type '%s'" % flagdef.type)


def _resolve_rel_path(val):
    val = os.path.expanduser(val)
    if val and not os.path.isabs(val):
        return os.path.abspath(val)
    return val


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


def _check_flag_val(val, flagdef):
    if isinstance(val, list):
        for x in val:
            _check_flag_val(x, flagdef)
    elif flagdef.arg_split and val is not None:
        _check_splittable_flag_val(val, flagdef)
    else:
        _check_flag_val_(val, flagdef)


def _check_splittable_flag_val(val, flagdef):
    assert flagdef.arg_split is not None
    encoded = _ensure_encoded_flag_val(val)
    split_val = [
        flag_util.decode_flag_val(part)
        for part in flag_util.split_encoded_flag_val(encoded, flagdef.arg_split)
    ]
    for x in split_val:
        _check_flag_val_(x, flagdef)


def _check_flag_val_(val, flagdef):
    if flag_util.is_flag_function(val):
        return
    _check_flag_choice(val, flagdef)
    _check_flag_type(val, flagdef)
    _check_flag_range(val, flagdef)


def _check_flag_choice(val, flag):
    if not val or flag.allow_other or not flag.choices:
        return
    for choice in flag.choices:
        if choice.alias and val == choice.alias:
            return
        if choice.value == val:
            return
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


def _apply_choice_vals(flagdefs, user_vals, target_vals):
    for flagdef in flagdefs:
        if not flagdef.choices:
            continue
        flag_val = target_vals.get(flagdef.name)
        if flag_val is None:
            continue
        for choice in flagdef.choices:
            if (choice.alias or choice.value) != flag_val:
                continue
            if choice.alias:
                target_vals[flagdef.name] = choice.value
            if choice.flags:
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
    """Applies default values to flag_vals.

    Skips flag values that are already defined in flag_vals.

    """
    for flagdef in flagdefs:
        if flagdef.name not in flag_vals:
            flag_vals[flagdef.name] = flagdef.default


def flag_assigns(flags, skip_none=False):
    return [
        flag_assign(name, val)
        for name, val in sorted(flags.items())
        if not skip_none or val is not None
    ]


def flag_assign(name, val):
    return "%s=%s" % (name, flag_util.format_flag(val))


def parse_flag_assigns(args, opdef=None):
    flag_types = _flag_types_for_opdef(opdef) if opdef else None
    expanded_args = [os.path.expanduser(arg) for arg in args]
    parsed_flags = [parse_flag_arg(arg, flag_types) for arg in expanded_args]
    return dict(parsed_flags)


def _flag_types_for_opdef(opdef):
    return {flagdef.name: flagdef.type for flagdef in opdef.flags}


def parse_flag_arg(arg, flag_types=None):
    parts = arg.split("=", 1)
    if len(parts) == 1:
        raise ArgValueError(arg)
    name, val = parts
    flag_type = flag_types.get(name) if flag_types else None
    return name, flag_util.decode_flag_val(val, flag_type)


def args_to_flags(args):
    """Returns `flags, other_args` for `args`.

    `other_args` is a list of args that cannot be converted to flag
    values.

    If args contains `--` then all args before the last occuring `--`
    are included in `other_args`.

    Uses `util.decode_yaml()` to decode flag arg values.
    """
    flags = {}
    flag_args, other_args = split_args_for_flags(args)
    name = None
    for arg in flag_args:
        if arg[:2] == "--":
            _maybe_switch(flags, name)
            name = arg[2:]
        elif arg[:1] == "-":
            maybe_num = util.decode_yaml(arg)
            if isinstance(maybe_num, (int, float)):
                _set_or_append_flag(flags, name, maybe_num)
            elif len(arg) == 2:
                _maybe_switch(flags, name)
                name = arg[1]
            elif len(arg) > 2:
                _maybe_switch(flags, name)
                name = arg[1]
                _set_or_append_flag(flags, name, arg[2:])
        elif name is not None:
            _set_or_append_flag(flags, name, util.decode_yaml(arg))
        else:
            other_args.append(arg)
    _maybe_switch(flags, name)
    return flags, other_args


def _maybe_switch(flags, name):
    if name is not None and name not in flags:
        flags[name] = True


def _set_or_append_flag(flags, name, val):
    try:
        existing = flags[name]
    except KeyError:
        flags[name] = val
    else:
        if isinstance(existing, list):
            existing.append(val)
        else:
            flags[name] = [existing, val]


def split_args_for_flags(args):
    """Returns `split_args, other_args` for `args`.

    Split occurs using the last occurrence of `--` in `args`.

    If `arg` does not contain `--` returns `args, []`.
    """
    for i in range(len(args) - 1, -1, -1):
        if args[i] == "--":
            return args[i + 1 :], args[:i]
    return args, []


def global_dest(global_name, flags):
    dest = cur = {}
    for name in global_name.split("."):
        cur = cur.setdefault(name, {})
    cur.update(flags)
    return dest


def flags_desc(flags, truncate_floats=False, delim=", "):
    formatted = flag_util.flag_assigns(flags, truncate_floats)
    return delim.join(formatted)


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
    elif ext in ("", ".csv"):
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
# Restart support
###################################################################


def restart_needed(run, flags):
    return run.status in RESTART_NEEDED_STATUS or run.get("flags") != flags


def run_params_for_restart(run, user_specified_params=None):
    """Returns params for use in run command for a restart of run.

    The set of applicable params in the run "run_params" attribute are
    considered. If user_specified_params contains a non-default value
    (i.e. the user has indicated she wants to use a specific value)
    that param will not be included in the result. If
    user_specified_params is None (default) then all applicable params
    for a restart that are defined in run are returned.
    """
    # Note about applicable run params:
    #
    # A limited number of params could possibly apply to args - those
    # are listed here. This list has to be maintained as new args are
    # added to the run command. Params must be included where the user
    # would reasonably assume applicability and never in cases where
    # the use of the parameter would be clearly surprising to the user
    # (e.g. reusing the 'yes' param, which would alter the expected
    # behavior of the command on a restart).
    #
    # Params that are saved as run attrs or otherwise available under
    # the run guild path (e.g. opspec, label, flags) should NOT be
    # returned in this value in the interest of elimiting redundancy
    # and potential mismtach bugs. Anyone needing those values MUST
    # read them via run attrs or applicable run interface
    # (e.g. opref in the case of opsec).
    #
    applicable_run_params = [
        "force_flags",
        "gpus",
        "max_trials",
        "maximize",
        "minimize",
        "no_gpus",
        "opt_flags",
        "optimizer",
        "random_seed",
    ]
    from guild.commands.run import run as run_cmd

    run_params = run.get("run_params", {})
    if not isinstance(run_params, dict):
        return
    baseline_params = run_cmd.make_context("", []).params
    result = {}
    for name in run_params:
        val = _coerce_run_param(name, run_params[name])
        if name not in applicable_run_params:
            continue
        if user_specified_params is None:
            result[name] = val
            continue
        try:
            user_specified_val = user_specified_params[name]
        except KeyError:
            result[name] = val
            continue
        if user_specified_val != baseline_params[name]:
            continue
        result[name] = val
    return result


def _coerce_run_param(name, val):
    """Ensures that named param is valid for the run command."""
    if name == "flags":
        return tuple(val)
    return val


###################################################################
# Wait for proc
###################################################################


def wait_for_proc(p, stop_after_min, poll_interval=None, kill_delay=None):
    poll_interval = poll_interval or DEFAULT_PROC_POLL_INTERVAL
    kill_delay = kill_delay or DEFAULT_PROC_KILL_DELAY
    started = time.time()
    stop_at = time.time() + stop_after_min * 60
    while time.time() < stop_at:
        returncode = p.poll()
        if returncode is not None:
            return returncode
        time.sleep(poll_interval)
    elapsed = (time.time() - started) / 60
    log.info("Stopping process early (pid %i) - %.1f minute(s) elapsed", p.pid, elapsed)
    return _terminate(p, poll_interval, kill_delay)


def _terminate(p, poll_interval, kill_delay):
    kill_at = time.time() + kill_delay
    p.terminate()
    while p.poll() is None and time.time() < kill_at:
        time.sleep(poll_interval)
    if p.poll() is None:
        log.warning("Process did not terminate (pid %i), killing", p.pid)
        p.kill()
        time.sleep(poll_interval)
    returncode = p.poll()
    if returncode not in (0, -15):
        raise ProcessError("Process did not terminate gracefully (pid %i)" % p.pid)
    return returncode


###################################################################
# Other utils
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


def write_proc_lock(pid, run):
    with open(run.guild_path("LOCK"), "w") as f:
        f.write(str(pid))


def delete_proc_lock(run):
    try:
        os.remove(run.guild_path("LOCK"))
    except OSError:
        pass


def init_logging():
    if os.getenv("LOG_INIT_SKIP") == "1":
        return
    level = int(os.getenv("LOG_LEVEL", logging.WARN))
    format = os.getenv("LOG_FORMAT", "%(levelname)s: [%(name)s] %(message)s")
    loglib.init_logging(level, {"_": format})


def current_run():
    return _api.current_run()
