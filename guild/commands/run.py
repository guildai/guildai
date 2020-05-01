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


def run_params(fn):
    click_util.append_params(
        fn,
        [
            click.Argument(("flags",), metavar="[FLAG=VAL...]", nargs=-1),
            click.Option(
                ("-l", "--label"), metavar="LABEL", help="Set a label for the run."
            ),
            click.Option(
                ("-t", "--tag"),
                metavar="TAG",
                help="Prepend TAG to the default label. Cannot be used with --label.",
            ),
            click.Option(
                ("-e", "--edit-flags"),
                help="Use an editor to review and modify flags.",
                is_flag=True,
            ),
            click.Option(
                ("-d", "--run-dir",),
                metavar="DIR",
                help=(
                    "Use alternative run directory DIR. Cannot be used with --stage."
                ),
            ),
            click.Option(("--stage",), help="Stage an operation.", is_flag=True),
            click.Option(
                ("--start", "--restart", "restart"),
                metavar="RUN",
                help=(
                    "Start a staged run or restart an existing run. Cannot be "
                    "used with --proto or --run-dir."
                ),
            ),
            click.Option(
                ("--proto",),
                metavar="RUN",
                help=(
                    "Use the operation, flags and source code from RUN. Flags may "
                    "be added or redefined in this operation. Cannot "
                    "be used with --restart."
                ),
            ),
            click.Option(
                ("--force-sourcecode",),
                is_flag=True,
                help=(
                    "Use working source code when --restart or --proto is specified. "
                    "Ignored otherwise."
                ),
            ),
            click.Option(
                ("--gpus",),
                metavar="DEVICES",
                help=(
                    "Limit availabe GPUs to DEVICES, a comma separated list of "
                    "device IDs. By default all GPUs are available. Cannot be"
                    "used with --no-gpus."
                ),
            ),
            click.Option(
                ("--no-gpus",),
                is_flag=True,
                help="Disable GPUs for run. Cannot be used with --gpu.",
            ),
            click.Option(
                ("-bl", "--batch-label",),
                metavar="LABEL",
                help="Label to use for batch runs. Ignored for non-batch runs.",
            ),
            click.Option(
                ("-bt", "--batch-tag",),
                metavar="TAG",
                help="Tag to use for batch runs. Ignored for non-batch runs.",
            ),
            click.Option(
                ("-o", "--optimizer",),
                metavar="ALGORITHM",
                help=(
                    "Optimize the run using the specified algorithm. See "
                    "Optimizing Runs for more information."
                ),
            ),
            click.Option(
                ("-O", "--optimize",),
                is_flag=True,
                help="Optimize the run using the default optimizer.",
            ),
            click.Option(
                ("-N", "--minimize",),
                metavar="COLUMN",
                help=(
                    "Column to minimize when running with an optimizer. See "
                    "help for compare command for details specifying a column. "
                    "May not be used with --maximize."
                ),
            ),
            click.Option(
                ("-X", "--maximize",),
                metavar="COLUMN",
                help=(
                    "Column to maximize when running with an optimizer. See "
                    "help for compare command for details specifying a column. "
                    "May not be used with --minimize."
                ),
            ),
            click.Option(
                ("-Fo", "--opt-flag", "opt_flags"),
                metavar="FLAG=VAL",
                multiple=True,
                help="Flag for OPTIMIZER. May be used multiple times.",
            ),
            click.Option(
                ("-m", "--max-trials",),
                metavar="N",
                type=click.IntRange(1, None),
                help=(
                    "Maximum number of trials to run in batch operations. "
                    "Default is optimizer specific. If optimizer is not "
                    "specified, default is 20."
                ),
            ),
            click.Option(
                ("--random-seed",),
                metavar="N",
                type=int,
                help="Random seed used when sampling trials or flag values.",
            ),
            click.Option(
                ("--debug-sourcecode",),
                metavar="PATH",
                help=(
                    "Specify an alternative source code path for debugging. "
                    "See Debug Source Code below for details."
                ),
            ),
            click.Option(
                ("--init-trials", "--stage-trials"),
                is_flag=True,
                # TODO: clean this up - we have --stage now, which is
                # what we're using to stage trials. This should be
                # deleted but we need to make sure it doesn't break
                # anything.
                hidden=True,
                help=("For batch operations, initialize trials without running them."),
            ),
            click.Option(
                ("-r", "--remote"), metavar="REMOTE", help="Run the operation remotely."
            ),
            click.Option(
                ("-y", "--yes"),
                help="Do not prompt before running operation.",
                is_flag=True,
            ),
            click.Option(
                ("-f", "--force-flags"),
                help=(
                    "Accept all flag assignments, even for undefined or "
                    "invalid flags."
                ),
                is_flag=True,
            ),
            click.Option(
                ("--stop-after",),
                metavar="N",
                type=click_util.NUMBER,
                help="Stop operation after N minutes.",
            ),
            click.Option(
                ("--needed",),
                is_flag=True,
                help=(
                    "Run only if there is not an available matching run. "
                    "A matching run is of the same operation with the same "
                    "flag values that is not stopped due to an error."
                ),
            ),
            click.Option(
                ("-b", "--background",),
                is_flag=True,
                help="Run operation in background.",
            ),
            click.Option(
                ("--pidfile",),
                metavar="PIDFILE",
                help=(
                    "Run operation in background, writing the background process "
                    "ID to PIDFILE."
                ),
            ),
            click.Option(
                ("-n", "--no-wait",),
                help=(
                    "Don't wait for a remote operation to complete. Ignored "
                    "if run is local."
                ),
                is_flag=True,
            ),
            click.Option(
                ("--save-trials",),
                metavar="PATH",
                help=(
                    "Saves generated trials to a CSV batch file. See BATCH FILES "
                    "for more information."
                ),
            ),
            click.Option(
                ("--set-trace",),
                help="Enter the Python debugger at the operation entry point.",
                is_flag=True,
            ),
            click.Option(("-q", "--quiet",), help="Do not show output.", is_flag=True),
            click.Option(
                ("--print-cmd",), help="Show operation command and exit.", is_flag=True
            ),
            click.Option(
                ("--print-env",),
                help="Show operation environment and exit.",
                is_flag=True,
            ),
            click.Option(
                ("--print-trials",),
                help="Show generated trials and exit.",
                is_flag=True,
            ),
            click.Option(
                ("--help-model",), help="Show model help and exit.", is_flag=True
            ),
            click.Option(
                ("-h", "--help-op"), help="Show operation help and exit.", is_flag=True
            ),
            click.Option(
                ("--test-output-scalars",),
                metavar="OUTPUT",
                help=(
                    "Test output scalars on output. Use '-' to read from standard "
                    "intput."
                ),
            ),
            click.Option(
                ("--test-sourcecode",), help="Test source code selection.", is_flag=True
            ),
            click.Option(
                ("--test-flags",), help="Test flag configuration.", is_flag=True
            ),
        ],
    )
    return fn


@click.command()
@click.argument("opspec", metavar="[[MODEL:]OPERATION]", required=False)
@run_params
@click_util.use_args
def run(args):
    """Run a model operation.

    By default Guild tries to run `OPERATION` for the default model
    defined in the current project.

    If `MODEL` is specified, Guild uses it instead of the default
    model.

    `OPERATION` may alternatively be a Python script. In this case any
    current project is ignored and the script is run directly. Options
    in the format ``--NAME=VAL`` can be passed to the script using
    flags (see below).

    `[MODEL]:OPERATION` may be omitted if `--restart` or `--proto` is
    specified, in which case the operation used in `RUN` is used.

    Specify `FLAG` values in the form `FLAG=VAL`.

    ### Batch Files

    One or more batch files can be used to run multiple trials by
    specifying the file path as `@PATH`.

    For example, to run trials specified in a CSV file named
    `trials.csv`, run:

        guild run [MODEL:]OPERATION @trials.csv

    NOTE: At this time you must specify the operation with batch files
    - batch files only contain flag values and cannot be used to run
    different operations for the same command.

    Batch files may be formatted as CSV, JSON, or YAML. Format is
    determined by the file extension.

    Each entry in the file is used as a set of flags for a trial run.

    CSV files must have a header row containing the flag names. Each
    subsequent row is a corresponding list of flag values that Guild
    uses for a generated trial.

    JSON and YAML files must contain a top-level list of flag-to-value
    maps.

    Use `--print-trials` to preview the trials run for the specified
    batch files.

    ### Flag Lists

    A list of flag values may be specified using the syntax
    `[VAL1[,VAL2]...]`. Lists containing white space must be
    quoted. When a list of values is provided, Guild generates a trial
    run for each value. When multiple flags have list values, Guild
    generates the cartesian product of all possible flag combinations.

    Flag lists may be used to perform grid search operations.

    For example, the following generates four runs for operation
    `train` and flags `learning-rate` and `batch-size`:

        guild run train learning-rate[0.01,0.1] batch-size=[10,100]

    You can preview the trials generated from flag lists using
    `--print-trials`. You can save the generated trials to a batch
    file using `--save-trials`. For more information, see PREVIEWING
    AND SAVING TRIALS below.

    When `--optimizer` is specified, flag lists may take on different
    meaning depending on the type of optimizer. For example, the
    `random` optimizer randomly selects values from a flag list,
    rather than generate trials for each value. See OPTIMIZERS for
    more information.

    ### Optimizers

    A run may be optimized using `--optimizer`. An optimizer runs up
    to `--max-trials` runs using flag values and flag configuration.

    For details on available optimizers and their behavior, refer to
    https://guild.ai/optimizers/.

    ### Limit Trials

    When using flag lists or optimizers, which generate trials, you
    can limit the number of trials with `--max-trials`. By default,
    Guild limits the number of generated trials to 20.

    Guild limits trials by randomly sampling the maximum number from
    the total list of generated files. You can specify the seed used
    for the random sample with `--random-seed`. The random seed is
    guaranteed to generate consistent results when used on the same
    version of Python. When used across different versions of Python,
    the results may be inconsistent.

    ### Preview or Save Trials

    When flag lists (used for grid search) or an optimizer is used,
    you can preview the generated trials using `--print-trials`. You
    can save the generated trials as a CSV batch file using
    `--save-trials`.

    ### Start an Operation Using a Prototype Run

    If `--proto` is specified, Guild applies the operation, flags, and
    source code used in `RUN` to the new operation. You may add or
    redefine flags in the new operation. You may use an alternative
    operation, in which case only the flag values and source code from
    `RUN` are applied. `RUN` must be a run ID or unique run ID prefix.

    ### Restart an Operation

    If `--restart` is specified, `RUN` is restarted using its
    operation and flags. Unlike `--proto`, restart does not create a
    new run. You cannot change the operation, flags, source code, or
    run directory when restarting a run.

    ### Staging an Operation

    Use `--stage` to stage an operation to be run later. Use `--start`
    with the staged run ID to start it.

    If `--start` is specified, `RUN` is started using the same rules
    applied to `--restart` (see above).

    ### Alternate Run Directory

    To run an operation outside of Guild's run management facility,
    use `--run-dir` or `--stage-dir` to specify an alternative run
    directory. These options are useful when developing or debugging
    an operation. Use `--stage-dir` to prepare a run directory for an
    operation without running the operation itself. This is useful
    when you want to verify run directory layout or manually run an
    operation in a prepared directory.

    **NOTE:** Runs started with `--run-dir` are not visible to Guild
    and do not appear in run listings.

    ### Control Visible GPUs

    By default, operations have access to all available GPU
    devices. To limit the GPU devices available to a run, use
    `--gpus`.

    For example, to limit visible GPU devices to `0` and `1`, run:

        guild run --gpus 0,1 ...

    To disable all available GPUs, use `--no-gpus`.

    **NOTE:** `--gpus` and `--no-gpus` are used to construct the
    `CUDA_VISIBLE_DEVICES` environment variable used for the run
    process. If `CUDA_VISIBLE_DEVICES` is set, using either of these
    options redefines that environment variable for the run.

    ### Optimize Runs

    Use `--optimizer` to run the operation multiple times in attempt
    to optimize a result. Use `--minimize` or `--maximize` to indicate
    what should be optimized. Use `--max-runs` to indicate the maximum
    number of runs the optimizer should generate.

    ### Edit Flags

    Use `--edit-flags` to use an editor to review and modify flag
    values. Guild uses the editor defined in `VISUAL` or `EDITOR`
    environment variables. If neither environment variable is defined,
    Guild uses an editor suitable for the current platform.

    ### Debug Source Code

    Use `--debug-sourcecode` to specify the location of project source
    code for debugging. Guild uses this path instead of the location
    of the copied soure code for the run. For example, when debugging
    project files, use this option to ensure that modules are loaded
    from the project location rather than the run directory.

    """
    from . import run_impl

    run_impl.main(args)
