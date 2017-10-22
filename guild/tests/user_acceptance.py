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

WORKSPACE = os.getenv("WORKSPACE")

GUILD = abspath("bazel-bin/guild/guild")

if exists("../guild-examples"):
    EXAMPLES_REPO = abspath("../guild-examples")
else:
    EXAMPLES_REPO = "https://github.com/guildai/guild-examples.git"

_cwd = None

def main():
    if WORKSPACE is None:
        init_workspace()
    fresh_install_test()
    install_required_pip_packages()
    check_guild_without_tensorflow_test()
    install_tensorflow()
    check_guild_with_tensorflow_test()
    run_guild_tests_test()
    initial_packages_test()
    install_mnist_packages_test()
    install_examples()
    no_cwd_modelfile_tests()
    mnist_tests()
    keras_zero_config_tests()
    delete_workspace()

def test_env():
    env_root = "/tmp/guild-uat-hhwPZw"
    path = [
        os.path.join(env_root, "bin"),
        "./bazel-bin/guild",
    ]
    cmd_env = {
        "PATH": os.path.pathsep.join(path)
    }
    subprocess.call("pip list --user --format=legacy", shell=True, env=cmd_env)
    subprocess.call("guild packages", shell=True, env=cmd_env)

def init_workspace():
    print("Initializing workspace")
    path = tempfile.mkdtemp(prefix="guild-uat-")
    subprocess.call(["virtualenv", path])
    print("Created workspace %s" % path)
    globals()["WORKSPACE"] = path

def fresh_install_test():
    """Guild behavior on a fresh install.

    Guild require a number of Python packages. If any of these aren't
    installed it will exit with a user message.

    >>> run("$GUILD check")
    guild: missing required package 'twine'
    Try 'pip install twine' to install the package.
    <exit 1>

    Guild will continue to display these messages until all of its
    requires packages are installed.

    """
    rundoc()

def install_required_pip_packages():
    print("Installing required pip packages")
    run("pip install twine")
    run("pip install Werkzeug")
    run("pip install PyYAML")

def check_guild_without_tensorflow_test():
    """Runs guild check assuming that tensorflow is not installed.

    Guild check should display information but note that tensorflow is
    not installed and display an error message.

    >>> run("$GUILD check")
    guild_version:             ...
    guild_home:                ...
    installed_plugins:         gpu, keras, disk, cpu, memory
    python_version:            ...
    tensorflow_version:        NOT INSTALLED (No module named tensorflow)
    nvidia_smi_available:      ...
    pip_version:               ...
    psutil_version:            ...
    setuptools_version:        ...
    twine_version:             ...
    yaml_version:              ...
    werkzeug_version:          ...
    guild: there are problems with your Guild setup
    Refer to the issues above for more information.
    <exit 1>
    """
    rundoc()

def install_tensorflow():
    print("Installing tensorflow")
    run("pip install tensorflow")

def check_guild_with_tensorflow_test():
    """Runs guild check assuming that tensorflow is installed.

    >>> run("$GUILD check")
    guild_version:             ...
    guild_home:                ...
    installed_plugins:         gpu, keras, disk, cpu, memory
    python_version:            ...
    tensorflow_version:        ...
    tensorflow_cuda_support:   no
    tensorflow_gpu_available:  no
    libcuda_version:           not loaded
    libcudnn_version:          not loaded
    tensorboard_version:       ...
    nvidia_smi_available:      ...
    pip_version:               ...
    psutil_version:            ...
    setuptools_version:        ...
    twine_version:             ...
    yaml_version:              ...
    werkzeug_version:          ...
    <exit 0>

    """
    rundoc()

def run_guild_tests_test():
    """Runs guild tests.

    >>> run("$GUILD check -nT")
    internal tests:
      config:                  ok
      cpu-plugin:              ok
      disk-plugin:             ok
      imports:                 ok
      logging:                 ok
      main-bootstrap:          ok
      memory-plugin:           ok
      modelfiles:              ok
      models:                  ok
      namespaces:              ok
      ops:                     ok
      packages:                ok
      plugin-python-utils:     ok
      plugins:                 ok
      resources:               ok
      runs:                    ok
      tables:                  ok
      utils:                   ok
      var:                     ok
    <exit 0>

    """
    rundoc()

def initial_packages_test():
    """Lists packages within a fresh environment.

    By default the packages command lists Guild packages (i.e. within
    the gpkg namespace). We don't have any installed yet so this is an
    empty list.

    >>> run("$GUILD packages")
    <BLANKLINE>
    <exit 0>

    If we use the -a option, we get all packages, which at this point
    consists of all of the pip packages that have been installed in
    the env.

    >>> run("$GUILD packages -a")
    pypi/Markdown                ...
    pypi/PyYAML                  ...
    pypi/Werkzeug                ...
    pypi/backports.weakref       ...
    pypi/bleach                  ...
    pypi/certifi                 ...
    pypi/chardet                 ...
    pypi/funcsigs                ...
    pypi/html5lib                ...
    pypi/idna                    ...
    pypi/mock                    ...
    pypi/numpy                   ...
    pypi/pbr                     ...
    pypi/pip                     ...
    pypi/pkginfo                 ...
    pypi/protobuf                ...
    pypi/requests                ...
    pypi/requests-toolbelt       ...
    pypi/setuptools              ...
    pypi/six                     ...
    pypi/tensorflow              ...
    pypi/tensorflow-tensorboard  ...
    pypi/tqdm                    ...
    pypi/twine                   ...
    pypi/urllib3                 ...
    pypi/wheel                   ...
    <exit 0>

    """
    rundoc()

def install_mnist_packages_test():
    """Installs Guild and PyPI mnist packages.

    >>> run("$GUILD install mnist")
    Collecting gpkg.mnist
    ...
    Successfully installed gpkg.mnist-...
    <exit 0>

    >>> run("$GUILD install pypi/mnist")
    Collecting mnist
    ...
    Successfully installed mnist-...
    <exit 0>

    """
    rundoc()

def install_examples():
    """Installs the examples repo into the workspace."""
    run("git -C $WORKSPACE clone $EXAMPLES_REPO")

def no_cwd_modelfile_tests():
    """Various operations run in a directory that doesn't have models.

    Running an operation on a default model that doesn't exit:

    >>> run("$GUILD run train")
    guild: there are no models in the current directory
    Try a different directory or 'guild operations' for available operations.
    <exit 1>

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

    Train a model that doesn't exist:

    >>> run("$GUILD train foobar")
    guild: cannot find a model matching 'foobar'
    Try 'guild models' for a list of available models.
    <exit 1>

    Train with multiple model candidates:

    >>> run("$GUILD train mnist")
    guild: there are multiple models that match 'mnist'
    Try specifying one of the following:
      ./mnist-expert
      ./mnist-intro
    <exit 1>

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
    <exit 0>

    Running `runs` for a new project will return an empty
    list. Because there aren't any runs.

    >>> run("$GUILD runs")
    Limiting runs to the current directory (use --all to include all).
    <exit 0>

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
    <exit 0>

    """
    rundoc()

def mnist_single_run_tests():
    """Examines a project with a single run.

    We've just trained the intro model and have a single completed
    run:

    >>> run("$GUILD runs")
    Limiting runs to the current directory (use --all to include all).
    [0:...]  ./mnist-intro:train  ... ...  completed
    <exit 0>

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
    cmd_env = {}
    cmd_env.update(_globals_env())
    cmd_env["PATH"] = os.path.pathsep.join([
        os.path.join(WORKSPACE, "bin"),
        os.path.join(os.path.dirname(__file__), "../../bazel-bin/guild"),
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
    print(out.strip())
    print("<exit %i>" % exit_code)

def _globals_env():
    return {
        name: str(val)
        for name, val in globals().items()
        if isinstance(val, str)
    }

if __name__ == "__main__":
    main()
