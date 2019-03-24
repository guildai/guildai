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

import fnmatch
import csv
import hashlib
import logging
import re
import os
import shlex
import shutil
import struct
import sys
import threading
import time

import six
from six.moves import shlex_quote

import yaml

# Move any import that's expensive or seldom used into function
from guild import util

log = logging.getLogger("guild")

# Legacy support for functionality moved to _api
from guild import _api
NoCurrentRun = _api.NoCurrentRun
current_run = _api.current_run

function_pattern = re.compile(r"([a-zA-Z0-9_\-\.]*)\[(.*)\]\s*$")
function_arg_delimiter = ":"

RESTART_NEEDED_STATUS = ("pending",)

class ArgValueError(ValueError):

    def __init__(self, arg):
        super(ArgValueError, self).__init__(arg)
        self.arg = arg

class MissingRequiredFlags(ValueError):

    def __init__(self, missing):
        super(MissingRequiredFlags, self).__init__(missing)
        self.missing = missing

class InvalidFlagChoice(ValueError):

    def __init__(self, val, flag):
        super(InvalidFlagChoice, self).__init__(val, flag)
        self.val = val
        self.flag = flag

class InvalidFlagValue(ValueError):

    def __init__(self, val, flag, msg):
        super(InvalidFlagValue, self).__init__(val, flag, msg)
        self.val = val
        self.flag = flag
        self.msg = msg

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
            b = os_read(input_fileno, 1)
            if not b:
                break
            with lock:
                if stream_fileno is not None:
                    os_write(stream_fileno, b)
                if b < b"\x09": # non-printable
                    continue
                line.append(b)
                if b == b"\n":
                    line_bytes = b"".join(line)
                    os_write(output_fileno, line_bytes)
                    line = []
                    entry = struct.pack(
                        "!QB", int(time_() * 1000), stream_type)
                    os_write(index_fileno, entry)
                    if self._output_cb:
                        try:
                            self._output_cb.write(line_bytes)
                        except Exception:
                            log.exception(
                                "error in output callback (will be removed)")
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
    return util.find_apply([
        _abs_file,
        _cmd_file,
        _model_file,
        _cwd_file
    ], filename)

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

def parse_flags(args):
    return dict([parse_flag_arg(os.path.expanduser(arg)) for arg in args])

def parse_flag_arg(arg):
    parts = arg.split("=", 1)
    if len(parts) == 1:
        raise ArgValueError(arg)
    else:
        return parts[0], parse_arg_val(parts[1])

def parse_arg_val(s):
    if s == "":
        return s
    parsers = [
        (int, ValueError),
        (float, ValueError),
        (_yaml_parse, (ValueError, yaml.YAMLError)),
    ]
    for p, e_type in parsers:
        try:
            return p(s)
        except e_type:
            pass
    return s

def _yaml_parse(s):
    """Uses yaml module to parse s to a Python value.

    First tries to parse as an unnamed flag function with at least two
    args and, if successful, returns s unmodified. This prevents yaml
    from attempting to parse strings like '1:1' which it considers to
    be timestamps.
    """
    try:
        name, args = parse_function(s)
    except ValueError:
        pass
    else:
        if name is None and len(args) >= 2:
            return s
    return yaml.safe_load(s)

def format_flag_val(val):
    if val is True:
        return "yes"
    elif val is False:
        return "no"
    elif val is None:
        return "null"
    elif isinstance(val, list):
        return _format_flag_list(val)
    elif isinstance(val, (six.string_types, float)):
        return _yaml_format(val)
    else:
        return str(val)

def _format_flag_list(val_list):
    joined = ", ".join([format_flag_val(val) for val in val_list])
    return "[%s]" % joined

def _yaml_format(val):
    formatted = yaml.safe_dump(val).strip()
    if formatted.endswith("\n..."):
        formatted = formatted[:-4]
    return formatted

def format_flag_arg(name, val):
    return "%s=%s" % (name, format_flag_val(val))

class TFEvents(object):

    def __init__(self, logdir):
        self.logdir = logdir
        self._writer = None

    def add_scalars(self, scalars, global_step=None):
        self._ensure_writer()
        self._writer.add_summary(self._scalars_summary(scalars), global_step)

    @staticmethod
    def _scalars_summary(scalars):
        import tensorflow as tf
        value = [
            tf.summary.Summary.Value(tag=tag, simple_value=val)
            for tag, val in scalars
        ]
        return tf.summary.Summary(value=value)

    def _ensure_writer(self):
        import tensorflow as tf
        if not self._writer:
            self._writer = tf.summary.FileWriter(self.logdir, max_queue=0)

    def flush(self):
        if self._writer:
            self._writer.flush()

    def close(self):
        if self._writer:
            self._writer.close()
            self._writer = None

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.close()

def tfevents(subdir=None, run=None):
    if not run:
        run = current_run()
    if subdir:
        logdir = os.path.join(run.path, subdir)
    else:
        logdir = run.path
    return TFEvents(logdir)

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
    flags, _args = args_to_flags2(args)
    return flags

def args_to_flags2(args):
    flags = {}
    extra = []
    name = None
    for arg in args:
        if arg[:2] == "--":
            name = arg[2:]
            flags[name] = True
        elif arg[:1] == "-":
            val = parse_arg_val(arg)
            if isinstance(val, (int, float)):
                flags[name] = val
            elif len(arg) == 2:
                name = arg[1]
                flags[name] = True
            elif len(arg) > 2:
                name = None
                flags[arg[1]] = arg[2:]
        elif name is not None:
            flags[name] = parse_arg_val(arg)
            name = None
        else:
            extra.append(arg)
    return flags, extra

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
    if val is None or not flagdef or not flagdef.type:
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
    elif flagdef.type == "number":
        if isinstance(val, (float, int)):
            return val
        return _try_coerce_flag_val(val, (int, float), flagdef)
    elif flagdef.type in ("path", "existing-path"):
        return _resolve_rel_path(val)
    else:
        log.warning(
            "unknown flag type '%s' for %s - cannot coerce",
            flagdef.type, flagdef.name)
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
        flag for flag in opdef.flags
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
    if (val and flag.choices and not flag.allow_other and
        val not in [choice.value for choice in flag.choices]):
        raise InvalidFlagChoice(val, flag)

def _check_flag_type(val, flag):
    if flag.type == "existing-path":
        if val and not os.path.exists(val):
            raise InvalidFlagValue(val, flag, "%s does not exist" % val)

def _check_flag_range(val, flag):
    if val is None:
        return
    if flag.min is not None and val < flag.min:
        raise InvalidFlagValue(
            val, flag, "out of range (less than min %s)" % flag.min)
    if flag.max is not None and val > flag.max:
        raise InvalidFlagValue(
            val, flag, "out of range (greater than max %s)" % flag.max)

def copy_source(run, opdef):
    _copy_source(
        opdef.guildfile.dir,
        opdef.modeldef.source,
        run.guild_path("source"))

def _copy_source(src_base, source_config, dest_base):
    to_copy = _source_to_copy(src_base, source_config)
    if not to_copy:
        log.debug("no source to copy")
        return
    for src, src_rel_path in to_copy:
        dest = os.path.join(dest_base, src_rel_path)
        log.debug("copying source %s to %s", src, dest)
        util.ensure_dir(os.path.dirname(dest))
        _try_copy_file(src, dest)

def _source_to_copy(src_dir, source_config):
    to_copy = []
    seen_dirs = set()
    for root, dirs, files in os.walk(src_dir, followlinks=True):
        seen_dirs.add(os.path.realpath(root))
        _del_excluded_dirs(dirs, root, seen_dirs)
        for name in files:
            path = os.path.join(root, name)
            rel_path = os.path.relpath(path, src_dir)
            if _to_copy(path, rel_path, source_config):
                to_copy.append((path, rel_path))
    return to_copy

def _try_copy_file(src, dest):
    try:
        shutil.copyfile(src, dest)
    except (IOError, OSError) as e:
        # This is not an error we want to stop an operation for. Log
        # and continue.
        if log.getEffectiveLevel() <= logging.DEBUG:
            log.exception("copy %s to %s", src, dest)
        else:
            log.warning("could not copy source file %s: %s", src, e)

def _del_excluded_dirs(dirs, root, seen_dirs):
    _del_env_dirs(dirs, root)
    _del_git_dir(dirs)
    _del_seen_dirs(dirs, root, seen_dirs)

def _del_env_dirs(dirs, root):
    for name in dirs:
        if _is_env_dir(os.path.join(root, name)):
            dirs.remove(name)

def _del_git_dir(dirs):
    try:
        dirs.remove(".git")
    except ValueError:
        pass

def _del_seen_dirs(dirs, root, seen):
    for dir_name in dirs:
        real_path = os.path.realpath(os.path.join(root, dir_name))
        if real_path in seen:
            dirs.remove(dir_name)

def _is_env_dir(path):
    return os.path.exists(os.path.join(path, "bin", "activate"))

def _to_copy(path, rel_path, source_config):
    last_match = None
    for spec in source_config.specs:
        if _source_match(rel_path, spec):
            last_match = spec
    if last_match:
        return _to_copy_for_spec(last_match)
    return _is_text_file(path)

def _source_match(rel_path, spec):
    return any((fnmatch.fnmatch(rel_path, p) for p in spec.patterns))

def _to_copy_for_spec(spec):
    return spec.type == "include"

def _is_text_file(path):
    from guild import binaryornot
    return not binaryornot.is_binary(path)

def split_main(main):
    if isinstance(main, list):
        return main
    # If main is None, this call will block (see
    # https://bugs.python.org/issue27775)
    return shlex.split(main or "")

# Alias
split_cmd = split_main

def wait_for_proc(p, stop_after_min, poll_interval=5, kill_delay=30):
    stop_at = time.time() + stop_after_min * 60
    while time.time() < stop_at:
        time.sleep(poll_interval)
        returncode = p.poll()
        if returncode is not None:
            return returncode
    log.info(
        "Stopping process early (pid %i) - %i minute(s) elapsed",
        p.pid, stop_after_min)
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
        raise ProcessError(
            "Process did not terminate gracefully (pid %i)"
            % p.pid)
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
            row.update(
                {name: format_flag_val(flags[name])
                 for name in flags})
            names.update(flags)
    heading = {name: name for name in names}
    heading["_trial"] = "#"
    return [heading] + data, ["_trial"] + sorted(names)

def save_trials(trials, path):
    data, cols = _trials_table_data(trials)
    cols.remove("_trial") # Don't include trial number in CSV
    with open(path, "w") as f:
        out = csv.writer(f)
        for row in data:
            out.writerow([row.get(name, "") for name in cols])

def op_flag_encoder(op):
    import importlib
    spec = op.opdef.flag_encoder
    if not spec:
        return None
    parts = spec.split(":")
    if len(parts) != 2:
        log.warning(
            "invalid flag decoder %r - must be MODULE:FUNCTION",
            spec)
        return None
    mod_name, fun_name = parts
    try:
        mod = importlib.import_module(mod_name)
    except Exception as e:
        if log.getEffectiveLevel() <= logging.DEBUG:
            log.exception("importing %s", mod_name)
        else:
            log.warning(
                "cannot load flag decoder %r: %s",
                spec, e)
        return None
    fun = getattr(mod, fun_name, None)
    if fun is None:
        log.warning(
            "cannot load flag decoder %r: no such attribute in %s",
            spec, mod_name)
        return None
    return fun

def ensure_exit_status(run, exit_status):
    from guild import op as oplib
    run_exit_status = run.get("exit_status")
    if run_exit_status is None:
        run.write_attr("exit_status", exit_status)
    oplib.delete_pending(run)

def format_op_desc(run, nowarn=False, seen_protos=None):
    seen_protos = seen_protos or set()
    opref = run.opref
    base_desc = _base_op_desc(opref, nowarn)
    return _apply_batch_desc(base_desc, run, seen_protos)

def _base_op_desc(opref, nowarn):
    if opref.pkg_type == "guildfile":
        return _format_guildfile_op(opref)
    elif opref.pkg_type == "package":
        return _format_package_op(opref)
    elif opref.pkg_type == "script":
        return _format_script_op(opref)
    elif opref.pkg_type == "builtin":
        return _format_builtin_op(opref)
    elif opref.pkg_type == "pending":
        return _format_pending_op(opref)
    elif opref.pkg_type == "test":
        return _format_test_op(opref)
    else:
        if not nowarn:
            log.warning(
                "cannot format op desc, unexpected pkg type: %s (%s)",
                opref.pkg_type, opref.pkg_name)
        return "?"

def _format_guildfile_op(opref):
    parts = []
    gf_dir = _guildfile_dir(opref)
    if gf_dir:
        parts.extend([gf_dir, os.path.sep])
    if opref.model_name:
        parts.extend([opref.model_name, ":"])
    parts.append(opref.op_name)
    return "".join(parts)

def _guildfile_dir(opref):
    from guild import config
    gf_dir = os.path.dirname(opref.pkg_name)
    relpath = os.path.relpath(gf_dir, config.cwd())
    if relpath == ".":
        return ""
    return re.sub(r"\.\./(\.\./)+", ".../", _ensure_dot_path(relpath))

def _ensure_dot_path(path):
    if path[0:1] == ".":
        return path
    return os.path.join(".", path)

def _format_package_op(opref):
    return "%s/%s:%s" % (opref.pkg_name, opref.model_name, opref.op_name)

def _format_script_op(opref):
    return _format_guildfile_op(opref)

def _format_builtin_op(opref):
    return opref.op_name

def _format_pending_op(opref):
    return "<pending %s>" % opref.op_name

def _format_test_op(opref):
    return "%s:%s" % (opref.model_name, opref.op_name)

def _apply_batch_desc(base_desc, run, seen_protos):
    import guild.run
    try:
        proto_dir = run.guild_path("proto")
    except TypeError:
        # Occurs for run proxies that don't support guild_path - punt
        # with generic descriptor. (TODO: implement explicit behavior
        # in run interface + proxy)
        proto_dir = ""
    if not os.path.exists(proto_dir):
        return base_desc
    if proto_dir in seen_protos:
        # We have a cycle - drop this proto_dir
        return base_desc
    proto_run = guild.run.Run("", proto_dir)
    proto_op_desc = format_op_desc(proto_run, seen_protos)
    parts = [proto_op_desc]
    if not base_desc.startswith("+"):
        parts.append("+")
    parts.append(base_desc)
    return "".join(parts)

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
        "disable_plugins",
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
        "%s:%s" % (name, format_flag_val(val))
        for name, val in sorted(flags.items())
    ]
    to_hash = "\n".join(flag_parts).encode()
    return hashlib.md5(to_hash).hexdigest()

def restart_needed(run, flags):
    return run.status in RESTART_NEEDED_STATUS or run.get("flags") != flags

def parse_function(s):
    if not isinstance(s, six.string_types):
        raise ValueError("requires string")
    m = function_pattern.match(s)
    if not m:
        raise ValueError("not a function")
    name = m.group(1) or None
    args_raw = m.group(2).strip()
    if args_raw:
        args_s = args_raw.split(function_arg_delimiter)
    else:
        args_s = []
    args = [parse_arg_val(arg.strip()) for arg in args_s]
    return name, tuple(args)

def flag_assigns(flags):
    def fmt(val):
        if isinstance(val, float):
            val = round(val, 4)
        return shlex_quote(format_flag_val(val))
    return [
        "%s=%s" % (name, fmt(flags[name]))
        for name in sorted(flags)
    ]

def opdef_model_paths(opdef):
    return _opdef_paths(opdef) + _model_parent_paths(opdef.modeldef)

def _opdef_paths(opdef):
    if not opdef.guildfile.dir:
        return []
    abs_gf_dir = os.path.abspath(opdef.guildfile.dir)
    if opdef.python_path is not None:
        return [os.path.join(abs_gf_dir, p) for p in opdef.python_path]
    return [abs_gf_dir]

def _model_parent_paths(modeldef):
    return [os.path.abspath(parent.dir) for parent in modeldef.parents]

def _patch_yaml_safe_loader():
    # Credit: https://stackoverflow.com/users/1307905/anthon
    # Ref:    https://stackoverflow.com/questions/30458977/
    #         yaml-loads-5e-6-as-string-and-not-a-number
    loader = yaml.SafeLoader
    loader.add_implicit_resolver(
        u'tag:yaml.org,2002:float',
        re.compile(u'''^(?:
        [-+]?(?:[0-9][0-9_]*)\\.[0-9_]*(?:[eE][-+]?[0-9]+)?
        |[-+]?(?:[0-9][0-9_]*)(?:[eE][-+]?[0-9]+)
        |\\.[0-9_]+(?:[eE][-+][0-9]+)?
        |[-+]?[0-9][0-9_]*(?::[0-5]?[0-9])+\\.[0-9_]*
        |[-+]?\\.(?:inf|Inf|INF)
        |\\.(?:nan|NaN|NAN))$''', re.X),
        list(u'-+0123456789.'))

_patch_yaml_safe_loader()
