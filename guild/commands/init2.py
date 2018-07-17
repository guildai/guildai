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
    "--python", metavar="VERSION",
    help="The version of Python to use within a virtual environment.")
@click.option(
    "-r", "--requirement", metavar="FILE", multiple=True,
    help="Install packages defined in FILE. May be used multiple times.")
@click.option(
    "--no-reqs", is_flag=True,
    help="Don't install from requirements.txt in environment parent directory.")
@click.option(
    "-y", "--yes", is_flag=True,
    help="Initialize a Guild environment without prompting.")

@click.pass_context
@click_util.use_args

def init2(ctx, args):
    """Alternative init command.

    `init2` initializes a Guild environment in `DIR`, which is the
    current directory by default.

    `init2` creates a virtual environment in `DIR` using `virtualenv`.

    Use `--python` to specify the Python interpreter to use within the
    generated virtual environment. If `no-venv` is specified,
    `--python` is ignored.

    The environment may be initialized with packages defined in Python
    requirements files. For information in requirements files, see:

    https://pip.readthedocs.io/en/1.1/requirements.html

    By default, packages defined in `requirements.txt` in the
    environment parent directory will be installed. Use `--no-reqs` to
    surppress this behavior.

    You may explicitly specify requirements file using `-r` or
    `--requirement`.

    """
    from . import init2_impl
    init2_impl.main(args, ctx)
