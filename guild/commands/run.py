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
            ("-o", "--optimizer",), metavar="OPERATION",
            help=(
                "Optimize the run using OPERATION. See Optimizing "
                "Runs for more information.")),
        click.Option(
            ("--minimize",), metavar="COLUMN",
            help=(
                "Column to minimize when running with an optimizer. See "
                "help for compare command for details specifying a column. "
                "May not be used with --maximize.")),
        click.Option(
            ("--maximize",), metavar="COLUMN",
            help=(
                "Column to maximize when running with an optimizer. See "
                "help for compare command for details specifying a column. "
                "May not be used with --minimize.")),
        click.Option(
            ("--opt-flag", "opt_flags"), metavar="FLAG=VAL", multiple=True,
            help="Flag for OPTIMIZER. May be used multiple times."),
        click.Option(
            ("-r", "--remote"), metavar="REMOTE",
            help="Run the operation remotely."),
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
            ("--stop-after",), metavar="N", type=int,
            help="Stop operation after N minutes."),
        click.Option(
            ("--needed",), is_flag=True,
            help=(
                "Run only if there is not an available matching run. "
                "A matching run is of the same operation with the same "
                "flag values that is not stopped due to an error.")),
        click.Option(
            ("--pidfile",), metavar="PIDFILE",
            help=(
                "Run operation in background, writing the background process "
                "ID to PIDFILE.")),
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
            ("--print-trials",),
            help="Show generated trials and exit.",
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

@click_util.use_args

def run(args):
    """Run a model operation.

    By default Guild will try to run `OPERATION` for the default model
    defined in the current project.

    If `MODEL` is specified, Guild will use it instead of the default
    model.

    `OPERATION` may alternatively be a Python script. In this case any
    current project is ignored and the script is run directly. Options
    in the format ``--NAME=VAL`` can be passed to the script using
    flags (see below).

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

    ### Optimizing runs

    Use `--optimizer` to run the operation multiple times in attempt
    to optimize a result. Use `--minimize` or `--maximize` to indicate
    what should be optimized. Use `--max-runs` to indicate the maximum
    number of runs the optimizer should generate.
    """
    from . import run_impl
    run_impl.main(args)
