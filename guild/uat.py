from __future__ import print_function

import doctest
import inspect
import os
import re
import shutil
import subprocess
import sys
import tempfile

import guild.test

INDEX = "guild/tests/uat/README.md"
WORKSPACE = os.path.join(tempfile.gettempdir(), "guild-uat")
GUILD_PATH = os.path.abspath("./bazel-bin/guild")
EXAMPLES_REPO = os.path.abspath("../guild-examples")

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
    readme = open(INDEX).read()
    return re.findall("\((.+?)\.md\)", readme)

def _init_workspace():
    print("Initializing workspace %s" % WORKSPACE)
    subprocess.call(["virtualenv", WORKSPACE])
    os.mkdir(os.path.join(WORKSPACE, "passed-tests"))
    os.mkdir(os.path.join(WORKSPACE, ".guild"))

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
        "quiet": lambda cmd: _run(cmd, quiet=True),
        "abspath": os.path.abspath,
    })
    return globs

def _global_vars():
    return {
        name: str(val)
        for name, val in globals().items()
        if isinstance(val, str)
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
    globals()["_cwd"] = path

def _run(cmd, quiet=False):
    cmd = "set -eu && %s" % cmd
    cmd_env = {}
    cmd_env.update(_global_vars())
    cmd_env["GUILD_HOME"] = os.path.join(WORKSPACE, ".guild")
    cmd_env["PATH"] = os.path.pathsep.join([
        os.path.join(WORKSPACE, "bin"),
        GUILD_PATH,
        "/usr/bin",
    ])
    cmd_cwd = WORKSPACE if not _cwd else os.path.join(WORKSPACE, _cwd)
    try:
        out = subprocess.check_output(
            [cmd],
            shell=True,
            env=cmd_env,
            cwd=cmd_cwd,
            stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        out = e.output
        exit_code = e.returncode
    else:
        exit_code = 0
    if not quiet or exit_code != 0:
        print(out.strip())
        print("<exit %i>" % exit_code)

def _maybe_delete_workspace():
    if os.getenv("KEEP_WORKSPACE"):
        print("KEEP_WORKSPACE specified, leaving %s in place" % WORKSPACE)
    else:
        _delete_workspace()

def _delete_workspace():
    assert os.path.dirname(WORKSPACE) == tempfile.gettempdir(), WORKSPACE
    print("Deleting workspace %s" % WORKSPACE)
    shutil.rmtree(WORKSPACE)
