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
    "--venv", "type", flag_value="venv", default=True,
    help="Use virtualenv to create a virtual environment (default).")
@click.option(
    "--no-venv", "type", flag_value="none",
    help="Do not create a virtual environment.")
@click.option(
    "--python", metavar="PYTHON_EXE",
    help="The Python interpreter to use within a virtual environment.")
@click.option(
    "--yes", is_flag=True,
    help="Initialize a Guild environment without prompting.")

@click.pass_context
@click_util.use_args

def init2(ctx, args):
    """Alternative init command.

    `init2` initializes a Guild environment in `DIR`, which is the
    current directory by default.

    ### Virtual environments

    By default `init2` creates a virtual environment in `DIR` using
    `virtualenv`. You may skip the creation of a virtual environment
    by specifying `no-venv`.

    Use `--python` to specify the Python interpreter to use within the
    generated virtual environment. If `no-venv` is specified,
    `--python` is ignored.

    """
    from . import init2_impl
    init2_impl.main(args, ctx)
