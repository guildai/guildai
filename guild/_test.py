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

"""Internal test support.

Notes on improving the pattern matching:

- `...` should only match for one line, if it is not on its own
  line. It's all too common to have `...` match unexpected content
  spanning multiple lines.

- If `...` is on its own line, it should match multiple lines.

- Matching support support variables along these lines:

    >> foo = 123
    >> print(foo)
    {{foo}}

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import codecs
import doctest
import fnmatch
import glob
import errno
import json
import os
import platform
import pprint
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time

import six

import guild

from guild import _api as gapi
from guild import cli
from guild import config as configlib
from guild import file_util
from guild import guildfile
from guild import init
from guild import op_util
from guild import run as runlib
from guild import util

PLATFORM = platform.system()

TEST_NAME_WIDTH = 27

NORMALIZE_PATHS = doctest.register_optionflag("NORMALIZE_PATHS")
STRIP_U = doctest.register_optionflag("STRIP_U")
STRIP_L = doctest.register_optionflag("STRIP_L")
WINDOWS = doctest.register_optionflag("WINDOWS")
WINDOWS_ONLY = doctest.register_optionflag("WINDOWS_ONLY")
STRIP_ANSI_FMT = doctest.register_optionflag("STRIP_ANSI_FMT")
PY2 = doctest.register_optionflag("PY2")
PY3 = doctest.register_optionflag("PY3")
PY27 = doctest.register_optionflag("PY27")
PY35 = doctest.register_optionflag("PY35")
PY36 = doctest.register_optionflag("PY36")
PY37 = doctest.register_optionflag("PY37")
PY38 = doctest.register_optionflag("PY38")
ANNOTATIONS = doctest.register_optionflag("ANNOTATIONS")

_ansi_p = re.compile(r"\033\[[;?0-9]*[a-zA-Z]")


def run_all(skip=None):
    return run(all_tests(), skip)


def all_tests():
    test_pattern = os.path.join(tests_dir(), "*.md")
    return sorted([_test_name_for_path(path) for path in glob.glob(test_pattern)])


def tests_dir():
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), "tests")


def _test_name_for_path(path):
    name, _ = os.path.splitext(os.path.basename(path))
    return name


def run(tests, skip=None):
    skip = skip or []
    sys.stdout.write("internal tests:\n")
    success = True
    for test in tests:
        if test not in skip:
            run_success = _run_test(test)
            success = success and run_success
        else:
            sys.stdout.write(
                "  %s:%s skipped\n" % (test, " " * (TEST_NAME_WIDTH - len(test)))
            )
    return success


def _run_test(name):
    sys.stdout.write("  %s: " % name)
    sys.stdout.flush()
    filename = _filename_for_test(name)
    if _skip_windows_test(filename):
        _log_skipped_windows_test(name)
        return True
    try:
        failures, _tests = run_test_file(filename)
    except IOError:
        _log_test_not_found(name)
        return False
    else:
        if not failures:
            _log_test_ok(name)
        return failures == 0


def _filename_for_test(name_or_path):
    if os.path.sep in name_or_path or "." in name_or_path:
        return os.path.abspath(name_or_path)
    else:
        return _named_test_filename(name_or_path)


def _named_test_filename(name):
    return _resolve_relative_test_filename(os.path.join("tests", name + ".md"))


def _resolve_relative_test_filename(filename):
    if os.path.isabs(filename):
        return filename
    package = doctest._normalize_module(None, 3)
    return doctest._module_relative_path(package, filename)


def _skip_windows_test(filename):
    if PLATFORM != "Windows":
        return False
    full_filename = os.path.join(os.path.dirname(__file__), filename)
    try:
        with open(full_filename, "r") as f:
            head = f.read(256)
    except IOError:
        return False
    else:
        return re.search(r"^skip-windows: *yes$", head, re.MULTILINE)


def _log_skipped_windows_test(name):
    sys.stdout.write(" " * (TEST_NAME_WIDTH - len(name)))
    sys.stdout.write("ok (skipped test on Windows)\n")
    sys.stdout.flush()


def _log_test_not_found(name):
    sys.stdout.write("%sTEST NOT FOUND\n" % (" " * (TEST_NAME_WIDTH - len(name))))


def _log_test_ok(name):
    sys.stdout.write(" " * (TEST_NAME_WIDTH - len(name)))
    sys.stdout.write("ok\n")
    sys.stdout.flush()


def run_test_file(filename, globs=None):
    filename = _resolve_relative_test_filename(filename)
    globs = globs or test_globals()
    return run_test_file_with_config(
        filename,
        globs=globs,
        optionflags=(
            _report_first_flag()
            | doctest.ELLIPSIS
            | doctest.NORMALIZE_WHITESPACE
            | NORMALIZE_PATHS
            | WINDOWS
            | STRIP_U
            | STRIP_L
            | STRIP_ANSI_FMT
            | PY2
            | PY3
            | ANNOTATIONS
        ),
    )


def _report_first_flag():
    if os.getenv("REPORT_ONLY_FIRST_FAILURE") == "1":
        return doctest.REPORT_ONLY_FIRST_FAILURE
    return 0


class Py23DocChecker(doctest.OutputChecker):
    """Output checker that works around Python 2/3 unicode representations.

    https://dirkjan.ochtman.nl/writing/2014/07/06/single-source-python-23-doctests.html
    """

    def check_output(self, want, got, optionflags):
        got = self._got(got, optionflags)
        want = self._want(want, optionflags)
        return doctest.OutputChecker.check_output(self, want, got, optionflags)

    def _got(self, got, optionflags):
        if sys.version_info[0] < 3:
            got = self._py2_got(got, optionflags)
        if PLATFORM == "Windows":
            got = self._windows_got(got, optionflags)
        return got

    def _py2_got(self, got, optionflags):
        if optionflags & STRIP_U:
            got = self._strip_u(got)
        if optionflags & STRIP_L:
            got = self._strip_L(got)
        if optionflags & STRIP_ANSI_FMT:
            got = self._strip_ansi_fmt(got)
        return got

    @staticmethod
    def _strip_u(got):
        # Strip unicode prefix
        got = re.sub(r"([\W])u'(.*?)'", "\\1'\\2'", got)
        got = re.sub(r'([\W])u"(.*?)"', '\\1"\\2"', got)
        got = re.sub(r"^u'(.*?)'", "'\\1'", got)
        got = re.sub(r'^u"(.*?)"', '"\\1"', got)
        return got

    @staticmethod
    def _strip_L(got):
        # Normalize long integers
        return re.sub(r"([0-9]+)L", "\\1", got)

    @staticmethod
    def _strip_ansi_fmt(got):
        return _ansi_p.sub("", got)

    @staticmethod
    def _windows_got(got, optionflags):
        if optionflags & NORMALIZE_PATHS:
            # Convert Windows paths to UNIXy paths
            got = re.sub(r"[c-zC-Z]:\\\\?|\\\\?", "/", got)
        return got

    def _want(self, want, optionflags):
        want = self._leading_wildcard_want(want)
        if optionflags & ANNOTATIONS:
            want = self._annotations_want(want)
        return want

    @staticmethod
    def _leading_wildcard_want(want):
        # Treat leading '???' like '...' (work around for '...' as
        # code continuation token in doctest.
        return re.sub(r"^\?\?\?", "...", want)

    @staticmethod
    def _annotations_want(want):
        return want.replace(":<pathsep>", os.path.pathsep)


class TestRunner(doctest.DocTestRunner, object):
    def __init__(self, checker=None, verbose=None, optionflags=0):
        super(TestRunner, self).__init__(checker, verbose, optionflags)
        self.skipped = 0

    def run(self, test, compileflags=None, out=None, clear_globs=True):
        self._apply_skip(test)
        super(TestRunner, self).run(test, compileflags, out, clear_globs)

    @staticmethod
    def _apply_skip(test):
        SKIP = doctest.SKIP
        is_windows = PLATFORM == "Windows"
        py_major_ver = sys.version_info[0]
        py_minor_ver = sys.version_info[1]
        for example in test.examples:
            if example.options.get(WINDOWS) is False and is_windows:
                example.options[SKIP] = True
            if example.options.get(WINDOWS_ONLY) is True and not is_windows:
                example.options[SKIP] = True
            # PY2 and PY3 are enabled by default - check if explicitly disabled.
            if example.options.get(PY2) is False and py_major_ver == 2:
                example.options[SKIP] = True
            if example.options.get(PY3) is False and py_major_ver == 3:
                example.options[SKIP] = True
            # Force tests on/off if more specific Python versions specified.
            for opt, maj_ver, min_ver in [
                (example.options.get(PY27), 2, 7),
                (example.options.get(PY35), 3, 5),
                (example.options.get(PY36), 3, 6),
                (example.options.get(PY37), 3, 7),
                (example.options.get(PY38), 3, 8),
            ]:
                if (
                    opt in (True, False)
                    and py_major_ver == maj_ver
                    and py_minor_ver == min_ver
                ):
                    example.options[SKIP] = not opt


def run_test_file_with_config(filename, globs, optionflags):
    test_dir = os.path.dirname(filename)
    with _safe_chdir(test_dir):
        return _run_test_file_with_config(filename, globs, optionflags)


def _safe_chdir(dir):
    if not os.path.exists(dir):

        class NoOp(object):
            def __enter__(self):
                pass

            def __exit__(self, *_args):
                pass

        return NoOp()

    return util.Chdir(dir)


def _run_test_file_with_config(filename, globs, optionflags):
    """Modified from doctest.py to use custom checker."""
    text, filename = _load_testfile(filename)
    name = os.path.basename(filename)
    if globs is None:
        globs = {}
    else:
        globs = globs.copy()
    if '__name__' not in globs:
        globs['__name__'] = '__main__'
    checker = Py23DocChecker()
    runner = TestRunner(checker=checker, verbose=None, optionflags=optionflags)
    parser = doctest.DocTestParser()
    test = parser.get_doctest(text, globs, name, filename, 0)
    flags = (
        print_function.compiler_flag
        | absolute_import.compiler_flag
        | division.compiler_flag
    )
    runner.run(test, flags)
    results = runner.summarize()
    if doctest.master is None:
        doctest.master = runner
    else:
        doctest.master.merge(runner)
    return results


def _load_testfile(filename):
    # Copied from Python 3.6 doctest._load_testfile to ensure utf-8
    # encoding on Python 2.
    package = doctest._normalize_module(None, 3)
    if getattr(package, '__loader__', None) is not None:
        if hasattr(package.__loader__, 'get_data'):
            file_contents = package.__loader__.get_data(filename)
            file_contents = file_contents.decode("utf-8")
            # get_data() opens files as 'rb', so one must do the equivalent
            # conversion as universal newlines would do.
            return file_contents.replace(os.linesep, '\n'), filename
    with codecs.open(filename, encoding="utf-8") as f:
        return f.read(), filename


def test_globals():
    return {
        "PLATFORM": PLATFORM,
        "Chdir": util.Chdir,
        "Env": util.Env,
        "LogCapture": util.LogCapture,
        "ModelPath": ModelPath,
        "PrintStderr": PrintStderr,
        "Project": Project,
        "Proxy": Proxy,
        "RunError": gapi.RunError,
        "SetCwd": configlib.SetCwd,
        "SetGuildHome": configlib.SetGuildHome,
        "StderrCapture": StderrCapture,
        "SysPath": SysPath,
        "TempFile": util.TempFile,
        "UserConfig": UserConfig,
        "abspath": os.path.abspath,
        "basename": os.path.basename,
        "cat": cat,
        "cat_json": cat_json,
        "cli": cli,
        "compare_paths": util.compare_paths,
        "copyfile": copyfile,
        "copytree": util.copytree,
        "cd": _chdir,
        "cwd": os.getcwd,
        "dir": dir,
        "dirname": os.path.dirname,
        "ensure_dir": util.ensure_dir,
        "exists": os.path.exists,
        "find": find,
        "findl": file_util.find,
        "gapi": gapi,
        "guild": guild,
        "guildfile": guildfile,
        "isdir": os.path.isdir,
        "isfile": os.path.isfile,
        "islink": os.path.islink,
        "join_path": os.path.join,
        "json": json,
        "mkdir": os.mkdir,
        "mkdtemp": mkdtemp,
        "mktemp_guild_dir": mktemp_guild_dir,
        "normlf": _normlf,
        "not_used": object(),  # an uncooperative value
        "os": os,
        "path": os.path.join,
        "pprint": pprint.pprint,
        "quiet": lambda cmd, **kw: _run(cmd, quiet=True, **kw),
        "re": re,
        "realpath": util.realpath,
        "relpath": os.path.relpath,
        "rm": os.remove,
        "rmdir": util.safe_rmtree,
        "run": _run,
        "run_capture": _run_capture,
        "sample": sample,
        "samples_dir": samples_dir,
        "sha256": util.file_sha256,
        "sleep": time.sleep,
        "symlink": os.symlink,
        "sys": sys,
        "tests_dir": tests_dir,
        "touch": util.touch,
        "which": util.which,
        "write": write,
    }


def sample(*parts):
    return os.path.join(*(samples_dir(),) + parts)


def samples_dir():
    return os.path.join(tests_dir(), "samples")


def mkdtemp(prefix="guild-test-"):
    return tempfile.mkdtemp(prefix=prefix)


def mktemp_guild_dir():
    guild_dir = mkdtemp()
    init.init_guild_dir(guild_dir)
    return guild_dir


def find(root, followlinks=False, includedirs=False, ignore=None):
    paths = file_util.find(root, followlinks, includedirs)
    if ignore:
        paths = _filter_ignored(paths, ignore)
    _sort_normalized_paths(paths)
    if not paths:
        print("<empty>")
    else:
        for path in paths:
            print(path)


def _sort_normalized_paths(paths):
    key = lambda p: p.replace(os.path.sep, "/")
    paths.sort(key=key)


def _filter_ignored(paths, ignore):
    if isinstance(ignore, six.string_types):
        ignore = [ignore]
    return [
        p for p in paths if not any((fnmatch.fnmatch(p, pattern) for pattern in ignore))
    ]


def cat(*parts):
    with open(os.path.join(*parts), "r") as f:
        s = f.read()
        if not s:
            print("<empty>")
        else:
            print(s)


def cat_json(*parts):
    with open(os.path.join(*parts), "r") as f:
        data = json.load(f)
        json.dump(data, sys.stdout, sort_keys=True, indent=4, separators=(",", ": "))


def dir(path=".", ignore=None):
    return sorted(
        [
            name
            for name in os.listdir(path)
            if ignore is None or not any((fnmatch.fnmatch(name, p) for p in ignore))
        ]
    )


def copyfile(*args, **kw):
    # No return value here to normalize differenced between python2
    # and python3.
    shutil.copy2(*args, **kw)


class StderrCapture(object):

    closed = False
    _stderr = None
    _captured = []

    def __init__(self, autoprint=False):
        self._autoprint = autoprint

    def __enter__(self):
        self._stderr = sys.stderr
        self._captured = []
        self.closed = False
        sys.stderr = self
        return self

    def __exit__(self, *exc):
        assert self._stderr is not None
        sys.stderr = self._stderr
        self.closed = True

    def write(self, b):
        self._captured.append(b)
        if self._autoprint:
            sys.stdout.write(b.decode("utf-8"))
            sys.stdout.flush()

    def flush(self):
        pass

    def print(self):
        for part in self._captured:
            sys.stdout.write(part.decode("utf-8"))
        sys.stdout.flush()


def PrintStderr():
    return StderrCapture(autoprint=True)


def write(filename, contents):
    try:
        contents = contents.encode()
    except AttributeError:
        pass
    with open(filename, "wb") as f:
        f.write(contents)


class SysPath(object):

    _sys_path0 = None

    def __init__(self, path=None, prepend=None, append=None):
        path = path if path is not None else sys.path
        if prepend:
            path = prepend + path
        if append:
            path = path + append
        self.sys_path = path

    def __enter__(self):
        self._sys_path0 = sys.path
        sys.path = self.sys_path

    def __exit__(self, *exc):
        assert self._sys_path0 is not None
        sys.path = self._sys_path0


class ModelPath(object):

    _model_path0 = None

    def __init__(self, path):
        self.model_path = path

    def __enter__(self):
        from guild import model

        self._model_path0 = model.get_path()
        model.set_path(self.model_path)

    def __exit__(self, *exc):
        from guild import model

        assert self._model_path0 is not None
        model.set_path(self._model_path0)


class Project(object):
    def __init__(self, cwd, guild_home=None, env=None):
        from guild import index as indexlib  # expensive

        self.cwd = cwd
        self.guild_home = guild_home or mkdtemp()
        self._env = env
        runs_cache_path = os.path.join(self.guild_home, "cache", "runs")
        self.index = indexlib.RunIndex(runs_cache_path)

    def run_capture(self, *args, **kw):
        """Runs an operation returning a tuple of run and output."""
        run_dir = self._run_dir_apply(kw)
        out = self._run(*args, **kw)
        return runlib.for_dir(run_dir), out

    def _run_dir_apply(self, kw):
        """Returns a run directory for kw, optionally apply it to kw.

        If kw contains an explicit run directory, returns
        it. Otherwise checks if kw is a restart/proto and if so
        returns the run directory associated with the specified
        restart/proto. If it's a normal run, creates a new run ID and
        applies it to kw.

        This scheme is used so that we know the run directory prior to
        running an operation. This lets us return a corresponding run
        object after the operation is finished.
        """
        return util.find_apply(
            [
                lambda: kw.get("run_dir"),
                lambda: self._restart_proto_run_dir(kw),
                lambda: self._init_run_dir_apply(kw),
            ]
        )

    def _restart_proto_run_dir(self, kw):
        """Return the run dir for a restart or proto kw if specified.

        If kw contains either restart or proto spec, performs a lookup
        within the project Guild home for a single matching run and
        returns its directory. Otherwise, returns None.

        This is used to identify the run directory prior to passing
        rerunning/restarting it.
        """
        for name in ("restart", "start", "proto"):
            spec = kw.get(name)
            if not spec:
                continue
            from guild import run_util
            from guild.commands import run_impl

            with configlib.SetGuildHome(self.guild_home):
                run = util.find_apply(
                    [run_util.marked_or_latest_run_for_opspec, run_impl.one_run], spec
                )
                return run.dir
        return None

    def _init_run_dir_apply(self, kw):
        run_id = runlib.mkid()
        run_dir = os.path.join(self.guild_home, "runs", run_id)
        kw["run_dir"] = run_dir
        return run_dir

    def _run(self, *args, **kw):
        ignore_output = kw.pop("ignore_output", False)
        cwd = os.path.join(self.cwd, kw.pop("cwd", "."))
        with self._run_env():
            out = gapi.run_capture_output(
                guild_home=self.guild_home, cwd=cwd, *args, **kw
            )
        if ignore_output:
            out = self._filter_output(out, ignore_output)
        return out.strip()

    def _run_env(self):
        env = {"NO_WARN_RUNDIR": "1"}
        if self._env:
            env.update(self._env)
        return util.Env(env)

    def run(self, *args, **kw):
        try:
            _run, out = self.run_capture(*args, **kw)
        except gapi.RunError as e:
            print("{}\n<exit {}>".format(e.output.strip(), e.returncode))
        else:
            print(out)

    def run_quiet(self, *args, **kw):
        cwd = os.path.join(self.cwd, kw.pop("cwd", "."))
        with self._run_env():
            gapi.run_quiet(guild_home=self.guild_home, cwd=cwd, *args, **kw)

    @staticmethod
    def _filter_output(out, ignore):
        if isinstance(ignore, six.string_types):
            ignore = [ignore]
        return "\n".join(
            [
                line
                for line in out.split("\n")
                if all(s and s not in line for s in ignore)
            ]
        )

    def list_runs(self, **kw):
        return gapi.runs_list(cwd=self.cwd, guild_home=self.guild_home, **kw)

    def print_runs(
        self,
        runs=None,
        ids=False,
        flags=False,
        labels=False,
        status=False,
        cwd=None,
        limit=None,
    ):
        cwd = os.path.join(self.cwd, cwd) if cwd else self.cwd
        if runs is None:
            runs = self.list_runs(limit=limit)
        cols = self._cols_for_print_runs(ids, flags, labels, status)
        rows = []
        with util.Chdir(cwd):
            for run in runs:
                rows.append(self._row_for_print_run(run, ids, flags, labels, status))
        cli.table(rows, cols)

    @staticmethod
    def _cols_for_print_runs(ids, flags, labels, status):
        cols = ["opspec"]
        if ids:
            cols.append("id")
        if flags:
            cols.append("flags")
        if labels:
            cols.append("label")
        if status:
            cols.append("status")
        return cols

    @staticmethod
    def _row_for_print_run(run, ids, flags, labels, status):
        from guild.commands import runs_impl

        fmt_run = runs_impl.format_run(run)
        row = {"opspec": fmt_run["op_desc"]}
        if ids:
            row["id"] = run.id
        if flags:
            flag_vals = run.get("flags") or {}
            row["flags"] = op_util.flags_desc(flag_vals, delim=" ")
        if labels:
            row["label"] = run.get("label", "")
        if status:
            row["status"] = run.status
        return row

    def delete_runs(self, runs=None, **kw):
        with PrintStderr():
            gapi.runs_delete(runs, guild_home=self.guild_home, **kw)

    def print_trials(self, *args, **kw):
        print(self._run(print_trials=True, *args, **kw))

    def ls(self, run=None, all=False, sourcecode=False, ignore_compiled_source=False):
        # TODO: remove ignore_compiled_source for op2 promo
        if not run:
            runs = self.list_runs()
            if not runs:
                raise RuntimeError("no runs")
            run = runs[0]

        def filter(path):
            default_select = (
                all
                or not path.startswith(".guild")
                or (sourcecode and _is_run_sourcecode(path))
            )
            return default_select and not (
                ignore_compiled_source and _is_compiled_source(path)
            )

        return [path for path in file_util.find(run.path) if filter(path)]

    @staticmethod
    def cat(run, path):
        cat(os.path.join(run.path, path))

    def mark(self, runs, **kw):
        with PrintStderr():
            gapi.mark(runs, cwd=self.cwd, guild_home=self.guild_home, **kw)

    def scalars(self, run):
        self.index.refresh([run], ["scalar"])
        return self.index.run_scalars(run)

    def scalar(self, run, prefix, tag, qual, step):
        self.index.refresh([run], ["scalar"])
        return self.index.run_scalar(run, prefix, tag, qual, step)

    def compare(self, runs=None, **kw):
        return gapi.compare(runs=runs, cwd=self.cwd, guild_home=self.guild_home, **kw)

    def publish(self, runs=None, **kw):
        with PrintStderr():
            gapi.publish(runs=runs, cwd=self.cwd, guild_home=self.guild_home, **kw)

    def package(self, **kw):
        with PrintStderr():
            gapi.package(cwd=self.cwd, guild_home=self.guild_home, **kw)

    def label(self, runs=None, **kw):
        with PrintStderr():
            gapi.runs_label(runs, cwd=self.cwd, guild_home=self.guild_home, **kw)

    def tag(self, runs=None, **kw):
        with PrintStderr():
            gapi.runs_tag(runs, cwd=self.cwd, guild_home=self.guild_home, **kw)

    def select(self, run=None, **kw):
        return gapi.select(run, cwd=self.cwd, guild_home=self.guild_home, **kw)


def _is_run_sourcecode(path):
    return path.startswith(os.path.join(".guild", "sourcecode"))


def _is_compiled_source(path):
    return _is_run_sourcecode(path) and path.endswith(".pyc")


class _MockConfig(object):
    def __init__(self, data):
        self.path = configlib.user_config_path()
        self.data = data

    def read(self):
        return self.data


class UserConfig(object):
    def __init__(self, config):
        self._config = _MockConfig(config)

    def __enter__(self):
        configlib._user_config = self._config

    def __exit__(self, *exc):
        # None forces a lazy re-reread from disk, which is the correct
        # behavior for a reset here.
        configlib._user_config = None


class Proxy(object):
    """Empty object for use as proxy."""


def _patch_py3_exception_detail():
    import traceback

    format_exception_only = traceback.format_exception_only

    def patch(*args):
        formatted = format_exception_only(*args)
        formatted[-1] = _strip_error_module(formatted[-1])
        return formatted

    traceback.format_exception_only = patch


if sys.version_info[0] > 2:
    _patch_py3_exception_detail()


def _strip_error_module(last_line):
    m = re.match(r"([\w\.]+): (.+)", last_line)
    if not m:
        return _strip_class_module(last_line)
    else:
        return "{}: {}".format(_strip_class_module(m.group(1)), m.group(2))


def _strip_class_module(class_name):
    return class_name[class_name.rfind(".") + 1 :]


def _normlf(s):
    return s.replace("\r", "")


def _run_capture(*args, **kw):
    return _run(*args, _capture=True, **kw)


def _run(
    cmd,
    quiet=False,
    ignore=None,
    timeout=60,
    cut=None,
    guild_home=None,
    cwd=None,
    env=None,
    _capture=False,
):
    cmd = _run_shell_cmd(cmd)
    proc_env = dict(os.environ)
    if env:
        proc_env.update(env)
    proc_env["SYNC_RUN_OUTPUT"] = "1"
    if guild_home:
        proc_env["GUILD_HOME"] = guild_home
    p = _popen(cmd, proc_env, cwd)
    with _kill_after(p, timeout):
        out, err = p.communicate()
        assert err is None, err
        exit_code = p.returncode
    if _capture or not quiet or exit_code != 0:
        out = out.strip().decode("utf-8")
        if ignore:
            out = _strip_lines(out, ignore)
        if cut:
            out = _cut_cols(out, cut)
        if _capture:
            return out, exit_code
        print(out)
        print("<exit %i>" % exit_code)


def _run_shell_cmd(cmd):
    if util.get_platform() == "Windows":
        return _run_shell_win_cmd(cmd)
    else:
        return _run_shell_posix_cmd(cmd)


def _run_shell_win_cmd(cmd):
    cmd_norm_paths = cmd.replace(os.path.sep, "/")
    parts = util.shlex_split(cmd_norm_paths)
    _apply_guild_cmd_for_win(parts)
    return parts


def _apply_guild_cmd_for_win(parts):
    if parts and parts[0] == "guild":
        parts[0] = _guild_exe_for_win()


def _guild_exe_for_win():
    return util.find_apply(
        [
            _sys_arg_guild_exe_for_win,
            _which_guild_exe_for_win,
            _guild_exe_for_win_error,
        ]
    )


def _sys_arg_guild_exe_for_win():
    arg0 = sys.argv[0]
    arg0_basename = os.path.basename(arg0)
    if arg0_basename in ("guild.cmd", "guild.exe"):
        return arg0
    if arg0_basename == "guild":
        arg0_dir = os.path.dirname(arg0)
        return util.find_apply(
            [
                lambda: _test_exe_path(os.path.join(arg0_dir, "guild.exe")),
                lambda: _test_exe_path(os.path.join(arg0_dir, "guild.cmd")),
            ]
        )
    return None


def _test_exe_path(path):
    if os.path.isfile(path):
        return path
    return None


def _which_guild_exe_for_win():
    return util.find_apply(
        [
            lambda: util.which("guild.cmd"),
            lambda: util.which("guild.exe"),
        ]
    )


def _guild_exe_for_win_error():
    raise RuntimeError("cannot find guild exe for Windows")


def _run_shell_posix_cmd(cmd):
    return "set -eu && %s" % cmd


def _popen(cmd, env, cwd):
    if util.get_platform() == "Windows":
        return _popen_win(cmd, env, cwd)
    else:
        return _popen_posix(cmd, env, cwd)


def _popen_win(cmd, env, cwd):
    return subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        env=env,
        cwd=cwd,
    )


def _popen_posix(cmd, env, cwd):
    return subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        preexec_fn=os.setsid,
        env=env,
        cwd=cwd,
    )


class _kill_after(object):
    def __init__(self, p, timeout):
        self._p = p
        self._timer = threading.Timer(timeout, self._kill)

    def _kill(self):
        if util.get_platform() == "Windows":
            self._kill_win()
        else:
            self._kill_posix()

    def _kill_win(self):
        try:
            self._p.send_signal(signal.CTRL_BREAK_EVENT)
            self._p.kill()
        except OSError as e:
            if e.errno != errno.ESRCH:  # no such process
                raise

    def _kill_posix(self):
        try:
            os.killpg(os.getpgid(self._p.pid), signal.SIGKILL)
        except OSError as e:
            if e.errno != errno.ESRCH:  # no such process
                raise

    def __enter__(self):
        self._timer.start()

    def __exit__(self, _type, _val, _tb):
        self._timer.cancel()


def _strip_lines(out, patterns):
    if isinstance(patterns, str):
        patterns = [patterns]
    stripped_lines = [
        line
        for line in out.split("\n")
        if not any((re.search(p, line) for p in patterns))
    ]
    return "\n".join(stripped_lines)


def _cut_cols(out, to_cut):
    assert isinstance(to_cut, list) and to_cut, to_cut
    cut_lines = [_cut_line(line, to_cut) for line in out.split("\n")]
    return "\n".join([" ".join(cut_line) for cut_line in cut_lines])


def _cut_line(line, to_cut):
    cut_line = []
    cols = line.split()
    for i in to_cut:
        cut_line.extend(cols[i : i + 1])
    return cut_line


def _chdir(s):
    os.chdir(os.path.expandvars(s))
