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

import click

from guild import click_util

@click.command()
@click.argument("dir", default="env")
@click.option(
    "-n", "--name", metavar="NAME",
    help="Environment name (default is env parent directory name).")
@click.option(
    "-p", "--python", metavar="VERSION",
    help="Version of Python to use for the environment.")
@click.option(
    "-g", "--guild", metavar="VERSION_OR_PATH",
    help=(
        "Version of Guild AI to use for the environment. "
        "By default, the active version of Guild is installed. This "
        "value may alternatively be a path to a Guild wheel distribution.")
    )
@click.option(
    "--gpu", "tf_package", flag_value="tensorflow-gpu",
    help="Use the GPU enabled tensorflow package for the environment.")
@click.option(
    "--no-gpu", "tf_package", flag_value="tensorflow",
    help="Use the non-GPU tensorflow package for the environment.")
@click.option(
    "--no-tensorflow", "tf_package", flag_value="no",
    help="Do not install TensorFlow in the environment.")
@click.option(
    "-r", "--requirement", metavar="FILE", multiple=True,
    help="Install packages defined in FILE. May be used multiple times.")
@click.option(
    "-P", "--path", metavar="DIR", multiple=True,
    help="Include DIR as a Python path in the environment.")
@click.option(
    "--no-reqs", is_flag=True,
    help=(
        "Don't install from requirements.txt or guild.yml in environment "
        "parent directory."))
@click.option(
    "--local-resource-cache", is_flag=True,
    help="Use a local cache when initializing an environment.")
@click.option(
    "-y", "--yes", is_flag=True,
    help="Initialize a Guild environment without prompting.")
@click.option(
    "--no-progress", is_flag=True,
    help="Don't show progress when installing environment packages.")

@click_util.use_args

def init(args):
    """Initialize a Guild environment.

    `init` initializes a Guild environment in `DIR`, which is the
    current directory by default.

    `init` creates a virtual environment in `DIR` using `virtualenv`.

    Use `--python` to specify the Python interpreter to use within the
    generated virtual environment. If `no-venv` is specified,
    `--python` is ignored.

    ### Requirements

    By default, any required packages listed under packages.requires
    in `guild.yml` in the environment parent directory are installed
    into the environment. Use `--no-reqs` to suppress this behavior.

    Additionally, packages defined in `requirements.txt` in the
    environment parent directory will be installed. Use `--no-reqs` to
    suppress this behavior.

    Note that packages defined in `guild.yml` use Guild package names
    while packages defined in `requirements.txt` use PyPI package
    names.

    For information in requirements files, see:

    https://pip.readthedocs.io/en/1.1/requirements.html

    You may explicitly specify requirements file using `-r` or
    `--requirement`. If `-r, --requirement` is specified, Guild will
    not automatically install packages in `requirements.txt` -- that
    file must be specified explicitly in the command.

    ### TensorFlow

    By default `init` installs TensorFlow in the initialized
    environment if it's not already installed. When Guild installs
    TensorFlow, it detects GPU support on the system and selects the
    appropriate package: `tensorflow-gpu` for GPU support, otherwise
    `tensorflow`.

    To override the default package, use `--gpu` to install the
    `tensorflow-gpu` package or `--no-gpu` to install the `tensorflow`
    package.

    To skip installing TensorFlow, use `--no-tensorflow`.

    If TensorFlow was installed by way of a requirements file, either
    `requirements.txt` located in the environment parent directory or
    a file specified by a `--requirement` option, Guild will not
    reinstall it.

    ### Guild AI

    By default `init` installs the active version of Guild AI in the
    initialized environment. To install a different version, or to
    install a Guild wheel distribution file use the `--guild` option.

    ### Resource cache

    By default resources are cached and shared at the user level in
    `~/.guild/cache/resources` so that resources downloaded from one
    environment are available to other environments. You can modify
    this behavior to have all resources downloaded local to the
    environment by specifying `--local-resource-cache`.

    """
    from . import init_impl
    init_impl.main(args)
