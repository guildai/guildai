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

- `?...` should be an alias for `...`. This can be used on the first
  line of a matching section. Currently we have to print some dummy
  var to work-around the ambiguity of `...`.

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import doctest
import fnmatch
import glob
import os
import platform
import pprint
import re
import sys
import tempfile

from guild import _api as gapi
from guild import cli
from guild import config as configlib
from guild import guildfile
from guild import index2
from guild import init
from guild import op_util
from guild import util

PLATFORM = platform.system()

TEST_NAME_WIDTH = 27

class Py23DocChecker(doctest.OutputChecker):
    """Output checker that works around Python 2/3 unicode representations.

    https://dirkjan.ochtman.nl/writing/2014/07/06/single-source-python-23-doctests.html
    """

    def check_output(self, want, got, optionflags):
        if sys.version_info[0] > 2:
            # Strip unicode prefix from expected output on Python 2
            want = re.sub("u'(.*?)'", "'\\1'", want)
            want = re.sub('u"(.*?)"', '"\\1"', want)
        if PLATFORM == "Windows":
            # Convert Windows paths to UNIXy paths
            got = re.sub(r"[c-zC-Z]:\\\\?|\\\\?", "/", got)
        return doctest.OutputChecker.check_output(self, want, got, optionflags)

def run_all(skip=None):
    return run(all_tests(), skip)

def all_tests():
    test_pattern = os.path.join(tests_dir(), "*.md")
    return sorted(
        [_test_name_from_path(path)
         for path in glob.glob(test_pattern)])

def tests_dir():
    return os.path.join(os.path.dirname(__file__), "tests")

def _test_name_from_path(path):
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
                "  %s:%s skipped\n"
                % (test, " " * (TEST_NAME_WIDTH - len(test))))
    return success

def _run_test(name):
    sys.stdout.write("  %s: " % name)
    sys.stdout.flush()
    filename = _test_filename(name)
    globs = test_globals()
    try:
        failures, _tests = run_test_file(filename, globs)
    except IOError:
        sys.stdout.write(" ERROR test not found\n")
        return False
    else:
        if not failures:
            sys.stdout.write(" " * (TEST_NAME_WIDTH - len(name)))
            sys.stdout.write("ok\n")
            sys.stdout.flush()
        return failures == 0

def _test_filename(name):
    # Path must be relative to module
    return os.path.join("tests", name + ".md")

def run_test_file(filename, globs):
    return run_test_file_with_config(
        filename,
        globs=globs,
        optionflags=(
            _report_first_flag() |
            doctest.ELLIPSIS |
            doctest.NORMALIZE_WHITESPACE))

def _report_first_flag():
    if os.getenv("REPORT_ONLY_FIRST_FAILURE") == "1":
        return doctest.REPORT_ONLY_FIRST_FAILURE
    return 0

def run_test_file_with_config(filename, globs, optionflags):
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
    runner = doctest.DocTestRunner(
        checker=checker,
        verbose=None,
        optionflags=optionflags)
    parser = doctest.DocTestParser()
    test = parser.get_doctest(text, globs, name, filename, 0)
    flags = (
        print_function.compiler_flag |
        absolute_import.compiler_flag |
        division.compiler_flag
    )
    runner.run(test, flags)
    runner.summarize()
    if doctest.master is None:
        doctest.master = runner
    else:
        doctest.master.merge(runner)
    return doctest.TestResults(runner.failures, runner.tries)

def _load_testfile(filename):
    # Wrapper to handle Python 2/3 differences
    try:
        # pylint: disable=no-value-for-parameter
        return doctest._load_testfile(filename, None, True)
    except TypeError:
        # pylint: disable=too-many-function-args
        return doctest._load_testfile(filename, None, True, "utf-8")

def test_globals():
    return {
        "Chdir": Chdir,
        "Env": Env,
        "LogCapture": util.LogCapture,
        "ModelPath": ModelPath,
        "Project": Project,
        "StderrCapture": StderrCapture,
        "SysPath": SysPath,
        "TempFile": util.TempFile,
        "UserConfig": UserConfig,
        "abspath": os.path.abspath,
        "basename": os.path.basename,
        "cat": cat,
        "dir": dir,
        "dirname": os.path.dirname,
        "exists": os.path.exists,
        "find": find,
        "gapi": gapi,
        "guildfile": guildfile,
        "join_path": os.path.join,
        "mkdir": os.mkdir,
        "mkdtemp": mkdtemp,
        "mktemp_guild_dir": mktemp_guild_dir,
        "os": os,
        "pprint": pprint.pprint,
        "re": re,
        "realpath": os.path.realpath,
        "relpath": os.path.relpath,
        "sample": sample,
        "samples_dir": samples_dir,
        "sha256": util.file_sha256,
        "symlink": os.symlink,
        "touch": util.touch,
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

def find(root, followlinks=False):
    all = []
    relpath = lambda path, name: (
        os.path.relpath(os.path.join(path, name), root))
    for path, dirs, files in os.walk(root, followlinks=followlinks):
        for name in dirs:
            if os.path.islink(os.path.join(path, name)):
                all.append(relpath(path, name))
        for name in files:
            all.append(relpath(path, name))
    return sorted(all)

def cat(*parts):
    with open(os.path.join(*parts), "r") as f:
        print(f.read())

def dir(path, ignore=None):
    return sorted([
        name for name in os.listdir(path)
        if ignore is None
        or not any((fnmatch.fnmatch(name, p) for p in ignore))
    ])

def _patch_py3_exception_detail():
    import traceback
    format_exception_only = traceback.format_exception_only
    def patch(*args):
        formatted = format_exception_only(*args)
        formatted[-1] = _strip_error_module(formatted[-1])
        return formatted
    traceback.format_exception_only = patch

def _strip_error_module(last_line):
    m = re.match(r"([\w\.]+): (.+)", last_line)
    if not m:
        return _strip_class_module(last_line)
    else:
        return "{}: {}".format(_strip_class_module(m.group(1)), m.group(2))

def _strip_class_module(class_name):
    return class_name[class_name.rfind(".") + 1:]

if sys.version_info[0] > 2:
    _patch_py3_exception_detail()

class StderrCapture(object):

    closed = False
    _stderr = None
    _captured = []

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

    def flush(self):
        pass

    def print(self):
        for part in self._captured:
            sys.stdout.write(part.decode("utf-8"))
        sys.stdout.flush()

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

def write(filename, contents):
    with open(filename, "w") as f:
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

    simplify_trial_output_patterns = [
        (re.compile(r"INFO: \[guild\] "), ""),
        (re.compile(r"trial [a-f0-9]+"), "trial"),
    ]

    def __init__(self, cwd):
        self.guild_home = mkdtemp()
        self.cwd = cwd
        runs_path = os.path.join(self.guild_home, "runs")
        self.index = index2.RunIndex(runs_path)

    def run(self, *args, **kw):
        print(self._run(*args, **kw))

    def _run(self, *args, **kw):
        simplify_trial_output = kw.pop("simplify_trial_output", False)
        try:
            out = gapi.run_capture_output(
                guild_home=self.guild_home,
                cwd=self.cwd,
                *args, **kw)
        except gapi.RunError as e:
            return "{}\n<exit {}>".format(e.output.strip(), e.returncode)
        else:
            if simplify_trial_output:
                out = self._simplify_trial_output(out)
            return out.strip()

    def _simplify_trial_output(self, out):
        for p, repl in self.simplify_trial_output_patterns:
            out = p.sub(repl, out)
        return out

    def list_runs(self, **kw):
        return gapi.runs_list(
            cwd=self.cwd,
            guild_home=self.guild_home,
            **kw)

    def print_runs(self, runs=None, flags=False, labels=False, status=False):
        if runs is None:
            runs = self.list_runs()
        cols = self._cols_for_print_runs(flags, labels, status)
        rows = []
        with Chdir(self.cwd):
            for run in runs:
                rows.append(self._row_for_print_run(
                    run, flags, labels, status))
        cli.table(rows, cols)

    @staticmethod
    def _cols_for_print_runs(flags, labels, status):
        cols = ["opspec"]
        if flags:
            cols.append("flags")
        if labels:
            cols.append("label")
        if status:
            cols.append("status")
        return cols

    @staticmethod
    def _row_for_print_run(run, flags, labels, status):
        row = {
            "opspec": op_util.format_op_desc(run)
        }
        if flags:
            flags_desc = " ".join(
                ["%s=%s" % (name, op_util.format_flag_val(val))
                 for name, val in sorted(run.get("flags").items())])
            row["flags"] = flags_desc
        if labels:
            row["label"] = run.get("label", "")
        if status:
            row["status"] = run.status
        return row

    def delete_runs(self, runs=None):
        gapi.runs_delete(runs, guild_home=self.guild_home)

    def print_trials(self, *args, **kw):
        print(self._run(print_trials=True, *args, **kw))

    @staticmethod
    def ls(run, all=False):
        def filter(path):
            if all:
                return True
            return not path.startswith(".guild")
        return [path for path in find(run.path) if filter(path)]

    @staticmethod
    def cat(run, path):
        cat(os.path.join(run.path, path))

    def mark(self, run, **kw):
        gapi.mark(
            run,
            cwd=self.cwd,
            guild_home=self.guild_home,
            **kw)

    def run_scalars(self, run):
        self.index.refresh([run], ["scalar"])
        return self.index.run_scalars(run)

    def run_scalar(self, run, prefix, tag, qual, step):
        self.index.refresh([run], ["scalar"])
        return self.index.run_scalar(run, prefix, tag, qual, step)

    def compare(self, runs=None, **kw):
        return gapi.compare(
            runs=runs,
            cwd=self.cwd,
            guild_home=self.guild_home,
            **kw)

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
        # behavior for a reset here
        configlib._user_config = None

class Env(object):

    def __init__(self, vals):
        self._vals = vals
        self._revert_ops = []

    def __enter__(self):
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
        for op in self._revert_ops:
            op()
