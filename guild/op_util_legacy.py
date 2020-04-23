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
import hashlib
import logging
import re
import os
import struct
import sys
import threading
import time

# Move any import that's expensive or seldom used into function
from guild import file_util
from guild import flag_util
from guild import util

log = logging.getLogger("guild")

# Legacy support for functionality moved to _api
from guild import _api

NoCurrentRun = _api.NoCurrentRun
current_run = _api.current_run

NO_ARG_VALUE = object()

RESTART_NEEDED_STATUS = ("pending",)

MAX_DEFAULT_SOURCECODE_FILE_SIZE = 1024 * 1024
MAX_DEFAULT_SOURCECODE_COUNT = 100

RUN_OUTPUT_STREAM_BUFFER = 4096


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


class ProcessError(Exception):
    pass


class RunOutput(object):

    DEFAULT_WAIT_TIMEOUT = 10

    def __init__(self, run, proc=None, quiet=False, output_cb=None):
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
        if proc:
            self.open(proc)

    @property
    def closed(self):
        return not self._open

    def open(self, proc):
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
        if not self._quiet:
            stream_fileno = output_stream.fileno()
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
                        line = []
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


def resolve_file(filename):
    return util.find_apply([_abs_file, _cmd_file, _model_file, _cwd_file], filename)


def _abs_file(filename):
    if os.path.isabs(filename):
        return filename
    return None


def _cmd_file(filename):
    assert "CMD_DIR" in os.environ
    filename = os.path.join(os.environ["CMD_DIR"], filename)
    if os.path.exists(filename):
        return filename
    return None


def parse_flag_assigns(args):
    return dict([parse_flag_arg(os.path.expanduser(arg)) for arg in args])


def parse_flag_arg(arg):
    parts = arg.split("=", 1)
    if len(parts) == 1:
        raise ArgValueError(arg)
    else:
        return parts[0], flag_util.decode_flag_val(parts[1])


def exit(msg, exit_status=1):
    """Exit the Python runtime with a message.
    """
    sys.stderr.write(os.path.basename(sys.argv[0]))
    sys.stderr.write(": ")
    sys.stderr.write(msg)
    sys.stderr.write("\n")
    sys.exit(exit_status)


def parse_op_args(args):
    if len(args) < 2:
        exit("usage: %s COMMAND [ARG...]" % args[0])
    return args[1], args[2:]


def args_to_flags(args):
    """Returns `flags, other_args` for `args`.

    `other_args` is a list of args that cannot be converted to flag
    values.

    If args contains `--` then all args before the last occuring `--`
    are included in `other_args`.
    """
    flags = {}
    args, other_args = split_args_for_flags(args)
    name = None
    for arg in args:
        if arg[:2] == "--":
            name = arg[2:]
            flags[name] = True
        elif arg[:1] == "-":
            val = flag_util.decode_flag_val(arg)
            if isinstance(val, (int, float)):
                flags[name] = val
            elif len(arg) == 2:
                name = arg[1]
                flags[name] = True
            elif len(arg) > 2:
                name = None
                flags[arg[1]] = arg[2:]
        elif name is not None:
            flags[name] = flag_util.decode_flag_val(arg)
            name = None
        else:
            other_args.append(arg)
    return flags, other_args


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


def find_file(path):
    return util.find_apply([_cwd_file, _model_file], path)


def _cwd_file(path):
    if os.path.exists(path):
        return path
    return None


def _model_file(path):
    model_path = os.getenv("MODEL_PATH")
    if model_path:
        for root in model_path.split(os.path.pathsep):
            full_path = os.path.join(root, path)
            if os.path.exists(full_path):
                return full_path
    return None


def coerce_flag_value(val, flagdef):
    """Coerces a flag value based on flagdef settings."""
    if (
        val is None
        or not flagdef
        or not flagdef.type
        or flag_util.is_flag_function(val)
    ):
        return val
    if isinstance(val, list):
        return [coerce_flag_value(x, flagdef) for x in val]
    elif flagdef.type == "string":
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
            "unknown flag type '%s' for %s - cannot coerce", flagdef.type, flagdef.name
        )
        return val


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


def validate_flag_vals(vals, opdef):
    _check_missing_flags(vals, opdef)
    _check_flag_vals(vals, opdef)


def _check_missing_flags(vals, opdef):
    missing = _missing_flags(vals, opdef)
    if missing:
        raise MissingRequiredFlags(missing)


def _missing_flags(vals, opdef):
    return [
        flag
        for flag in opdef.flags
        if flag.required and _flag_missing(vals.get(flag.name))
    ]


def _flag_missing(val):
    if val is None or val == "":
        return True
    return False


def _check_flag_vals(vals, opdef):
    for flag in opdef.flags:
        val = vals.get(flag.name)
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


def copy_run_sourcecode(run, opdef):
    log.debug("copying source code files for run %s", run.id)
    copy_sourcecode(
        opdef, run.guild_path("sourcecode"), SourceCodeCopyHandler.handler_cls(opdef)
    )


class SourceCodeCopyHandler(file_util.FileCopyHandler):
    """Handler to log warnings when soure code files are skipped.

    Only logs warnings when the default rules are in effect.
    """

    @classmethod
    def handler_cls(cls, opdef):
        def f(src_root, dest_root, select):
            handler = cls(src_root, dest_root, select)
            handler.opdef = opdef
            return handler

        return f

    opdef = None
    _warned_max_matches = False

    def ignore(self, path, rule_results):
        fullpath = os.path.join(self.src_root, path)
        if self._ignored_max_matches(rule_results):
            self._warn_max_matches()
        if self._ignored_max_size(fullpath, rule_results):
            self._warn_max_size(fullpath)

    def _ignored_max_matches(self, results):
        matches_exceeded = lambda: (results[0][1].matches >= results[0][1].max_matches)
        return self._default_rules_in_effect(results) and matches_exceeded()

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
            self._opdef_help_suffix(),
        )
        self._warned_max_matches = True

    def _opdef_help_suffix(self):
        if self.opdef:
            return (
                " To control which source code files are copied, "
                "specify 'sourcecode' for the '%s' operation in "
                "guild.yml." % self.opdef.fullname
            )
        return ""

    def _ignored_max_size(self, path, results):
        if not self._default_rules_in_effect(results):
            return False
        size = util.safe_filesize(path)
        return size is not None and size >= results[0][1].size_lt

    def _warn_max_size(self, path):
        log.warning(
            "Skipping potential source code file %s because it's " "too big.%s",
            path,
            self._opdef_help_suffix(),
        )


def copy_sourcecode(opdef, dest, handler_cls=None):
    if os.getenv("NO_SOURCECODE") == "1":
        log.debug("NO_SOURCECODE=1, skipping sourcecode copy")
        return
    select = _sourcecode_select_for_opdef(opdef)
    root_start = opdef.guildfile.dir
    file_util.copytree(dest, select, root_start, handler_cls=handler_cls)


def _sourcecode_select_for_opdef(opdef):
    root = opdef_sourcecode_root(opdef)
    rules = _select_rules_for_opdef(opdef)
    return file_util.FileSelect(root, rules)


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


def split_main(main):
    if isinstance(main, list):
        return main
    return util.shlex_split(main or "")


# Alias
split_cmd = split_main


def wait_for_proc(p, stop_after_min, poll_interval=5, kill_delay=30):
    started = time.time()
    stop_at = time.time() + stop_after_min * 60
    while time.time() < stop_at:
        time.sleep(poll_interval)
        returncode = p.poll()
        if returncode is not None:
            return returncode
    elapsed = (time.time() - started) / 60
    log.info(
        "Stopping process early (pid %i) - %.1f minute(s) elapsed", p.pid, elapsed,
    )
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


def init_logging():
    import guild.log

    level = int(os.getenv("LOG_LEVEL", logging.WARN))
    format = os.getenv("LOG_FORMAT", "%(levelname)s: [%(name)s] %(message)s")
    guild.log.init_logging(level, {"_": format})
    globals()["log"] = logging.getLogger("guild")


def print_trials(trials):
    from guild import cli

    data, cols = _trials_table_data(trials)
    cli.table(data, cols)


def _trials_table_data(trials):
    names = set()
    data = []
    for i, flags in enumerate(trials):
        row = {"_trial": i + 1}
        data.append(row)
        if flags:
            row.update({name: flag_util.encode_flag_val(flags[name]) for name in flags})
            names.update(flags)
    heading = {name: name for name in names}
    heading["_trial"] = "#"
    return [heading] + data, ["_trial"] + sorted(names)


def save_trials(trials, path):
    data, cols = _trials_table_data(trials)
    cols.remove("_trial")  # Don't include trial number in CSV
    with open(path, "w") as f:
        out = csv.writer(f, lineterminator="\n")
        for row in data:
            out.writerow([row.get(name, "") for name in cols])


def op_flag_encoder(op):
    import importlib

    spec = op.opdef.flag_encoder
    if not spec:
        return None
    parts = spec.split(":")
    if len(parts) != 2:
        log.warning("invalid flag decoder %r - must be MODULE:FUNCTION", spec)
        return None
    mod_name, fun_name = parts
    try:
        mod = importlib.import_module(mod_name)
    except Exception as e:
        if log.getEffectiveLevel() <= logging.DEBUG:
            log.exception("importing %s", mod_name)
        else:
            log.warning("cannot load flag decoder %r: %s", spec, e)
        return None
    fun = getattr(mod, fun_name, None)
    if fun is None:
        log.warning(
            "cannot load flag decoder %r: no such attribute in %s", spec, mod_name
        )
        return None
    return fun


def ensure_exit_status(run, exit_status):
    """Ensures that a run is noted as having exited.

    Writes `exit_status` if the run doesn't already have an exit
    status. Also deletes PENDING status.
    """
    from guild import op as oplib

    run_exit_status = run.get("exit_status")
    if run_exit_status is None:
        run.write_attr("exit_status", exit_status)
    oplib.delete_pending(run)


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
    # behavior of the command on a restart/rerun).
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


def flags_hash(flags):
    flag_parts = [
        "%s:%s" % (name, flag_util.encode_flag_val(val))
        for name, val in sorted(flags.items())
    ]
    to_hash = "\n".join(flag_parts).encode()
    return hashlib.md5(to_hash).hexdigest()


def restart_needed(run, flags):
    return run.status in RESTART_NEEDED_STATUS or run.get("flags") != flags


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


def mapped_flag_vals(flag_vals, opdef):
    vals = {}
    flag_map = {}
    for name, val in sorted(flag_vals.items()):
        flagdef = opdef.get_flagdef(name)
        if flagdef:
            if flagdef.choices:
                _apply_choice_args(flagdef, val, flag_vals, vals)
            if not _skip_flag_arg(flagdef):
                _apply_flag_arg(flagdef, val, flag_vals, vals, flag_map)
        else:
            vals[name] = val
    return vals, flag_map


def _apply_choice_args(flagdef, val, flag_vals, target):
    for choice in flagdef.choices:
        if choice.value == val:
            if choice.flags:
                choice_flags = {
                    name: util.resolve_refs(val, flag_vals)
                    for name, val in choice.flags.items()
                }
                # Choice args must not overwrite existing args
                # (i.e. default values from other flags or values from
                # user)
                for name in choice_flags:
                    if name not in target:
                        target[name] = choice_flags[name]
            break


def _skip_flag_arg(flagdef):
    if flagdef.arg_skip is not None:
        return flagdef.arg_skip
    return flagdef.opdef.default_flag_arg_skip


def _apply_flag_arg(flagdef, value, flag_vals, target, flag_map):
    if flagdef.arg_name:
        arg_name = flagdef.arg_name
        flag_map[arg_name] = flagdef.name
    else:
        arg_name = flagdef.name
    arg_val = util.resolve_refs(value, flag_vals)
    if flagdef.arg_switch is not None:
        if arg_val == flagdef.arg_switch:
            target[arg_name] = NO_ARG_VALUE
    else:
        target[arg_name] = arg_val


def default_label(opdef, flag_vals):
    if opdef.label:
        return opdef.label
    flag_vals = _non_default_flag_vals(flag_vals, opdef)
    if not flag_vals:
        return None
    return flags_desc(flag_vals, truncate_floats=True, delim=" ")


def flags_desc(flags, truncate_floats=False, delim=", "):
    formatted = flag_util.format_flag_assigns(flags, truncate_floats)
    return delim.join(formatted)


def _non_default_flag_vals(flag_vals, opdef):
    return {
        name: val
        for name, val in flag_vals.items()
        if not _is_default_flag_val(val, name, opdef)
    }


def _is_default_flag_val(val, name, opdef):
    flagdef = opdef.get_flagdef(name)
    if not flagdef:
        return False
    return val == flagdef.default


def flag_assigns(flags, skip_none=False):
    return [
        flag_assign(name, val)
        for name, val in sorted(flags.items())
        if not skip_none or val is not None
    ]


def flag_assign(name, val):
    return "%s=%s" % (name, flag_util.format_flag(val))


def write_sourcecode_digest(run, opdef):
    if opdef.sourcecode.digest is False:
        log.info(
            "sourcecode digest disabled for operation '%s' - skipping", opdef.fullname
        )
        return
    if (
        opdef.sourcecode.digest is not True
        and opdef.modeldef.sourcecode.digest is False
    ):
        log.info(
            "sourcecode digest disabled for model '%s' - skipping", opdef.modeldef.name
        )
        return
    digest = file_util.files_digest(run.guild_path("sourcecode"))
    run.write_attr("sourcecode_digest", digest)
