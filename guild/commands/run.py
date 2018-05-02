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

def run_params(fn):
    click_util.append_params(fn, [
        click.Argument(("args",), metavar="[ARG...]", nargs=-1),
        click.Option(
            ("-l", "--label"), metavar="LABEL",
            help="Set a label for the run."),
        click.Option(
            ("-d", "--run-dir"), metavar="DIR",
            help="Use an alternative run directory."),
        click.Option(
            ("-r", "--rerun",), metavar="RUN",
            help=(
                "Use the operation and flags from RUN. Flags may "
                "be added or redefined in this operation. Cannot "
                "be used with --restart.")),
        click.Option(
            ("-s", "--restart",), metavar="RUN",
            help=(
                "Restart RUN in-place without creating a new run. Cannot be "
                "used with --rerun or --run-dir.")),
        click.Option(
            ("--no-deps",),
            help="Don't resolve dependencies",
            is_flag=True),
        click.Option(
            ("--disable-plugins",), metavar="LIST",
            help=("A comma separated list of plugin names to disable. "
                  "Use 'all' to disable all plugins.")),
        click.Option(
            ("-y", "--yes"),
            help="Do not prompt before running operation.",
            is_flag=True),
        click.Option(
            ("-n", "--no-wait",),
            help=("Don't wait for a remote operation to complete. Ignored "
                  "if run is local."),
            is_flag=True),
        click.Option(
            ("--set-trace",),
            help="Enter the Python debugger at the operation entry point.",
            is_flag=True),
        click.Option(
            ("--print-cmd",),
            help="Show operation command and exit.",
            is_flag=True),
        click.Option(
            ("--print-env",),
            help="Show operation environment and exit.",
            is_flag=True),
        click.Option(
            ("--help-model",),
            help="Show model help and exit.",
            is_flag=True),
        click.Option(
            ("--help-op",),
            help="Show operation help and exit.",
            is_flag=True),
    ])
    return fn

@click.command()
@click.argument("opspec", metavar="[[MODEL:]OPERATION]", required=False)
@run_params

@click.pass_context
@click_util.use_args

def run(ctx, args):
    """Run a model operation.

    By default Guild will try to run `OPERATION` for the default model
    defined in a project. If a project location is not specified (see
    `--project` option below), Guild looks for a project in the
    current directory.

    If `MODEL` is specified, Guild will use it instead of the default
    model defined in a project.

    `[MODEL]:OPERATION` may be omitted if `--rerun` is specified, in
    which case the operation used in `RUN` will be used.

    If `--rerun` is specified, the operation and flags used in `RUN`
    will be applied to the new operation. You may add or redefine
    flags in the new operation. You may also use an alternative
    operation, in which case only the flag values from `RUN` will be
    applied. `RUN` must be a run ID or unique run ID prefix or the
    special value ``0``, which indicates the latest run.

    If `--restart` is specified, the specified `RUN` is restarted
    in-place using its operation and flags. Unlike rerun, restart does
    not create a new run, but instead reuses the run directory of
    `RUN`. Like a rerun, a restart may specify a different operation
    and additional flags and may use ``0`` for the value of `RUN` to
    restart the latest run. `--run-dir` may not be used with
    `--restart`.

    `--rerun` and `--restart` may not both be used.

    """
    from . import run_impl
    run_impl.main(args, ctx)
