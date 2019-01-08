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
    "-r", "--requirement", metavar="REQ", multiple=True,
    help=(
        "Install required package or packages defined in a file. May be "
        "used multiple times."))
@click.option(
    "-P", "--path", metavar="DIR", multiple=True,
    help="Include DIR as a Python path in the environment.")
@click.option(
    "--no-reqs", is_flag=True,
    help=(
        "Don't install from requirements.txt or guild.yml in environment "
        "parent directory."))
@click.option(
    "--tensorflow", metavar="PACKAGE",
    help=(
        "Install PACKAGE for TensorFlow. By default installs the package "
        "suitable for the system based on GPU support."))
@click.option(
    "--skip-tensorflow", is_flag=True,
    help="Don't install TensorFlow.")
@click.option(
    "-l", "--local-resource-cache", is_flag=True,
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
    generated virtual environment. By default, the default Python
    interpreter for `virtualenv` is used unless `python` is explicitly
    listed as a requirement. If `no-venv` is specified, `--python` is
    ignored.

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

    ### Guild AI

    By default `init` installs the active version of Guild AI in the
    initialized environment. To install a different version, or to
    install a Guild wheel distribution file use the `--guild` option.

    ### TensorFlow

    TensorFlow is installed to the environment unless
    `--skip-tensorflow` is specified. The TensorFlow package to
    install can be specified using `--tensorflow`. By default, Guild
    installs the TensorFlow package suited for the system:
    ``tensorflow-gpu`` if a GPU is available, otherwise
    ``tensorflow``.

    ### Resource cache

    By default resources are cached and shared at the user level in
    `~/.guild/cache/resources` so that resources downloaded from one
    environment are available to other environments. You can modify
    this behavior to have all resources downloaded local to the
    environment by specifying `--local-resource-cache`.

    """
    from . import init_impl
    init_impl.main(args)
