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

import logging
import os
import struct
import sys
import threading
import time

import yaml

import guild.run
from guild import util

log = logging.getLogger("guild")

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
    return dict([_parse_flag_arg(os.path.expanduser(arg)) for arg in args])

def _parse_flag_arg(arg):
    parts = arg.split("=", 1)
    if len(parts) == 1:
        raise ArgValueError(arg)
    else:
        return parts[0], _parse_arg_val(parts[1])

def _parse_arg_val(s):
    parsers = [
        (int, ValueError),
        (float, ValueError),
        (yaml.safe_load, yaml.YAMLError),
    ]
    for p, e_type in parsers:
        try:
            return p(s)
        except e_type:
            pass
    return s

def format_arg_value(v):
    if v is True:
        return "yes"
    elif v is False:
        return "no"
    else:
        return str(v)

class NoCurrentRun(Exception):
    pass

def current_run():
    """Returns an instance of guild.run.Run for the current run.

    The current run directory must be specified with the RUN_DIR
    environment variable. If this variable is not defined, raised
    NoCurrentRun.

    """
    path = os.getenv("RUN_DIR")
    if not path:
        raise NoCurrentRun()
    return guild.run.Run(os.getenv("RUN_ID"), path)

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
            flags[name] = _parse_arg_val(arg)
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
    if (val and flag.choices and
        val not in [choice.value for choice in flag.choices]):
        raise InvalidFlagChoice(val, flag)

def _check_flag_type(val, flag):
    if flag.type == "existing-path":
        if val and not os.path.exists(val):
            raise InvalidFlagValue(val, flag, "%s does not exist" % val)
