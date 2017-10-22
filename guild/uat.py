from __future__ import print_function

import doctest
import inspect
import os
import shutil
import subprocess
import sys
import tempfile

import guild.test

WORKSPACE = os.path.join(tempfile.gettempdir(), "guild-uat")
GUILD_PATH = os.path.abspath("./bazel-bin/guild")
EXAMPLES_REPO = os.path.abspath("../guild-examples")

_cwd = None

TESTS = [
    "fresh-install",
    "install-required-pip-packages",
    "check-without-tensorflow",
    "install-tensorflow",
    "check-with-tensorflow",
    "guild-tests",
    "initial-packages",
    "initial-models",
    "initial-ops",
    "initial-runs",
    "train-missing-model",
    "run-with-missing-default-model",
    "install-mnist-packages",
    "packages-after-mnist-install",
    "models-after-mnist-install",
    "ops-after-mnist-install",
    "train-multiple-matches",
    "train-mnist-softmax",
    "runs-after-mnist-softmax-train",
    "install-examples",
    "mnist-example-models",
    "mnist-example-ops",
    "mnist-example-initial-runs",
    "train-mnist-intro-example",
    "mnist-example-runs-after-intro-train",
]

def run():
    if os.path.exists(WORKSPACE):
        print("Found workspace at %s, resuming tests" % WORKSPACE)
    else:
        _init_workspace()
    _run_tests()
    _maybe_delete_workspace()

def _init_workspace():
    print("Initializing workspace %s" % WORKSPACE)
    subprocess.call(["virtualenv", WORKSPACE])
    os.mkdir(os.path.join(WORKSPACE, "passed-tests"))
    os.mkdir(os.path.join(WORKSPACE, ".guild"))

def _run_tests():
    globs = _test_globals()
    for name in TESTS:
        print("Running %s:" % name)
        if _test_passed(name):
            print("  skipped (already passed)")
            continue
        filename = os.path.join("tests", "uat", name + ".md")
        _cd(WORKSPACE)
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

def _cd(path):
    globals()["_cwd"] = path

def _run(cmd, quiet=False):
    if _cwd:
        cmd = "cd %s && %s" % (os.path.join(WORKSPACE, _cwd), cmd)
    cmd = "set -eu && %s" % cmd
    cmd_env = {}
    cmd_env.update(_global_vars())
    cmd_env["GUILD_HOME"] = os.path.join(WORKSPACE, ".guild")
    cmd_env["PATH"] = os.path.pathsep.join([
        os.path.join(WORKSPACE, "bin"),
        GUILD_PATH,
        "/usr/bin",
    ])
    try:
        out = subprocess.check_output(
            [cmd],
            shell=True,
            env=cmd_env,
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
