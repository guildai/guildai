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

from __future__ import absolute_import
from __future__ import division

import chardet
import datetime
import errno
import os
import logging
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time
import threading

log = logging.getLogger("guild")

PLATFORM = platform.system()

OS_ENVIRON_WHITELIST = set([
    "DISPLAY",
    "HOME",
    "HOSTNAME",
    "LANG",
    "LD_LIBRARY_PATH",
    "PATH",
    "PWD",
    "SHELL",
    "SSH_AGENT_PID",
    "SSH_AUTH_SOCK",
    "SSH_CONNECTION",
    "TEMP",
    "TERM",
    "TMP",
    "USER",
    "VIRTUAL_ENV",
])

class Stop(Exception):
    """Raise to stop loops started with `loop`."""

def find_apply(funs, *args, **kw):
    for f in funs:
        result = f(*args)
        if result is not None:
            return result
    return kw.get("default")

def ensure_dir(d):
    d = os.path.realpath(d)
    try:
        os.makedirs(d)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

def pid_exists(pid):
    import psutil
    return psutil.pid_exists(pid)

def free_port():
    import random
    import socket
    min_port = 49152
    max_port = 65535
    max_attempts = 100
    attempts = 0

    while True:
        if attempts > max_attempts:
            raise RuntimeError("too many free port attempts")
        port = random.randint(min_port, max_port)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.1)
        try:
            sock.connect(('localhost', port))
        except socket.timeout:
            return port
        except socket.error as e:
            if e.errno == errno.ECONNREFUSED:
                return port
        else:
            sock.close()
        attempts += 1

def open_url(url):
    try:
        _open_url_with_cmd(url)
    except OSError:
        _open_url_with_webbrowser(url)

def _open_url_with_cmd(url):
    if sys.platform == "darwin":
        args = ["open", url]
    else:
        args = ["xdg-open", url]
    with open(os.devnull, "w") as null:
        subprocess.check_call(args, stderr=null, stdout=null)

def _open_url_with_webbrowser(url):
    import webbrowser
    webbrowser.open(url)

def loop(cb, wait, interval, first_interval=None):
    try:
        _loop(cb, wait, interval, first_interval)
    except Stop:
        pass
    except KeyboardInterrupt:
        pass

def _loop(cb, wait, interval, first_interval):
    loop_interval = first_interval if first_interval is not None else interval
    start = time.time()
    while True:
        sleep = _sleep_interval(loop_interval, start)
        loop_interval = interval
        should_stop = wait(sleep)
        if should_stop:
            break
        cb()

def _sleep_interval(interval, start):
    if interval <= 0:
        return 0
    now_ms = int(time.time() * 1000)
    interval_ms = int(interval * 1000)
    start_ms = int(start * 1000)
    sleep_ms = (
        ((now_ms - start_ms) // interval_ms + 1)
        * interval_ms + start_ms - now_ms)
    return sleep_ms / 1000

class LoopingThread(threading.Thread):

    def __init__(self, cb, interval, first_interval=None, stop_timeout=0):
        super(LoopingThread, self).__init__()
        self._cb = cb
        self._interval = interval
        self._first_interval = first_interval
        self._stop_timeout = stop_timeout
        self._stop = threading.Event()
        self._stopped = threading.Event()

    def run(self):
        loop(
            cb=self._cb,
            wait=self._stop.wait,
            interval=self._interval,
            first_interval=self._first_interval)
        self._stopped.set()

    def stop(self):
        self._stop.set()
        self._stopped.wait(self._stop_timeout)

def safe_osenv():
    return {
        name: val
        for name, val in os.environ.items()
        if name in OS_ENVIRON_WHITELIST
    }

def match_filters(filters, vals, match_any=False):
    test_fun = any if match_any else all
    vals_lower = [val.lower() for val in vals]
    filters_lower = [f.lower() for f in filters]
    return test_fun(
        (any((f in val for val in vals_lower))
         for f in filters_lower)
    )

def split_description(s):
    lines = s.split("\n")
    return lines[0], _format_details(lines[1:])

def _format_details(details):
    lines = []
    for i, line in enumerate(details):
        if i > 0:
            lines.append("")
        lines.append(line)
    return lines

def file_sha256(path, use_cache=True):
    if use_cache:
        cached_sha = try_cached_sha(path)
        if cached_sha:
            return cached_sha
    import hashlib
    hash = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            data = f.read(102400)
            if not data:
                break
            hash.update(data)
    return hash.hexdigest()

def try_cached_sha(for_file):
    try:
        f = open(_cached_sha_filename(for_file), "r")
    except IOError:
        return None
    else:
        return f.read().rstrip()

def _cached_sha_filename(for_file):
    parent, name = os.path.split(for_file)
    return os.path.join(parent, ".guild-cache-%s.sha" % name)

def write_cached_sha(sha, for_file):
    with open(_cached_sha_filename(for_file), "w") as f:
        f.write(sha)

def parse_url(url):
    try:
        from urlparse import urlparse
    except ImportError:
        # pylint: disable=import-error,no-name-in-module
        from urllib.parse import urlparse
    return urlparse(url)

class TempDir(object):

    def __init__(self, prefix="guild-", suffix="", keep=False):
        self._prefix = prefix
        self._suffix = suffix
        self._keep = keep
        self.path = None

    def __enter__(self):
        self.path = tempfile.mkdtemp(prefix=self._prefix, suffix=self._suffix)
        return self.path

    def __exit__(self, *_exc):
        if not self._keep:
            rmtempdir(self.path)

def mktempdir(prefix=None):
    return tempfile.mkdtemp(prefix=prefix)

def rmtempdir(path):
    assert os.path.dirname(path) == tempfile.gettempdir(), path
    try:
        shutil.rmtree(path)
    except Exception as e:
        if log.getEffectiveLevel() <= logging.DEBUG:
            log.exception("rmtree %s", path)
        else:
            log.error("error removing %s: %s", path, e)

class LogCapture(object):

    def __init__(self):
        self._records = []

    def __enter__(self):
        for logger in self._iter_loggers():
            logger.addFilter(self)
        self._records = []
        return self

    def __exit__(self, *exc):
        for logger in self._iter_loggers():
            logger.removeFilter(self)

    @staticmethod
    def _iter_loggers():
        yield logging.root
        for logger in logging.Logger.manager.loggerDict.values():
            if isinstance(logger, logging.Logger):
                yield logger

    def filter(self, record):
        self._records.append(record)

    def print_all(self):
        format = logging.root.handlers[0].format
        for r in self._records:
            print(format(r))

    def get_all(self):
        return self._records

def format_timestamp(ts):
    if not ts:
        return ""
    dt = datetime.datetime.fromtimestamp(ts / 1000000)
    return dt.strftime("%Y-%m-%d %H:%M:%S")

_raise_error_marker = object()

def resolve_refs(val, kv, undefined=_raise_error_marker):
    return _resolve_refs_recurse(val, kv, undefined, [])

def resolve_all_refs(kv, undefined=_raise_error_marker):
    resolved = {}
    for name in sorted(kv):
        resolved[name] = _resolve_refs_recurse(kv[name], kv, undefined, [])
    return resolved

def _resolve_refs_recurse(val, kv, undefined, stack):
    if not isinstance(val, str):
        return val
    parts = [part for part in re.split(r"(\\?\${.+?})", val) if part != ""]
    resolved = list(_iter_resolved_ref_parts(parts, kv, undefined, stack))
    if len(resolved) == 1:
        return resolved[0]
    else:
        return "".join([str(part) for part in resolved])

class ReferenceCycleError(Exception):
    pass

class UndefinedReferenceError(Exception):
    pass

def _iter_resolved_ref_parts(parts, kv, undefined, stack):
    for part in parts:
        if part.startswith("${") and part.endswith("}"):
            ref_name = part[2:-1]
            if ref_name in stack:
                raise ReferenceCycleError(stack + [ref_name])
            stack.append(ref_name)
            ref_val = kv.get(ref_name, undefined)
            if ref_val is _raise_error_marker:
                raise UndefinedReferenceError(ref_name)
            yield _resolve_refs_recurse(ref_val, kv, undefined, stack)
            stack.pop()
        elif part.startswith("\\${") and part.endswith("}"):
            yield part[1:-1]
        else:
            yield part

def strip_trailing_path(path):
    if path and path[-1] in ("/", "\\"):
        return path[:-1]
    else:
        return path

def strip_trailing_period(s):
    if s[-1:] == ".":
        return s[:-1]
    return s

def which(cmd):
    which_cmd = "where" if PLATFORM == "Windows" else "which"
    devnull = open(os.devnull, "w")
    try:
        out = subprocess.check_output([which_cmd, cmd], stderr=devnull)
    except subprocess.CalledProcessError:
        return None
    else:
        return out.strip().decode("utf-8")

def symlink(target, link):
    if PLATFORM == "Windows":
        _windows_symlink(target, link)
    else:
        os.symlink(target, link)

def _windows_symlink(target, link):
    if os.path.isdir(target):
        args = ["mklink", "/D", link, target]
    else:
        args = ["mklink", link, target]
    try:
        subprocess.check_output(args, shell=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        log.error(e.output)
        raise

_text_ext = set([
    ".csv",
    ".md",
    ".py",
    ".sh",
    ".txt",
])

_binary_ext = set([
    ".bin",
    ".gif",
    ".gz",
    ".jpeg",
    ".jpg",
    ".png",
    ".rar",
    ".tar",
    ".tif",
    ".tiff",
    ".xz",
    ".zip",
])

_control_chars = b'\n\r\t\f\b'
if bytes is str:
    _printable_ascii = _control_chars + b"".join(
        [chr(x) for x in range(32, 127)])
    _printable_high_ascii = b"".join(
        [chr(x) for x in range(127, 256)])
else:
    _printable_ascii = _control_chars + bytes(range(32, 127))
    _printable_high_ascii = bytes(range(127, 256))

def is_text_file(path, ignore_ext=False):
    # Adapted from https://github.com/audreyr/binaryornot under the
    # BSD 3-clause License
    if os.path.isdir(path):
        return False
    if not ignore_ext:
        ext = os.path.splitext(path)[1].lower()
        if ext in _text_ext:
            return True
        if ext in _binary_ext:
            return False
    with open(path, 'rb') as f:
        sample = f.read(1024)
    if not sample:
        return True
    low_chars = sample.translate(None, _printable_ascii)
    nontext_ratio1 = float(len(low_chars)) / float(len(sample))
    high_chars = sample.translate(None, _printable_high_ascii)
    nontext_ratio2 = float(len(high_chars)) / float(len(sample))
    likely_binary = (
        (nontext_ratio1 > 0.3 and nontext_ratio2 < 0.05) or
        (nontext_ratio1 > 0.8 and nontext_ratio2 > 0.8)
    )
    detected_encoding = chardet.detect(sample)
    decodable_as_unicode = False
    if (detected_encoding["confidence"] > 0.9 and
        detected_encoding["encoding"] != "ascii"):
        try:
            try:
                sample.decode(encoding=detected_encoding["encoding"])
            except TypeError:
                # pylint: disable=undefined-variable
                unicode(sample, encoding=detected_encoding["encoding"])
            decodable_as_unicode = True
        except LookupError:
            pass
        except UnicodeDecodeError:
            pass
    if likely_binary:
        return decodable_as_unicode
    else:
        if decodable_as_unicode:
            return True
        else:
            if b'\x00' in sample or b'\xff' in sample:
                return False
        return True

def touch(filename):
    open(filename, "a").close()

def getmtime(filename):
    try:
        return os.path.getmtime(filename)
    except OSError:
        return None

def kill_process_tree(pid, force=False, timeout=None):
    import psutil
    import signal
    if force:
        sig = signal.SIGKILL
    else:
        sig = signal.SIGTERM
    root = psutil.Process(pid)
    procs = [root] + root.children(recursive=True)
    for proc in procs:
        proc.send_signal(sig)
    return psutil.wait_procs(procs, timeout=timeout)

def safe_filesize(path):
    try:
        return os.path.getsize(path)
    except OSError:
        return None

def try_remove(l, remove):
    for x in remove:
        try:
            l.remove(x)
        except ValueError:
            pass

def local_server_url(host, port):
    import socket
    if not host or host == "0.0.0.0":
        host = socket.gethostname()
        try:
            # Verify that configured hostname is valid
            socket.gethostbyname(host)
        except socket.gaierror:
            host = "localhost"
    return "http://{}:{}".format(host, port)

def format_duration(start_time, end_time=None):
    if end_time is None:
        end_time = time.time() * 1000000
    seconds = (end_time - start_time) // 1000000
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return "%d:%02d:%02d" % (h, m, s)
