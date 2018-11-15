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

from guild import _api
from guild import init
from guild import util

PLATFORM = platform.system()

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
                % (test, " " * (23 - len(test))))
    return success

def _run_test(name):
    sys.stdout.write("  %s:" % name)
    filename = _test_filename(name)
    globs = _test_globals()
    try:
        failures, _tests = run_test_file(filename, globs)
    except IOError:
        sys.stdout.write(" ERROR test not found\n")
        return False
    else:
        if not failures:
            sys.stdout.write(" " * (25 - len(name)))
            sys.stdout.write(" ok\n")
        return failures == 0

def _test_filename(name):
    # Path must be relative to module
    return os.path.join("tests", name + ".md")

def run_test_file(filename, globs):
    return run_test_file_with_config(
        filename,
        globs=globs,
        optionflags=(
            doctest.REPORT_ONLY_FIRST_FAILURE |
            doctest.ELLIPSIS |
            doctest.NORMALIZE_WHITESPACE))

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

def _test_globals():
    return {
        "Chdir": Chdir,
        "LogCapture": util.LogCapture,
        "StderrCapture": StderrCapture,
        "abspath": os.path.abspath,
        "cat": cat,
        "dir": dir,
        "dirname": os.path.dirname,
        "find": find,
        "gapi": _api,
        "join_path": os.path.join,
        "mkdir": os.mkdir,
        "mkdtemp": mkdtemp,
        "mktemp_guild_dir": mktemp_guild_dir,
        "pprint": pprint.pprint,
        "realpath": os.path.realpath,
        "relpath": os.path.relpath,
        "sample": sample,
        "samples_dir": samples_dir,
        "symlink": os.symlink,
        "touch": util.touch,
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

def find(root):
    all = []
    for path, _, files in os.walk(root):
        for name in files:
            full_path = os.path.join(path, name)
            rel_path = os.path.relpath(full_path, root)
            all.append(rel_path)
    all.sort()
    return all

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
