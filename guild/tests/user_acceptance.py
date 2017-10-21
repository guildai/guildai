#!/usr/bin/env python

from __future__ import print_function

import doctest
import inspect
import os
import shutil
import subprocess
import sys
import tempfile

from os.path import abspath, dirname, exists

WORKSPACE = None

GUILD = abspath("bazel-bin/guild/guild")

if exists("../guild-examples"):
    EXAMPLES_REPO = abspath("../guild-examples")
else:
    EXAMPLES_REPO = "https://github.com/guildai/guild-examples.git"

_cwd = None

def main():
    init_workspace()
    clone_examples()
    no_cwd_modelfile_tests()
    mnist_tests()
    #keras_zero_config_tests()
    delete_workspace()

def init_workspace():
    path = tempfile.mkdtemp(prefix="guild-test-")
    print("Created workspace %s" % path)
    globals()["WORKSPACE"] = path

def clone_examples():
    run("git -C $WORKSPACE clone $EXAMPLES_REPO")

def no_cwd_modelfile_tests():
    """Various operations run in a directory that doesn't have models.

    Running an operation on a default model that doesn't exit:

    >>> run("$GUILD run train")
    guild: there are no models in the current directory
    Try a different directory or 'guild operations' for available operations.

    """
    cd("$WORKSPACE")
    rundoc()

def mnist_tests():
    cd("$WORKSPACE/guild-examples/mnist2")
    mnist_invalid_commands_tests()
    mnist_empty_project_tests()
    mnist_train_intro_tests()
    mnist_single_run_tests()

def mnist_invalid_commands_tests():
    """Attempts various invalid Guild commands.

    Let's try to train a model that doesn't exist:

    >>> run("$GUILD train foobar")
    guild: cannot find a model matching 'foobar'
    Try 'guild models' for a list of available models.

    Let's try to train a model that has multiple matches:

    >>> run("$GUILD train mnist")
    guild: there are multiple models that match 'mnist'
    Try specifying one of the following:
      ./mnist-expert
      ./mnist-intro

    """
    rundoc()

def mnist_empty_project_tests():
    """Examines an empty project.

    Running `models` inside a modelfile project will list the models
    defined only in the current modelfile.

    >>> run("$GUILD models")
    Limiting models to the current directory (use --all to include all).
    ./mnist-expert  MNIST model from TensorFlow expert tutorial
    ./mnist-intro   MNIST model from TensorFlow intro tutorial

    Running `runs` for a new project will return an empty
    list. Because there aren't any runs.

    >>> run("$GUILD runs")
    Limiting runs to the current directory (use --all to include all).

    """
    rundoc()

def mnist_train_intro_tests():
    """Trains the mnist intro model.

    Let's train the intro model with 1 epoch:

    >>> run("$GUILD train -y intro epochs=1")
    Extracting /tmp/MNIST_data/train-images-idx3-ubyte.gz
    Extracting /tmp/MNIST_data/train-labels-idx1-ubyte.gz
    Extracting /tmp/MNIST_data/t10k-images-idx3-ubyte.gz
    Extracting /tmp/MNIST_data/t10k-labels-idx1-ubyte.gz
    ...
    Step 0: training=...
    Step 0: validate=...
    Step 20: training=...
    Step 20: validate=...
    ...
    Step 540: training=...
    Step 540: validate=...

    """
    rundoc()

def mnist_single_run_tests():
    """Examines a project with a single run.

    We've just trained the intro model and have a single completed
    run:

    >>> run("$GUILD runs")
    Limiting runs to the current directory (use --all to include all).
    [0:...]  ./mnist-intro:train  ... ...  completed

    """
    rundoc()

def keras_zero_config_tests():
    print("TODO: train keras zero config")

def delete_workspace():
    assert dirname(WORKSPACE) == tempfile.gettempdir(), WORKSPACE
    print("Deleting workspace %s" % WORKSPACE)
    shutil.rmtree(WORKSPACE)

def rundoc():
    frame = inspect.currentframe()
    test_name = inspect.getouterframes(frame)[1][3]
    test_fun = globals()[test_name]
    finder = doctest.DocTestFinder()
    flags=(
        doctest.REPORT_ONLY_FIRST_FAILURE |
        doctest.ELLIPSIS |
        doctest.IGNORE_EXCEPTION_DETAIL |
        doctest.NORMALIZE_WHITESPACE
    )
    runner = doctest.DocTestRunner(optionflags=flags)
    print("Running %s:" % test_name)
    for test in finder.find(test_fun, test_name, globs=globals()):
        runner.run(test)
    failed, attempted = runner.summarize()
    if not failed:
        print("  %i test(s) passed" % attempted)
    else:
        sys.exit(1)

def cd(path):
    globals()["_cwd"] = path

def run(cmd):
    if _cwd:
        cmd = "cd %s && %s" % (_cwd, cmd)
    cmd = "set -eu && %s" % cmd
    try:
        out = subprocess.check_output(
            [cmd],
            shell=True,
            env=_globals_env(),
            stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        out = e.output
    print(out.strip())

def _globals_env():
    return {
        name: str(val)
        for name, val in globals().items()
        if isinstance(val, str)
    }

if __name__ == "__main__":
    main()
