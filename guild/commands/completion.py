# Copyright 2017-2020 TensorHub, Inc.
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
@click.option(
    "-s",
    "--shell",
    metavar="NAME",
    type=click.Choice(["bash", "zsh", "fish"]),
    help=(
        "Shell to generate completion script for (choice of bash, zsh, fish). "
        "Default is current shell."
    ),
)
@click.option(
    "--shell-init",
    metavar="PATH",
    help=("Path to shell initrc to modify when --install is specified."),
)
@click.option(
    "-i",
    "--install",
    is_flag=True,
    help="Install the completion script for use whenever you open a terminal.",
)
@click_util.use_args
def completion(args):
    """Generate command completion script.

    By default generates a completion script for the active shell. To
    specify a different shell, use `--shell`.
    """

    from . import completion_impl

    completion_impl.main(args)
