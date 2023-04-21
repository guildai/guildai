# Copyright 2017-2023 Posit Software, PBC
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
import os
import re
import sys
import tempfile

import guild

from guild import _test as testlib
from guild import config
from guild import pip_util
from guild import util

INDEX = "tests/uat/README.md"
try:
    _workspace_env = os.environ["WORKSPACE"]
except KeyError:
    WORKSPACE = None
    GUILD_HOME = None
else:
    WORKSPACE = os.path.abspath(_workspace_env)
    GUILD_HOME = os.getenv("GUILD_HOME") or os.path.join(WORKSPACE, ".guild")
TEMP = tempfile.gettempdir()
GUILD_PKG = os.path.abspath(guild.__pkgdir__)
REQUIREMENTS_PATH = os.path.join(GUILD_PKG, "requirements.txt")
EXAMPLES = os.path.abspath(os.getenv("EXAMPLES") or os.path.join(GUILD_PKG, "examples"))


def run(force=False, fail_fast=False):
    if not force and not pip_util.running_under_virtualenv():
        sys.stderr.write("This command must be run in a virtual environment\n")
        sys.exit(1)
    if WORKSPACE is None:
        raise ValueError("'WORKSPACE' environment variable not set - cannot run uat")
    tests = _tests_for_index()
    _init_workspace()
    _mark_passed_tests()
    _run_tests(tests, fail_fast)


def _tests_for_index():
    index_path = os.path.join(os.path.dirname(__file__), INDEX)
    index = open(index_path).read()
    return re.findall(r"\((.+?)\.md\)", index)


def _init_workspace():
    print(f"Initializing workspace {WORKSPACE} under {sys.executable}")
    util.ensure_dir(os.path.join(WORKSPACE, "passed-tests"))
    util.ensure_dir(os.path.join(WORKSPACE, ".guild"))


def _mark_passed_tests():
    passed = os.getenv("PASS")
    if not passed:
        return
    for name in [s.strip() for s in passed.split(",")]:
        _mark_test_passed(name)


def _run_tests(tests, fail_fast):
    globs = _test_globals()
    to_skip = os.getenv("UAT_SKIP", "").split(",")
    for name in tests:
        print(f"Running {name}:")
        if _skip_test(name, to_skip):
            print("  skipped (user requested)")
            continue
        if _test_passed(name):
            print("  skipped (already passed)")
            continue
        filename = os.path.join("tests", "uat", name + ".md")
        if testlib.front_matter_skip_test(filename):
            print("  skipped (doctest options)")
            continue
        with UATContext():
            failed, attempted = testlib.run_test_file(
                filename,
                globs=globs,
                fail_fast=fail_fast,
            )
        if not failed:
            print(f"  {attempted} test(s) passed")
            _mark_test_passed(name)
        else:
            sys.exit(1)


def _test_globals():
    globs = testlib.test_globals()
    globs.update(_global_vars())
    return globs


def _global_vars():
    return {
        name: str(val)
        for name, val in globals().items() if name[0] != "_" and isinstance(val, str)
    }


class UATContext:
    """Provides context for a user acceptance test.

    Context consists of an environment suitable for run commands (used
    extensively by the uat) and the setting of Guild home to the
    global `GUILD_HOME` (required by in-process commands that use
    Guild home).

    Note that the UAT Guild home is, by default, local to the UAT
    workspace and not the current process Guild home.
    """
    def __init__(self):
        self._env = util.Env(
            {
                "COLUMNS": "999",
                "EXAMPLES": EXAMPLES,
                "GUILD_HOME": GUILD_HOME,
                "GUILD_PKG": GUILD_PKG,
                "GUILD_PKGDIR": guild.__pkgdir__,
                "LANG": os.getenv("LANG", "en_US.UTF-8"),
                "REQUIREMENTS_PATH": REQUIREMENTS_PATH,
                "TEMP": TEMP,
                "WORKSPACE": WORKSPACE,
            }
        )
        self._guild_home = config.SetGuildHome(GUILD_HOME)

    def __enter__(self):
        self._env.__enter__()
        self._guild_home.__enter__()

    def __exit__(self, *args):
        self._env.__exit__(*args)
        self._guild_home.__exit__(*args)


def _skip_test(name, skip_patterns):
    for p in skip_patterns:
        if fnmatch.fnmatch(name, p):
            return True
    return False


def _test_passed(name):
    return os.path.exists(_test_passed_marker(name))


def _test_passed_marker(name):
    return os.path.join(WORKSPACE, "passed-tests", name)


def _mark_test_passed(name):
    open(_test_passed_marker(name), "w").close()
