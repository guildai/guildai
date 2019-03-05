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
from __future__ import print_function

import errno
import fnmatch
import os
import pprint
import re
import signal
import subprocess
import sys
import tempfile
import threading

import guild
import guild._test
import guild.var

from guild import pip_util
from guild import util

INDEX = "tests/uat/README.md"
WORKSPACE = os.path.abspath(os.getenv("WORKSPACE") or "GUILD-UAT-WORKSPACE")
TEMP = tempfile.gettempdir()
GUILD_PKG = os.path.abspath(guild.__pkgdir__)
REQUIREMENTS_PATH = os.path.join(GUILD_PKG, "requirements.txt")

_cwd = None

def run():
    if not pip_util.running_under_virtualenv():
        sys.stderr.write("This command must be run in a virtual environment\n")
        sys.exit(1)
    tests = _tests_from_index()
    _init_workspace()
    _run_tests(tests)

def _tests_from_index():
    index_path = os.path.join(os.path.dirname(__file__), INDEX)
    index = open(index_path).read()
    return re.findall(r"\((.+?)\.md\)", index)

def _init_workspace():
    print("Initializing workspace %s under %s" % (WORKSPACE, sys.executable))
    util.ensure_dir(os.path.join(WORKSPACE, "passed-tests"))
    util.ensure_dir(os.path.join(WORKSPACE, ".guild"))

def _run_tests(tests):
    globs = _test_globals()
    to_skip = os.getenv("UAT_SKIP", "").split(",")
    for name in tests:
        print("Running %s:" % name)
        if _skip_test(name, to_skip):
            print("  skipped (user requested)")
            continue
        if _test_passed(name):
            print("  skipped (already passed)")
            continue
        filename = os.path.join("tests", "uat", name + ".md")
        _reset_cwd()
        failed, attempted = guild._test.run_test_file(filename, globs)
        if not failed:
            print("  %i test(s) passed" % attempted)
            _mark_test_passed(name)
        else:
            sys.exit(1)

def _test_globals():
    globs = guild._test.test_globals()
    globs.update(_global_vars())
    globs.update({
        "cd": _cd,
        "cwd": _get_cwd,
        "pprint": pprint.pprint,
        "run": _run,
        "quiet": lambda cmd, **kw: _run(cmd, quiet=True, **kw),
        "abspath": os.path.abspath,
        "sample": _sample,
    })
    return globs

def _global_vars():
    return {
        name: str(val)
        for name, val in globals().items()
        if name[0] != "_" and isinstance(val, str)
    }

def _sample(path):
    return os.path.abspath(guild._test.sample(path))

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

def _reset_cwd():
    globals()["_cwd"] = None

def _cd(path):
    if not os.path.isdir(os.path.join(WORKSPACE, path)):
        raise ValueError("'%s' does not exist" % path)
    globals()["_cwd"] = path

def _get_cwd():
    if _cwd:
        return os.path.join(WORKSPACE, _cwd)
    return WORKSPACE

def _run(cmd, quiet=False, ignore=None, timeout=60):
    cmd = "set -eu && %s" % cmd
    cmd_env = {}
    cmd_env.update(_global_vars())
    cmd_env["GUILD_HOME"] = os.path.join(WORKSPACE, ".guild")
    cmd_env["PATH"] = os.environ["PATH"]
    cmd_env["LD_LIBRARY_PATH"] = os.getenv("LD_LIBRARY_PATH", "")
    if "VIRTUAL_ENV" in os.environ:
        cmd_env["VIRTUAL_ENV"] = os.environ["VIRTUAL_ENV"]
    cmd_env["COLUMNS"] = "999"
    cmd_env["LANG"] = os.getenv("LANG", "en_US.UTF-8")
    if _cwd:
        cmd_cwd = os.path.join(WORKSPACE, _cwd)
    else:
        cmd_cwd = WORKSPACE
    _apply_ssh_env(cmd_env)
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
        out = out.strip().decode("utf-8")
        if ignore:
            out = _strip_lines(out, ignore)
        print(out)
        print("<exit %i>" % exit_code)

def _apply_ssh_env(env):
    ssh_env = (
        "SSH_AUTH_SOCK",
        "USER",
    )
    for name in ssh_env:
        try:
            env[name] = os.environ[name]
        except KeyError:
            pass

class _kill_after(object):

    def __init__(self, p, timeout):
        self._p = p
        self._timer = threading.Timer(timeout, self._kill)

    def _kill(self):
        try:
            os.killpg(os.getpgid(self._p.pid), signal.SIGKILL)
        except OSError as e:
            if e.errno != errno.ESRCH: # no such process
                raise

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
