# Copyright 2017 TensorHub, Inc.
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

import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading

import guild.test
import guild.var

INDEX = "tests/uat/README.md"
WORKSPACE = os.path.join(tempfile.gettempdir(), "guild-uat")
GUILD_PATH = os.path.abspath("./bazel-bin/guild")
TEMP = tempfile.gettempdir()

GIT_REPOS = os.path.abspath("../")

_cwd = None

def run():
    tests = _tests_from_index()
    if os.path.exists(WORKSPACE):
        print("Found workspace at %s, resuming tests" % WORKSPACE)
    else:
        _init_workspace()
    _run_tests(tests)
    _maybe_delete_workspace()

def _tests_from_index():
    index_path = os.path.join(os.path.dirname(__file__), INDEX)
    index = open(index_path).read()
    return re.findall(r"\((.+?)\.md\)", index)

def _init_workspace():
    print("Initializing workspace %s under %s" % (WORKSPACE, sys.executable))
    subprocess.check_call(["virtualenv", "-p", sys.executable, WORKSPACE])
    open(os.path.join(WORKSPACE, "bin/activate"), "a").write(
        "export GUILD_HOME=%s/.guild\n" % WORKSPACE)
    os.mkdir(os.path.join(WORKSPACE, "passed-tests"))
    os.mkdir(os.path.join(WORKSPACE, ".guild"))
    os.symlink(
        guild.var.cache_dir(),
        os.path.join(WORKSPACE, ".guild", "cache"))

def _run_tests(tests):
    globs = _test_globals()
    for name in tests:
        print("Running %s:" % name)
        if _test_passed(name):
            print("  skipped (already passed)")
            continue
        filename = os.path.join("tests", "uat", name + ".md")
        _reset_cwd()
        failed, attempted = guild.test.run_test_file(filename, globs)
        if not failed:
            print("  %i test(s) passed" % attempted)
            _mark_test_passed(name)
        else:
            sys.exit(1)

def _test_globals():
    globs = {}
    globs.update(_global_vars())
    globs.update({
        "cd": _cd,
        "run": _run,
        "quiet": lambda cmd, **kw: _run(cmd, quiet=True, **kw),
        "abspath": os.path.abspath,
    })
    return globs

def _global_vars():
    return {
        name: str(val)
        for name, val in globals().items()
        if name[0] != "_" and isinstance(val, str)
    }

def _test_passed(name):
    return os.path.exists(_test_passed_marker(name))

def _test_passed_marker(name):
    return os.path.join(WORKSPACE, "passed-tests", name)

def _mark_test_passed(name):
    open(_test_passed_marker(name), "w").close()

def _reset_cwd():
    globals()["_cwd"] = None

def _cd(path):
    if not os.path.isdir(os.path.join(WORKSPACE, path)):
        raise ValueError("'%s' does not exist" % path)
    globals()["_cwd"] = path

def _run(cmd, quiet=False, ignore=None, timeout=60):
    cmd = "set -eu && %s" % cmd
    cmd_env = {}
    cmd_env.update(_global_vars())
    cmd_env["GUILD_HOME"] = os.path.join(WORKSPACE, ".guild")
    cmd_env["PATH"] = os.path.pathsep.join([
        os.path.join(WORKSPACE, "bin"),
        GUILD_PATH,
        os.getenv("PATH"),
    ])
    cmd_env["COLUMNS"] = "999"
    cmd_env["LANG"] = os.getenv("LANG", "")
    cmd_cwd = WORKSPACE if not _cwd else os.path.join(WORKSPACE, _cwd)
    p = subprocess.Popen(
        [cmd],
        shell=True,
        env=cmd_env,
        cwd=cmd_cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        preexec_fn=os.setsid)
    with _kill_after(p, timeout):
        exit_code = p.wait()
        out = p.stdout.read()
    if not quiet or exit_code != 0:
        out = out.strip()
        if sys.version_info[0] > 2:
            out = out.decode("utf-8")
        if ignore:
            out = _strip_lines(out, ignore)
        print(out)
        print("<exit %i>" % exit_code)

class _kill_after(object):

    def __init__(self, p, timeout):
        self._p = p
        self._timer = threading.Timer(timeout, self._kill)

    def _kill(self):
        os.killpg(os.getpgid(self._p.pid), signal.SIGKILL)

    def __enter__(self):
        self._timer.start()

    def __exit__(self, _type, _val, _tb):
        self._timer.cancel()

def _strip_lines(out, patterns):
    if isinstance(patterns, str):
        patterns = [patterns]
    stripped_lines = [
        line for line in out.split("\n")
        if not any((re.search(p, line) for p in patterns))
    ]
    return "\n".join(stripped_lines)

def _maybe_delete_workspace():
    if os.getenv("KEEP_WORKSPACE"):
        print("KEEP_WORKSPACE specified, leaving %s in place" % WORKSPACE)
    else:
        _delete_workspace()

def _delete_workspace():
    assert os.path.dirname(WORKSPACE) == tempfile.gettempdir(), WORKSPACE
    print("Deleting workspace %s" % WORKSPACE)
    shutil.rmtree(WORKSPACE)
