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

import chardet
import datetime
import errno
import fnmatch
import os
import logging
import platform
import re
import shlex
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import threading

log = logging.getLogger("guild")

PLATFORM = platform.system()

OS_ENVIRON_BLACKLIST = set([])

class Stop(Exception):
    """Raise to stop loops started with `loop`."""

class TryFailed(RuntimeError):
    """Raise to indicate an attempt in try_apply failed."""

def find_apply(funs, *args, **kw):
    for f in funs:
        result = f(*args)
        if result is not None:
            return result
    return kw.get("default")

def try_apply(funs, *args):
    for f in funs:
        try:
            return f(*args)
        except TryFailed:
            continue
    raise TryFailed(funs, args)

def ensure_dir(d):
    d = os.path.realpath(d)
    try:
        os.makedirs(d)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

def ensure_deleted(path):
    try:
        os.remove(path)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise

def try_read(path, default=None, apply=None):
    try:
        f = open(path, "r")
    except IOError as e:
        if e.errno != errno.ENOENT:
            raise
        return default
    else:
        out = f.read()
        if apply:
            if not isinstance(apply, list):
                apply = [apply]
            for f in apply:
                out = f(out)
        return out

def pid_exists(pid):
    try:
        import psutil
    except Exception as e:
        log.warning("cannot get stat for pid %s: %s", pid, e)
        if log.getEffectiveLevel() <= logging.DEBUG:
            log.exception("importing psutil")
        return False
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
    except (OSError, URLOpenError):
        _open_url_with_webbrowser(url)

class URLOpenError(Exception):
    pass

def _open_url_with_cmd(url):
    if sys.platform == "darwin":
        args = ["open", url]
    else:
        args = ["xdg-open", url]
    with open(os.devnull, "w") as null:
        try:
            subprocess.check_call(args, stderr=null, stdout=null)
        except subprocess.CalledProcessError as e:
            raise URLOpenError(url, e)

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
        if name not in OS_ENVIRON_BLACKLIST
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

def file_md5(path):
    import hashlib
    hash = hashlib.md5()
    with open(path, "rb") as f:
        while True:
            data = f.read(102400)
            if not data:
                break
            hash.update(data)
    return hash.hexdigest()

def parse_url(url):
    try:
        from urlparse import urlparse
    except ImportError:
        # pylint: disable=import-error,no-name-in-module
        from urllib.parse import urlparse
    return urlparse(url)

class TempBase(object):

    def __init__(self, prefix="guild-", suffix="", keep=False):
        self._prefix = prefix
        self._suffix = suffix
        self._keep = keep
        self.path = None

    def __enter__(self):
        self.path = self._init_temp(self._prefix, self._suffix)
        return self.path

    @staticmethod
    def _init_temp(prefix, suffix):
        raise NotImplementedError()

    def __exit__(self, *_exc):
        if not self._keep:
            self._del_temp(self.path)

    @staticmethod
    def _del_temp(path):
        raise NotImplementedError()

class TempDir(TempBase):

    @staticmethod
    def _init_temp(prefix, suffix):
        return tempfile.mkdtemp(prefix=prefix, suffix=suffix)

    @staticmethod
    def _del_temp(path):
        rmtempdir(path)

class TempFile(TempBase):

    @staticmethod
    def _init_temp(prefix, suffix):
        f, path = tempfile.mkstemp(prefix=prefix, suffix=suffix)
        os.close(f)
        return path

    @staticmethod
    def _del_temp(path):
        os.remove(path)

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

def safe_rmtree(path):
    """Removes path if it's not top level or user dir."""
    assert not _top_level_dir(path), path
    assert path != os.path.expanduser("~"), path
    shutil.rmtree(path)

def _top_level_dir(path):
    abs_path = os.path.abspath(path)
    parts = [p for p in re.split(r"[/\\]", abs_path) if p]
    if PLATFORM == "Windows":
        return len(parts) <= 2
    return len(parts) <= 1

class LogCapture(object):

    def __init__(self, use_root_handler=False):
        self._records = []
        self._use_root_handler = use_root_handler

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
        handler = self._handler()
        for r in self._records:
            print(handler.format(r))

    def _handler(self):
        if self._use_root_handler:
            return logging.root.handlers[0]
        from guild import log
        return log.ConsoleLogHandler()

    def get_all(self):
        return self._records

def format_timestamp(ts, fmt=None):
    if not ts:
        return ""
    dt = datetime.datetime.fromtimestamp(ts / 1000000)
    return dt.strftime(fmt or "%Y-%m-%d %H:%M:%S")

def utcformat_timestamp(ts, fmt=None):
    if not ts:
        return None
    dt = datetime.datetime.utcfromtimestamp(ts / 1000000)
    return dt.strftime(fmt or "%Y-%m-%d %H:%M:%S UTC")

_raise_error_marker = object()

def resolve_refs(val, kv, undefined=_raise_error_marker):
    return _resolve_refs_recurse(val, kv, undefined, [])

def resolve_all_refs(kv, undefined=_raise_error_marker):
    return {
        name: _resolve_refs_recurse(kv[name], kv, undefined, [])
        for name in sorted(kv)
    }

def _resolve_refs_recurse(val, kv, undefined, stack):
    if not isinstance(val, str):
        return val
    parts = [part for part in re.split(r"(\\?\${.+?})", val) if part != ""]
    resolved = list(_iter_resolved_ref_parts(parts, kv, undefined, stack))
    if len(resolved) == 1:
        return resolved[0]
    else:
        return "".join([_resolved_part_str(part) for part in resolved])

def _resolved_part_str(part):
    if part is None:
        return "null"
    return str(part)

def resolve_rel_paths(kv):
    return {
        name: _resolve_rel_path(kv[name])
        for name in kv
    }

def _resolve_rel_path(maybe_path):
    if os.path.exists(maybe_path) and not os.path.isabs(maybe_path):
        return os.path.abspath(maybe_path)
    return maybe_path

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
    ".pyc",
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
    if not os.path.exists(path):
        raise ValueError("%s does not exist" % path)
    if not os.path.isfile(path):
        return False
    if not ignore_ext:
        ext = os.path.splitext(path)[1].lower()
        if ext in _text_ext:
            return True
        if ext in _binary_ext:
            return False
    try:
        with open(path, 'rb') as f:
            sample = f.read(1024)
    except IOError:
        return False
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

def safe_mtime(path):
    try:
        return os.path.getmtime(path)
    except OSError:
        return None

def apply_remove(x, f):
    apply_remove_all([x], f)

def apply_remove_all(xs, f):
    for x in xs:
        try:
            f.remove(x)
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
    if start_time is None:
        return None
    if end_time is None:
        end_time = time.time() * 1000000
    seconds = (end_time - start_time) // 1000000
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return "%d:%02d:%02d" % (h, m, s)

def format_dir(dir):
    abs_cwd = os.path.abspath(dir)
    user_dir = os.path.expanduser("~")
    if abs_cwd.startswith(user_dir):
        return os.path.join("~", abs_cwd[len(user_dir)+1:])
    else:
        return abs_cwd

def apply_env(target, source, names):
    for name in names:
        try:
            target[name] = source[name]
        except KeyError:
            pass

def safe_filename(s):
    if PLATFORM == "Windows":
        return s.replace(":", "_")
    return re.sub(r"[/\\]+", "_", s)

def wait_forever(sleep_interval=0.1):
    while True:
        time.sleep(sleep_interval)

class RunOutputReader(object):

    def __init__(self, run_dir):
        self.run_dir = run_dir
        self._lines = []
        self._output = None
        self._index = None

    def read(self, start=0, end=None):
        """Read run output from start to end.

        Both start and end are zero-based indexes to run output lines
        and are both inclusive. Note this is different from the Python
        slice function where end is exclusive.
        """
        self._read_next(end)
        if end is None:
            slice_end = None
        else:
            slice_end = end + 1
        return self._lines[start:slice_end]

    def _read_next(self, end):
        if end is not None and end < len(self._lines):
            return
        try:
            output, index = self._ensure_open()
        except IOError as e:
            if e.errno != errno.EEXIST:
                raise
        else:
            lines = self._lines
            while True:
                line = output.readline().rstrip().decode()
                if not line:
                    break
                time, stream = struct.unpack("!QB", index.read(9))
                lines.append((time, stream, line))
                if end is not None and end < len(self._lines):
                    break

    def _ensure_open(self):
        if self._output is None:
            guild_path = os.path.join(self.run_dir, ".guild")
            output = open(os.path.join(guild_path, "output"), "rb")
            index = open(os.path.join(guild_path, "output.index"), "rb")
            self._output, self._index = output, index
        assert self._output is not None
        assert self._index is not None
        return self._output, self._index

    def close(self):
        self._try_close(self._output)
        self._try_close(self._index)

    @staticmethod
    def _try_close(f):
        if f is None:
            return
        try:
            f.close()
        except IOError:
            pass

def gpu_available():
    import ctypes
    if "linux" in sys.platform:
        lib = "libcublas.so"
    elif sys.platform == "darwin":
        lib = "libcublas.dylib"
    elif sys.platform == "win32":
        lib = "cublas.dll"
    else:
        log.warning("unable to detect GPU for platform '%s'", sys.platform)
        lib = None
    if lib:
        log.debug("checking for GPU by loading %s", lib)
        try:
            ctypes.CDLL(lib)
        except OSError as e:
            log.debug("error loading '%s': %s", lib, e)
        else:
            log.debug("%s loaded", lib)
            return True
    return False

def render_label(template, vals):
    tokens = re.split(r"(\${.+?})", template)
    return "".join([_rendered_str(_render_token(t, vals)) for t in tokens])

def _render_token(token, vals):
    m = re.match(r"\${(.+?)}", token)
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
    parts = t.split(":", 1)
    if len(parts) == 1:
        name = parts[0]
        arg = None
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
    else:
        log.warning("unsupported template transform: %r", t)
        return "#error#"

def _t_python_format(val, fmt):
    try:
        return fmt % val
    except TypeError as e:
        log.warning("error formatting %r with %r: %s", val, fmt, e)
        return val

def _t_default(val, arg):
    if val is None:
        return arg or ""
    return val

def _t_basename(val):
    if not val:
        return ""
    return os.path.basename(strip_trailing_path(val))

def _rendered_str(s):
    if s is None:
        return ""
    return str(s)

def del_env(names):
    for name in names:
        try:
            del os.environ[name]
        except KeyError:
            pass

def python_interpreters():
    import glob
    bin_dir = os.path.dirname(sys.executable)
    ret = []
    for path in glob.glob(os.path.join(bin_dir, "python*")):
        m = re.match(r"python([0-9\.]+)$", os.path.basename(path))
        if m:
            ret.append((path, m.group(1)))
    return ret

def find_python_interpreter(version_spec):
    import pkg_resources
    try:
        # Requirement.parse wants a package name, so we use 'python'
        # here, but anything would do.
        req = pkg_resources.Requirement.parse("python%s" % version_spec)
    except pkg_resources.RequirementParseError:
        raise ValueError(version_spec)
    python_interps = {ver: path for path, ver in python_interpreters()}
    matching = list(req.specifier.filter(sorted(python_interps)))
    if matching:
        matching_ver = matching[0]
        return python_interps[matching_ver], matching_ver
    return None

def is_executable_file(path):
    return os.path.isfile(path) and os.access(path, os.X_OK)

def copytree(src, dest, preserve_links=True):
    from distutils import dir_util
    dir_util.copy_tree(src, dest, preserve_symlinks=preserve_links)

def select_copytree(src, dest, config, copy_filter=None):
    if not isinstance(config, list):
        raise ValueError("invalid config: expected list got %r" % config)
    log.debug("copying files from %s to %s", src, dest)
    to_copy = _select_files_to_copy(src, config, copy_filter)
    if not to_copy:
        log.debug("no files to copy")
        return
    for file_src, file_src_rel_path in to_copy:
        file_dest = os.path.join(dest, file_src_rel_path)
        log.debug("copying file %s to %s", file_src, file_dest)
        ensure_dir(os.path.dirname(file_dest))
        _try_copy_file(file_src, file_dest)

def _select_files_to_copy(src_dir, config, copy_filter):
    to_copy = []
    seen_dirs = set()
    log.debug("generating file list from %s", src_dir)
    for root, dirs, files in os.walk(src_dir, followlinks=True):
        seen_dirs.add(os.path.realpath(root))
        _del_excluded_select_copy_dirs(root, dirs, seen_dirs, copy_filter)
        for name in files:
            path = os.path.join(root, name)
            if not os.path.isfile(path):
                continue
            rel_path = os.path.relpath(path, src_dir)
            log.debug("considering file to copy %s", path)
            if _select_to_copy(path, rel_path, config, copy_filter):
                log.debug("seleted file to copy %s", path)
                to_copy.append((path, rel_path))
    # Sort before notifying copy_filter to have deterministic result.
    to_copy.sort()
    if copy_filter:
        copy_filter.pre_copy(to_copy)
    return to_copy

def _del_excluded_select_copy_dirs(root, dirs, seen_dirs, copy_filter):
    _del_seen_dirs(dirs, root, seen_dirs)
    if copy_filter:
        copy_filter.delete_excluded_dirs(root, dirs)

def _del_seen_dirs(dirs, root, seen):
    for dir_name in dirs:
        real_path = os.path.realpath(os.path.join(root, dir_name))
        if real_path in seen:
            dirs.remove(dir_name)

def _select_to_copy(path, rel_path, config, copy_filter):
    assert isinstance(config, list)
    last_match = None
    for config_item in config:
        for spec in config_item.specs:
            if _select_file_match(rel_path, spec):
                last_match = spec
    if last_match:
        return _select_to_copy_for_spec(last_match)
    if copy_filter:
        return copy_filter.default_select_path(path)
    return True

def _select_file_match(rel_path, spec):
    return any((fnmatch.fnmatch(rel_path, p) for p in spec.patterns))

def _select_to_copy_for_spec(spec):
    return spec.type == "include"

def _try_copy_file(src, dest):
    try:
        shutil.copyfile(src, dest)
    except (IOError, OSError) as e:
        # This is not an error we want to stop an operation for. Log
        # and continue.
        if log.getEffectiveLevel() <= logging.DEBUG:
            log.exception("copy %s to %s", src, dest)
        else:
            log.warning("could not copy source code file %s: %s", src, e)

def hostname():
    return os.getenv("HOST") or _real_hostname()

def _real_hostname():
    import socket
    try:
        return socket.gethostname()
    except Exception:
        if log.getEffectiveLevel() <= logging.DEBUG:
            log.exception("socket.gethostname()")
        return ""

def user():
    return os.getenv("USER") or ""

def shlex_split(s):
    # If s is None, this call will block (see
    # https://bugs.python.org/issue27775)
    s = s or ""
    return shlex.split(s)

def shlex_quote(s):
    # If s can't be None in case where pipes.quote is used by six.
    import six
    s = s or ""
    return six.moves.shlex_quote(s)

def format_bytes(n):
    units = [None, "K", "M", "G", "T", "P", "E", "Z"]
    for unit in units[:-1]:
        if abs(n) < 1024:
            if not unit:
                return str(n)
            return "%3.1f%s" % (n, unit)
        n /= 1024.0
    return "%.1f%s" % (n, units[-1])

class Chdir(object):

    _save = None

    def __init__(self, path):
        self._path = path

    def __enter__(self):
        self._save = os.getcwd()
        os.chdir(self._path)

    def __exit__(self, *_args):
        os.chdir(self._save)

def log_apply(f, *args, **kw):
    level = kw.pop("logging_level", logging.DEBUG)
    prefix = kw.pop("logging_prefix", "CALLING")
    log.log(level, "%s %s", prefix, _log_apply_msg(f, args, kw))
    return f(*args, **kw)

class _log_apply_msg(object):

    def __init__(self, f, args, kw):
        self.f = f
        self.args = args
        self.kw = kw

    def __str__(self):
        return "%s %s %s %s" % (
            self.f.__module__, self.f.__name__, self.args, self.kw)

def encode_yaml(val):
    import yaml
    encoded = yaml.safe_dump(
        val,
        default_flow_style=False,
        indent=2)
    if encoded.endswith("\n...\n"):
        encoded = encoded[:-4]
    return encoded

def dir_size(dir):
    size = 0
    for root, dirs, names in os.walk(dir):
        for name in dirs + names:
            size += os.path.getsize(os.path.join(root, name))
    return size
