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

import datetime
import errno
import fnmatch
import os
import logging
import re
import shlex
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import threading

import six

from guild import ansi_util  # lightweight

# Avoid expensive imports.

log = logging.getLogger("guild")

UNSAFE_OS_ENVIRON = set(["_"])

REF_P = re.compile(r"(\\?\${.+?})")


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
    d = realpath(d)
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


def pid_exists(pid, default=True):
    return find_apply(
        [
            _proc_pid_exists,
            _psutil_pid_exists,
            lambda _: default,
        ],
        pid,
    )


def _proc_pid_exists(pid):
    if os.path.exists("/proc"):
        return os.path.exists(os.path.join("/proc", str(pid)))
    return None


def _psutil_pid_exists(pid):
    try:
        import psutil
    except Exception as e:
        log.warning("cannot get status for pid %s: %s", pid, e)
        if log.getEffectiveLevel() <= logging.DEBUG:
            log.exception("importing psutil")
        return None
    return psutil.pid_exists(pid)


def free_port(start=None):
    import random
    import socket

    min_port = 49152
    max_port = 65535
    max_attempts = 100
    attempts = 0
    if start is None:
        next_port = lambda _p: random.randint(min_port, max_port)
        port = next_port(None)
    else:
        next_port = lambda p: p + 1
        port = start
    while True:
        if attempts > max_attempts:
            raise RuntimeError("too many free port attempts")
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
        port = next_port(port)


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
        ((now_ms - start_ms) // interval_ms + 1) * interval_ms + start_ms - now_ms
    )
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
        try:
            loop(
                cb=self._cb,
                wait=self._stop.wait,
                interval=self._interval,
                first_interval=self._first_interval,
            )
        finally:
            self._stopped.set()

    def stop(self):
        self._stop.set()
        self._stopped.wait(self._stop_timeout)


def safe_osenv():
    return {
        name: val for name, val in os.environ.items() if name not in UNSAFE_OS_ENVIRON
    }


def match_filters(filters, vals, match_any=False):
    test_fun = any if match_any else all
    vals_lower = [val.lower() for val in vals]
    filters_lower = [f.lower() for f in filters]
    return test_fun((any((f in val for val in vals_lower)) for f in filters_lower))


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
        self.path = self._init_temp(self._prefix, self._suffix)

    def __enter__(self):
        return self

    @staticmethod
    def _init_temp(prefix, suffix):
        raise NotImplementedError()

    def __exit__(self, *_exc):
        if not self._keep:
            self.delete()

    def keep(self):
        self._keep = True

    @staticmethod
    def delete():
        raise NotImplementedError()


class TempDir(TempBase):
    @staticmethod
    def _init_temp(prefix, suffix):
        return tempfile.mkdtemp(prefix=prefix, suffix=suffix)

    def delete(self):
        rmtempdir(self.path)


class TempFile(TempBase):
    @staticmethod
    def _init_temp(prefix, suffix):
        f, path = tempfile.mkstemp(prefix=prefix, suffix=suffix)
        os.close(f)
        return path

    def delete(self):
        os.remove(self.path)


def mktempdir(prefix=""):
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


def ensure_safe_rmtree(path):
    try:
        safe_rmtree(path)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise


def _top_level_dir(path):
    abs_path = os.path.abspath(path)
    parts = [p for p in re.split(r"[/\\]", abs_path) if p]
    if get_platform() == "Windows":
        return len(parts) <= 2
    return len(parts) <= 1


class LogCapture(object):
    def __init__(
        self,
        use_root_handler=False,
        echo_to_stdout=False,
        strip_ansi_format=True,
        log_level=None,
    ):
        self._records = []
        self._use_root_handler = use_root_handler
        self._echo_to_stdout = echo_to_stdout
        self._strip_ansi_format = strip_ansi_format
        self._log_level = log_level
        self._saved_log_levels = {}

    def __enter__(self):
        assert not self._saved_log_levels
        for logger in self._iter_loggers():
            logger.addFilter(self)
            self._apply_log_level(logger)
        self._records = []
        return self

    def __exit__(self, *exc):
        for logger in self._iter_loggers():
            self._restore_log_level(logger)
            logger.removeFilter(self)
        self._saved_log_levels.clear()

    def _apply_log_level(self, logger):
        if self._log_level is not None:
            self._saved_log_levels[logger] = logger.level
            logger.setLevel(self._log_level)

    def _restore_log_level(self, logger):
        try:
            level = self._saved_log_levels[logger]
        except KeyError:
            pass
        else:
            logger.setLevel(level)

    @staticmethod
    def _iter_loggers():
        yield logging.root
        for logger in logging.Logger.manager.loggerDict.values():
            if isinstance(logger, logging.Logger):
                yield logger

    def filter(self, record):
        self._records.append(record)
        if self._echo_to_stdout:
            sys.stdout.write(self._format_record(record))
            sys.stdout.write("\n")

    def _format_record(self, r):
        msg = self._handler().format(r)
        if self._strip_ansi_format:
            msg = ansi_util.strip_ansi_format(msg)
        return msg

    def print_all(self):
        for r in self._records:
            sys.stdout.write(self._format_record(r))
            sys.stdout.write("\n")

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
        name: _resolve_refs_recurse(kv[name], kv, undefined, []) for name in sorted(kv)
    }


def _resolve_refs_recurse(val, kv, undefined, stack):
    if not isinstance(val, six.string_types):
        return val
    parts = [part for part in REF_P.split(val) if part != ""]
    resolved = list(_iter_resolved_ref_parts(parts, kv, undefined, stack))
    if len(resolved) == 1:
        return resolved[0]
    else:
        return "".join([_resolved_part_str(part) for part in resolved])


def _resolved_part_str(part):
    if isinstance(part, six.string_types):
        return part
    from guild import yaml_util  # expensive

    return yaml_util.encode_yaml(part)


def resolve_rel_paths(kv):
    return {name: _resolve_rel_path(kv[name]) for name in kv}


def _resolve_rel_path(maybe_path):
    if os.path.exists(maybe_path) and not os.path.isabs(maybe_path):
        return os.path.abspath(maybe_path)
    return maybe_path


class ReferenceCycleError(Exception):
    pass


class UndefinedReferenceError(Exception):
    def __init__(self, reference):
        super(UndefinedReferenceError, self).__init__(reference)
        self.reference = reference


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
            yield part[1:]
        else:
            yield part


def strip_trailing_sep(path):
    if path and path[-1] in ("/", "\\"):
        return path[:-1]
    return path


def strip_leading_sep(path):
    if path and path[0] in ("/", "\\"):
        return path[1:]
    return path


def ensure_trailing_sep(path, sep=None):
    sep = sep or os.path.sep
    if path[-1:] != sep:
        path += sep
    return path


def subpath(path, start, sep=None):
    if path == start:
        raise ValueError(path, start)
    start_with_sep = ensure_trailing_sep(start, sep)
    if path.startswith(start_with_sep):
        return path[len(start_with_sep) :]
    raise ValueError(path, start)


def which(cmd):
    which_cmd = "where" if get_platform() == "Windows" else "which"
    devnull = open(os.devnull, "w")
    try:
        out = subprocess.check_output([which_cmd, cmd], stderr=devnull)
    except subprocess.CalledProcessError:
        return None
    else:
        assert out, cmd
        return out.decode("utf-8").split(os.linesep)[0]


def symlink(target, link):
    if get_platform() == "Windows":
        _windows_symlink(target, link)
    else:
        os.symlink(target, link)


def copyfile(src, dest):
    shutil.copyfile(src, dest)
    shutil.copymode(src, dest)


def _windows_symlink(target, link):
    if os.path.isdir(target):
        args = ["mklink", "/D", link, target]
    else:
        args = ["mklink", link, target]
    try:
        subprocess.check_output(args, shell=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        raise OSError(e.returncode, e.output.decode(errors="ignore").strip())


_text_ext = set(
    [
        ".csv",
        ".md",
        ".py",
        ".sh",
        ".txt",
    ]
)

_binary_ext = set(
    [
        ".ai",
        ".bmp",
        ".gif",
        ".ico",
        ".jpeg",
        ".jpg",
        ".png",
        ".ps",
        ".psd",
        ".svg",
        ".tif",
        ".tiff",
        ".aif",
        ".mid",
        ".midi",
        ".mpa",
        ".mp3",
        ".ogg",
        ".wav",
        ".wma",
        ".avi",
        ".mov",
        ".mp4",
        ".mpeg",
        ".swf" ".wmv",
        ".7z",
        ".deb",
        ".gz",
        ".pkg",
        ".rar",
        ".rpm",
        ".tar",
        ".xz",
        ".z",
        ".zip",
        ".doc",
        ".docx",
        ".key",
        ".pdf",
        ".ppt",
        ".pptx",
        ".xlr",
        ".xls",
        ".xlsx",
        ".bin",
        ".pickle",
        ".pkl",
        ".pyc",
    ]
)

_control_chars = b'\n\r\t\f\b'
if bytes is str:
    _printable_ascii = _control_chars + b"".join([chr(x) for x in range(32, 127)])
    _printable_high_ascii = b"".join([chr(x) for x in range(127, 256)])
else:
    _printable_ascii = _control_chars + bytes(range(32, 127))
    _printable_high_ascii = bytes(range(127, 256))


def is_text_file(path, ignore_ext=False):
    import chardet

    # Adapted from https://github.com/audreyr/binaryornot under the
    # BSD 3-clause License
    if not os.path.exists(path):
        raise OSError("%s does not exist" % path)
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
    likely_binary = (nontext_ratio1 > 0.3 and nontext_ratio2 < 0.05) or (
        nontext_ratio1 > 0.8 and nontext_ratio2 > 0.8
    )
    detected_encoding = chardet.detect(sample)
    decodable_as_unicode = False
    if (
        detected_encoding["confidence"] > 0.9
        and detected_encoding["encoding"] != "ascii"
    ):
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


def safe_is_text_file(path, ignore_ext=False):
    try:
        return is_text_file(path, ignore_ext)
    except OSError as e:
        log.warning("could not check for text file %s: %s", path, e)
        return False


def touch(filename):
    open(filename, "ab").close()
    now = time.time()
    os.utime(filename, (now, now))


def ensure_file(filename):
    if not os.path.exists(filename):
        touch(filename)


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


def safe_list_remove(x, l):
    safe_list_remove_all([x], l)


def safe_list_remove_all(xs, l):
    for x in xs:
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
    if start_time is None:
        return None
    if end_time is None:
        end_time = time.time() * 1000000
    seconds = (end_time - start_time) // 1000000
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return "%d:%02d:%02d" % (h, m, s)


def format_dir(dir):
    return format_user_dir(os.path.abspath(dir))


def format_user_dir(s):
    if get_platform() == "Windows":
        return s
    user_dir = os.path.expanduser("~")
    if s.startswith(user_dir):
        return os.path.join("~", s[len(user_dir) + 1 :])
    return s


def apply_env(target, source, names):
    for name in names:
        try:
            target[name] = source[name]
        except KeyError:
            pass


def safe_filename(s):
    if get_platform() == "Windows":
        s = re.sub(r"[:<>?]", "_", s)
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


def get_env(name, type, default=None):
    try:
        val = os.environ[name]
    except KeyError:
        return default
    else:
        try:
            return type(val)
        except Exception as e:
            log.warning("error converting env %s to %s: %s", name, type, e)
            return None


def del_env(names):
    for name in names:
        try:
            del os.environ[name]
        except KeyError:
            pass


def python_interpreters():
    import glob
    from guild import config

    bin_dir = os.path.dirname(config.python_exe())
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
    if not matching:
        return None
    matching_ver = matching[0]
    return python_interps[matching_ver], matching_ver


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
        seen_dirs.add(realpath(root))
        _del_excluded_select_copy_dirs(
            dirs, src_dir, root, seen_dirs, config, copy_filter
        )
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


def _del_excluded_select_copy_dirs(dirs, src_dir, root, seen_dirs, config, copy_filter):
    _del_seen_dirs(dirs, root, seen_dirs)
    _del_config_excluded_dirs(dirs, src_dir, root, config)
    if copy_filter:
        copy_filter.delete_excluded_dirs(root, dirs)


def _del_seen_dirs(dirs, root, seen):
    for dir_name in dirs:
        real_path = realpath(os.path.join(root, dir_name))
        if real_path in seen:
            dirs.remove(dir_name)


def _del_config_excluded_dirs(dirs, src_dir, root, config):
    for name in list(dirs):
        path = os.path.join(root, name)
        rel_path = os.path.relpath(path, src_dir)
        if not _select_to_copy(path, rel_path, config):
            dirs.remove(name)


def _select_to_copy(path, rel_path, config, copy_filter=None):
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
    return shlex.split(s, posix=True)


def shlex_quote(s):
    # If s can't be None in case where pipes.quote is used by six.
    s = s or ""
    return _simplify_shlex_quote(six.moves.shlex_quote(s))


def _simplify_shlex_quote(s):
    repls = [
        ("''\"'\"'", "\"'"),
    ]
    for pattern_start, repl_start in repls:
        if not s.startswith(pattern_start):
            continue
        pattern_end = "".join(reversed(pattern_start))
        if not s.endswith(pattern_end):
            continue
        repl_end = "".join(reversed(repl_start))
        stripped = s[len(pattern_start) : -len(pattern_end)]
        return repl_start + stripped + repl_end
    return s


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

    _cwd = None

    def __init__(self, path):
        self.path = path

    def __enter__(self):
        self._cwd = os.getcwd()
        os.chdir(self.path)

    def __exit__(self, *exc):
        assert self._cwd is not None
        os.chdir(self._cwd)


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
        return "%s %s %s %s" % (self.f.__module__, self.f.__name__, self.args, self.kw)


def dir_size(dir):
    size = 0
    for root, dirs, names in os.walk(dir):
        for name in dirs + names:
            size += os.path.getsize(os.path.join(root, name))
    return size


def platform_info():
    """Returns a dict of system info."""
    info = _platform_base_info()
    info.update(_platform_psutil_info())
    return info


def _platform_base_info():
    import platform

    return {
        "architecture": " ".join(platform.architecture()),
        "processor": platform.processor(),
        "python_version": sys.version.replace("\n", ""),
        "uname": " ".join(platform.uname()),
    }


def _platform_psutil_info():
    try:
        import psutil
    except ImportError:
        return {}
    else:
        return {
            "cpus": psutil.cpu_count(),
        }


def guild_user_agent():
    import platform
    import guild

    system, _node, release, _ver, machine, _proc = platform.uname()
    return "python-guildai/%s (%s; %s; %s)" % (
        guild.__version__,
        system,
        machine,
        release,
    )


def nested_config(kv, nested=None):
    nested = nested or {}
    for name, val in sorted(kv.items()):
        _apply_nested(name, val, nested)
    return nested


def _apply_nested(name, val, nested):
    parts = name.split(".")
    cur = nested
    for i in range(0, len(parts) - 1):
        cur = cur.setdefault(parts[i], {})
        if not isinstance(cur, dict):
            conflicts_with = ".".join(parts[0 : i + 1])
            raise ValueError(
                "%r cannot be nested: conflicts with {%r: %s}"
                % (name, conflicts_with, cur)
            )
    cur[parts[-1]] = val


def encode_cfg(data):
    import io
    import configparser

    cfg = configparser.ConfigParser()
    io = io.StringIO()
    for key, val in sorted(data.items()):
        if isinstance(val, dict):
            cfg.add_section(key)
            for option, option_val in sorted(val.items()):
                cfg.set(key, option, str(option_val))
        else:
            cfg.set("DEFAULT", key, str(val))
    cfg.write(io)
    return io.getvalue()


def _split_cfg_key(key):
    parts = key.split(".", 1)
    if len(parts) == 2:
        return parts
    return "DEFAULT", parts[0]


def short_digest(s):
    if not s:
        return ""
    return s[:8]


def safe_listdir(path):
    try:
        return os.listdir(path)
    except OSError:
        return []


def compare_paths(p1, p2):
    return _resolve_path(p1) == _resolve_path(p2)


def _resolve_path(p):
    return realpath(os.path.abspath(os.path.expanduser(p)))


def shorten_path(path, max_len=28, ellipsis=u"\u2026", sep=os.path.sep):
    if len(path) <= max_len:
        return path
    parts = _shorten_path_split_path(path, sep)
    if len(parts) == 1:
        return parts[0]
    assert all(parts), parts
    r = [parts.pop()]  # Always include rightmost part
    if parts[0][0] == sep:
        l = []
        pop_r = False
    else:
        # Relative path, always include leftmost part
        l = [parts.pop(0)]
        pop_r = True
    while parts:
        len_l = sum([len(s) + 1 for s in l])
        len_r = sum([len(s) + 1 for s in r])
        part = parts.pop() if pop_r else parts.pop(0)
        side = r if pop_r else l
        if len_l + len_r + len(part) + len(ellipsis) >= max_len:
            break
        side.append(part)
        pop_r = not pop_r
    shortened = os.path.sep.join(
        [os.path.sep.join(l), ellipsis, os.path.sep.join(reversed(r))]
    )
    if len(shortened) >= len(path):
        return path
    return shortened


def _shorten_path_split_path(path, sep):
    """Splits path into parts.

    Leading and repeated '/' chars are prepended to the
    part. E.g. "/foo/bar" is returned as ["/foo", "bar"] and
    "foo//bar" as ["foo", "/bar"].
    """
    if not path:
        return []
    parts = path.split(sep)
    packed = []
    blanks = []
    for part in parts:
        if part == "":
            blanks.append("")
        else:
            packed.append(sep.join(blanks + [part]))
            blanks = []
    if len(blanks) > 1:
        packed.append(sep.join(blanks))
    return packed


class HTTPResponse(object):
    def __init__(self, resp):
        self.status_code = resp.status
        self.text = resp.read()


class HTTPConnectionError(Exception):
    pass


def http_post(url, data, timeout=None):
    headers = {
        "User-Agent": guild_user_agent(),
        "Content-type": "application/x-www-form-urlencoded",
    }
    return _http_request(url, headers, data, "POST", timeout)


def http_get(url, timeout=None):
    return _http_request(url, timeout=timeout)


def _http_request(url, headers=None, data=None, method="GET", timeout=None):
    import socket
    from six.moves import urllib

    headers = headers or {}
    url_parts = urllib.parse.urlparse(url)
    conn = _HTTPConnection(url_parts.scheme, url_parts.netloc, timeout)
    params = urllib.parse.urlencode(data) if data else ""
    try:
        conn.request(method, url_parts.path, params, headers)
    except socket.error as e:
        if e.errno == errno.ECONNREFUSED:
            raise HTTPConnectionError(url)
        raise
    else:
        return HTTPResponse(conn.getresponse())


def _HTTPConnection(scheme, netloc, timeout):
    from six.moves import http_client

    if scheme == "http":
        return http_client.HTTPConnection(netloc, timeout=timeout)
    elif scheme == "https":
        return http_client.HTTPSConnection(netloc, timeout=timeout)
    else:
        raise ValueError("unsupported scheme '%s' - must be 'http' or 'https'" % scheme)


class StdIOContextManager(object):
    def __init__(self, stream):
        self.stream = stream

    def __enter__(self):
        return self.stream

    def __exit__(self, *_exc):
        pass


def check_env(env):
    for name, val in env.items():
        if not isinstance(name, six.string_types):
            raise ValueError("non-string env name %r" % name)
        if not isinstance(val, six.string_types):
            raise ValueError("non-string env value for '%s': %r" % (name, val))


class SysArgv(object):
    def __init__(self, args):
        self._args = args
        self._save = None

    def __enter__(self):
        assert self._save is None, self._save
        self._save = sys.argv[1:]
        sys.argv[1:] = self._args

    def __exit__(self, *_exc):
        assert self._save is not None
        sys.argv[1:] = self._save
        self._save = None


class Env(object):
    def __init__(self, vals, replace=False):
        self._vals = vals
        self._replace = replace
        self._revert_ops = []
        self._save_env = None

    def __enter__(self):
        if self._replace:
            self._replace_env()
        else:
            self._merge_env()

    def _replace_env(self):
        self._save_env = dict(os.environ)
        os.environ.clear()
        os.environ.update(self._vals)

    def _merge_env(self):
        env = os.environ
        for name, val in self._vals.items():
            try:
                cur = env.pop(name)
            except KeyError:
                self._revert_ops.append(self._del_env_fun(name, env))
            else:
                self._revert_ops.append(self._set_env_fun(name, cur, env))
            env[name] = val

    @staticmethod
    def _del_env_fun(name, env):
        def f():
            try:
                del env[name]
            except KeyError:
                pass

        return f

    @staticmethod
    def _set_env_fun(name, val, env):
        def f():
            env[name] = val

        return f

    def __exit__(self, *exc):
        if self._replace:
            self._restore_env()
        else:
            self._unmerge_env()

    def _restore_env(self):
        assert self._save_env is not None
        os.environ.clear()
        os.environ.update(self._save_env)

    def _unmerge_env(self):
        for op in self._revert_ops:
            op()


class StdinReader(object):
    def __init__(self, stop_on_blank_line=False):
        self.stop_on_blank_line = stop_on_blank_line

    __enter__ = lambda self, *_args: self
    __exit__ = lambda *_args: None

    def __iter__(self):
        for line in sys.stdin:
            line = line.rstrip()
            if not line and self.stop_on_blank_line:
                break
            yield line


def env_var_name(s):
    return re.sub("[^A-Z0-9_]", "_", s.upper())


def env_var_quote(s):
    if s == "":
        return ""
    return shlex_quote(s)


def realpath(path):
    # Workaround for https://bugs.python.org/issue9949
    try:
        link = os.readlink(path)
    except OSError:
        return os.path.realpath(path)
    else:
        path_dir = os.path.dirname(path)
        return os.path.abspath(os.path.join(path_dir, _strip_windows_prefix(link)))


def _strip_windows_prefix(path):
    if get_platform() != "Windows":
        return path
    if path.startswith("\\\\?\\"):
        return path[4:]
    return path


def norm_path_sep(path):
    return path.replace(os.path.sep, "/")


def bind_method(obj, method_name, function):
    setattr(obj, method_name, function.__get__(obj, obj.__class__))


def edit(s, extension=".txt", strip_comment_lines=False):
    import click

    try:
        edited = click.edit(s, _try_editor(), extension=extension)
    except click.UsageError as e:
        raise ValueError(e)
    else:
        if edited is None:
            edited = s
        if strip_comment_lines:
            edited = _strip_comment_lines(edited)
        return edited


def _try_editor():
    return find_apply([_try_editor_env, _try_editor_bin])


def _try_editor_env():
    names = ("VISUAL", "EDITOR")
    for name in names:
        val = os.getenv(name)
        if val:
            return val
    return None


def _try_editor_bin():
    """Returns /usr/bin/editor if it exists.

    This is the path configured by `update-alternatives` on Ubuntu
    systems.
    """
    editor_bin = "/usr/bin/editor"
    if os.path.exists(editor_bin):
        return editor_bin
    return None


def _strip_comment_lines(s):
    return "\n".join([line for line in s.split("\n") if line.rstrip()[:1] != "#"])


def test_windows_symlinks():
    if get_platform() != "Windows":
        return
    with TempDir() as tmp:
        os.symlink(tempfile.gettempdir(), os.path.join(tmp.path, "link"))


def raise_from(raise_exc, from_exc):
    # pylint: disable=unused-variable,unused-argument
    if six.PY3:
        exec("raise raise_exc from from_exc")
    else:
        raise_exc_type = raise_exc.__class__
        tb = sys.exc_info()[2]
        exec("raise raise_exc_type, raise_exc, tb")


class PropertyCache(object):
    def __init__(self, properties):
        self._vals = {
            name: default for name, default, _callback, _timeout in properties
        }
        self._expirations = {
            name: 0 for name, _default, _callback, _timeout in properties
        }
        self._timeouts = {
            name: timeout for name, _default, _callback, timeout in properties
        }
        self._callbacks = {
            name: callback for name, _default, callback, _timeout in properties
        }

    def get(self, name, *args, **kw):
        if time.time() < self._expirations[name]:
            return self._vals[name]
        val = self._callbacks[name](*args, **kw)
        self._vals[name] = val
        self._expirations[name] = time.time() + self._timeouts[name]
        return val


def get_platform():
    import platform  # expensive

    return platform.system()


def make_executable(path):
    import stat

    os.chmod(path, os.stat(path).st_mode | stat.S_IEXEC)
