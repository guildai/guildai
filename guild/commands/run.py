# Copyright 2017 TensorHub, Inc.
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

def run_params(fn):
    click_util.append_params(fn, [
        click.Argument(("args",), metavar="[ARG...]", nargs=-1),
        click.Option(
            ("-p", "--project", "project_location"), metavar="LOCATION",
            help="Project location (file system directory) for MODEL."),
        click.Option(
            ("--disable-plugins",), metavar="LIST",
            help=("A comma separated list of plugin names to disable. "
                  "Use 'all' to disable all plugins.")),
        click.Option(
            ("-y", "--yes"),
            help="Do not prompt before running operation.",
            is_flag=True),
        click.Option(
            ("--print-cmd",),
            help="Show the operation command and exit (does not run).",
            is_flag=True),
        click.Option(
            ("--print-env",),
            help="Show the operation environment and exit (does not run).",
            is_flag=True),
    ])
    return fn

@click.command()
@click.argument("opspec", metavar="[MODEL:]OPERATION")
@run_params

@click_util.use_args

def run(args):
    """Run a model operation.

    By default Guild will try to run OPERATION for the default model
    defined in a project. If a project location is not specified (see
    --project option below), Guild looks for a project in the current
    directory.

    If MODEL is specified, Guild will use it instead of the default
    model defined in a project.
    """
    from . import run_impl
    run_impl.main(args)
