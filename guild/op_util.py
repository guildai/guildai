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
import logging
import os
import shlex
import shutil
import struct
import sys
import threading
import time

import yaml

from guild import util
from guild import binaryornot

log = logging.getLogger("guild")

# Legacy support for functionality moved to _api
from guild import _api
NoCurrentRun = _api.NoCurrentRun
current_run = _api.current_run

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

    def __init__(self, run, proc=None, quiet=False):
        assert run
        self._run = run
        self._quiet = quiet
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
                    os_write(output_fileno, b"".join(line))
                    line = []
                    entry = struct.pack(
                        "!QB", int(time_() * 1000), stream_type)
                    os_write(index_fileno, entry)

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
        self._assert_open()
        self._output.close()
        self._index.close()
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
        (_safe_float, ValueError),
        (yaml.safe_load, yaml.YAMLError),
    ]
    for p, e_type in parsers:
        try:
            return p(s)
        except e_type:
            pass
    return s

def _safe_float(s):
    """Returns a float for a string or raises ValueError.

    In cases where Python's float function would succeed in converting
    exponent notation without a decimal (e.g. '1e2') this raises
    ValueError.
    """
    if "." not in s:
        raise ValueError(s)
    return float(s)

def format_flag_val(val, use_nulls=False):
    if val is True:
        return "yes"
    elif val is False:
        return "no"
    elif val is None:
        return "null" if use_nulls else ""
    elif isinstance(val, list):
        return _format_flag_list(val)
    else:
        return str(val)

def _format_flag_list(val_list):
    joined = ", ".join([format_flag_val(val) for val in val_list])
    return "[%s]" % joined

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
    flags = {}
    name = None
    for arg in args:
        if arg[:2] == "--":
            name = arg[2:]
            flags[name] = True
        elif arg[:1] == "-":
            if len(arg) == 2:
                name = arg[1]
                flags[name] = True
            elif len(arg) > 2:
                name = None
                flags[arg[1]] = arg[2:]
        elif name is not None:
            flags[name] = parse_arg_val(arg)
    return flags

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

def coerce_flag_value(val, flag):
    if not flag or not flag.type:
        return val
    if flag.type == "string":
        return _try_coerce_flag_val(val, str, flag)
    elif flag.type == "int":
        if isinstance(val, float):
            raise ValueError("invalid value for type 'int'")
        return _try_coerce_flag_val(val, int, flag)
    elif flag.type == "float":
        return _try_coerce_flag_val(val, float, flag)
    elif flag.type == "number":
        if isinstance(val, (float, int)):
            return val
        return _try_coerce_flag_val(val, (int, float), flag)
    elif flag.type in ("path", "existing-path"):
        return _resolve_rel_path(val)
    else:
        log.warning(
            "unknown flag type '%s' for %s - cannot coerce",
            flag.type, flag.name)
        return val

def _try_coerce_flag_val(val, funs, flag):
    if not isinstance(funs, tuple):
        funs = (funs,)
    for f in funs:
        try:
            return f(val)
        except ValueError as e:
            log.debug("value error applying %s to %r: %s", f, val, e)
    raise ValueError("invalid value for type '%s'" % flag.type)

def _resolve_rel_path(val):
    if val is not None and not os.path.isabs(val):
        return os.path.abspath(val)
    return val

def validate_opdef_flags(opdef):
    vals = opdef.flag_values()
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

def _check_flag_choice(val, flag):
    if (val and flag.choices and not flag.allow_other and
        val not in [choice.value for choice in flag.choices]):
        raise InvalidFlagChoice(val, flag)

def _check_flag_type(val, flag):
    if flag.type == "existing-path":
        if val and not os.path.exists(val):
            raise InvalidFlagValue(val, flag, "%s does not exist" % val)

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
