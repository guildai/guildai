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
@click.argument("filters", metavar="[FILTER]...", required=False, nargs=-1)
@click.option(
    "-a",
    "--all",
    is_flag=True,
    help="Show all models including those designated as private.",
)
@click.option(
    "-i",
    "--installed",
    is_flag=True,
    help=(
        "Include operations installed from packages when running "
        "command from a project directory."
    ),
)
@click.option("-v", "--verbose", help="Show model details.", is_flag=True)
@click_util.use_args
def models(args):
    """Show available models.

    If the current directory is a project directory (i.e. contains a
    Guild file), the command shows models defined for the
    project. Otherwise, the command shows models defined in installed
    packages.

    Note that model operations defined in packages are always
    available to run, even when running within a project directory. To
    always show installed models, use the `--installed` option.

    Use one or more `FILTER` arguments to show only models that match
    the specified values.

    """
    from . import models_impl

    models_impl.main(args)
