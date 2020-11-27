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
from __future__ import print_function

import fnmatch
import os
import re
import sys
import tempfile

import guild

from guild import _test as testlib
from guild import pip_util
from guild import util


INDEX = "tests/uat/README.md"
try:
    _workspace_env = os.environ["WORKSPACE"]
except KeyError:
    WORKSPACE = None
    GUILD_HOME = os.path.abspath(".")
else:
    WORKSPACE = os.path.abspath(_workspace_env)
    GUILD_HOME = os.path.join(WORKSPACE, ".guild")
TEMP = tempfile.gettempdir()
GUILD_PKG = os.path.abspath(guild.__pkgdir__)
REQUIREMENTS_PATH = os.path.join(GUILD_PKG, "requirements.txt")
EXAMPLES = os.path.abspath(os.getenv("EXAMPLES") or os.path.join(GUILD_PKG, "examples"))


def run():
    if not pip_util.running_under_virtualenv():
        sys.stderr.write("This command must be run in a virtual environment\n")
        sys.exit(1)
    tests = _tests_for_index()
    _init_workspace()
    _mark_passed_tests()
    _run_tests(tests)


def _tests_for_index():
    index_path = os.path.join(os.path.dirname(__file__), INDEX)
    index = open(index_path).read()
    return re.findall(r"\((.+?)\.md\)", index)


def _init_workspace():
    print("Initializing workspace %s under %s" % (WORKSPACE, sys.executable))
    util.ensure_dir(os.path.join(WORKSPACE, "passed-tests"))
    util.ensure_dir(os.path.join(WORKSPACE, ".guild"))


def _mark_passed_tests():
    passed = os.getenv("PASS")
    if not passed:
        return
    for name in [s.strip() for s in passed.split(",")]:
        _mark_test_passed(name)


def _run_tests(tests):
    globs = _test_globals()
    to_skip = os.getenv("UAT_SKIP", "").split(",")
    with _UATEnv():
        for name in tests:
            print("Running %s:" % name)
            if _skip_test(name, to_skip):
                print("  skipped (user requested)")
                continue
            if _test_passed(name):
                print("  skipped (already passed)")
                continue
            filename = os.path.join("tests", "uat", name + ".md")
            failed, attempted = testlib.run_test_file(filename, globs)
            if not failed:
                print("  %i test(s) passed" % attempted)
                _mark_test_passed(name)
            else:
                sys.exit(1)


def _test_globals():
    globs = testlib.test_globals()
    globs.update(_global_vars())
    globs.update({"sample": _sample, "example": _example_dir})
    return globs


def _global_vars():
    return {
        name: str(val)
        for name, val in globals().items()
        if name[0] != "_" and isinstance(val, str)
    }


def _sample(path):
    return os.path.abspath(testlib.sample(path))


def _UATEnv():
    return util.Env(
        {
            "COLUMNS": "999",
            "EXAMPLES": EXAMPLES,
            "GUILD_HOME": os.path.join(WORKSPACE, ".guild"),
            "GUILD_PKG": GUILD_PKG,
            "GUILD_PKGDIR": guild.__pkgdir__,
            "LANG": os.getenv("LANG", "en_US.UTF-8"),
            "REQUIREMENTS_PATH": REQUIREMENTS_PATH,
            "TEMP": TEMP,
            "WORKSPACE": WORKSPACE,
        }
    )


def _skip_test(name, skip_patterns):
    for p in skip_patterns:
        if fnmatch.fnmatch(name, p):
            return True
    return False


def _example_dir(name):
    return os.path.join(EXAMPLES, name)


def _test_passed(name):
    return os.path.exists(_test_passed_marker(name))


def _test_passed_marker(name):
    return os.path.join(WORKSPACE, "passed-tests", name)


def _mark_test_passed(name):
    open(_test_passed_marker(name), "w").close()
