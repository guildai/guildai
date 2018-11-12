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
        click.Argument(("flags",), metavar="[FLAG=VAL...]", nargs=-1),
        click.Option(
            ("-l", "--label"), metavar="LABEL",
            help="Set a label for the run."),
        click.Option(
            ("-d", "--run-dir",), metavar="DIR",
            help=(
                "Use alternative run directory DIR. Cannot be used with "
                "--stage.")),
        click.Option(
            ("--stage",), metavar="DIR",
            help=(
                "Stage an operation in DIR but do not run. Cannot be used "
                "with --run-dir.")),
        click.Option(
            ("--rerun",), metavar="RUN",
            help=(
                "Use the operation and flags from RUN. Flags may "
                "be added or redefined in this operation. Cannot "
                "be used with --restart.")),
        click.Option(
            ("-r", "--remote"), metavar="REMOTE",
            help="Run the operation remotely."),
        click.Option(
            ("--restart",), metavar="RUN",
            help=(
                "Restart RUN in-place without creating a new run. Cannot be "
                "used with --rerun or --run-dir.")),
        click.Option(
            ("--disable-plugins",), metavar="LIST",
            help=("A comma separated list of plugin names to disable. "
                  "Use 'all' to disable all plugins.")),
        click.Option(
            ("--gpus",), metavar="DEVICES",
            help=("Limit availabe GPUs to DEVICES, a comma separated list of "
                  "device IDs. By default all GPUs are available. Cannot be"
                  "used with --no-gpus.")),
        click.Option(
            ("--no-gpus",), is_flag=True,
            help="Disable GPUs for run. Cannot be used with --gpu."),
        click.Option(
            ("-y", "--yes"),
            help="Do not prompt before running operation.",
            is_flag=True),
        click.Option(
            ("-f", "--force-flags"),
            help=(
                "Accept all flag assignments, even for undefined or "
                "invalid flags."),
            is_flag=True),
        click.Option(
            ("--background",), metavar="PIDFILE",
            help=(
                "Run operation in background. PIDFILE must be a path to a "
                "file where the background process ID is written.")),
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
            ("-q", "--quiet",),
            help="Do not show output.",
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
        click.Option(
            ("-w", "--workflow"),
            help="Experimental support for workflow.",
            is_flag=True,
            hidden=True)
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

    Specify `FLAG` values in the form `FLAG=VAL`.

    ### Re-running operations

    If `--rerun` is specified, the operation and flags used in `RUN`
    will be applied to the new operation. You may add or redefine
    flags in the new operation. You may also use an alternative
    operation, in which case only the flag values from `RUN` will be
    applied. `RUN` must be a run ID or unique run ID prefix or the
    special value ``0``, which indicates the latest run.

    ### Restarting operations

    If `--restart` is specified, the specified `RUN` is restarted
    in-place using its operation and flags. Unlike rerun, restart does
    not create a new run, but instead reuses the run directory of
    `RUN`. Like a rerun, a restart may specify a different operation
    and additional flags and may use ``0`` for the value of `RUN` to
    restart the latest run. `--run-dir` may not be used with
    `--restart`.

    `--rerun` and `--restart` may not both be used.

    ### Alternate run directory

    To run an operation outside of Guild's run management facility,
    use `--run-dir` or `--stage` to specify an alternative run
    directory. These options are useful when developing or debugging
    an operation. Use `--stage` to prepare a run directory for an
    operation without running the operation itself. This is useful
    when you want to verify dependency resolution and pre-processing
    or manually run an operation in a prepared directory.

    **NOTE:** Runs started with `--run-dir` are not visible to Guild
    and will not appear in run listings.

    ### Controlling visible GPU devices

    By default, operations have access to all available GPU
    devices. To limit the GPU devices available to a run, use
    `--gpus`.

    For example, to limit visible GPU devices to `0` and `1`, run:

        guild run --gpus 0,1 ...

    To disable all available GPUs, use `--no-gpus`.

    **NOTE:** `--gpus` and `--no-gpus` are used to construct the
    `CUDA_VISIBLE_DEVICES` environment variable used for the run
    process. If `CUDA_VISIBLE_DEVICES` is set, using either of these
    options will cause it to be redefined for the run.

    """
    from . import run_impl
    run_impl.main(args, ctx)
