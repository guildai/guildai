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

from . import remote_support


def _ac_opspec(incomplete, ctx, **_kw):
    ops = _ac_operations(incomplete, ctx)
    if not incomplete and ops:
        return ops
    return ops + click_util.completion_filename()


def _ac_operations(incomplete, ctx, **_kw):
    from guild import cmd_impl_support
    from guild import _test
    from . import operations_impl

    ops_args = click_util.Args(installed=False, all=False, filters=[])

    def f():
        with _test.StderrCapture():
            cmd_impl_support.init_model_path()
            return [op["fullname"] for op in operations_impl.filtered_ops(ops_args)]

    ops = click_util.completion_safe_apply(ctx, f, [])
    if not ops:
        return []
    names = [op for op in ops if op.startswith(incomplete)]
    return click_util.completion_opnames(names)


def _ac_flag(incomplete, ctx, **_kw):
    if incomplete[:1] == "@":
        return _ac_batch_files()

    run_args = click_util.Args(**ctx.params)
    _ensure_log_init()
    opdef = _ac_opdef(run_args.opspec)
    if not opdef:
        return []

    if "=" in incomplete:
        return _ac_flag_choices(incomplete, opdef)

    used_flags = _ac_used_flags(run_args.flags, opdef)
    unused_flags = sorted([f.name for f in opdef.flags if f.name not in used_flags])
    flags_ac = [f for f in unused_flags if f.startswith(incomplete)]
    return ["%s=" % f for f in flags_ac] + click_util.completion_nospace()


def _ensure_log_init():
    from guild import log

    log.init_logging()


def _ac_batch_files():
    return click_util.completion_batchfile(ext=["csv", "yaml", "yml", "json"])


def _ac_opdef(opspec):
    import os
    from . import run_impl

    try:
        return run_impl.opdef_for_opspec(opspec)
    except (Exception, SystemExit):
        if os.getenv("_GUILD_COMPLETE_DEBUG") == "1":
            raise
        return None


def _ac_flag_choices(incomplete, opdef):
    flag_name, flag_val_incomplete = incomplete.split("=", 1)
    flagdef = opdef.get_flagdef(flag_name)
    if not flagdef or (not flagdef.choices and _maybe_filename_type(flagdef)):
        return click_util.completion_filename()
    choices = _flagdef_choices(flagdef)
    return [val for val in choices if val.startswith(flag_val_incomplete)]


def _maybe_filename_type(flagdef):
    assert flagdef
    return flagdef.type not in ("int", "float", "number", "boolean")


def _flagdef_choices(flagdef):
    if flagdef.choices:
        from guild import yaml_util

        return [yaml_util.encode_yaml(c.value) for c in flagdef.choices]
    elif flagdef.type == "boolean":
        return ["true", "false"]
    else:
        return []


def _ac_used_flags(flag_args, opdef):
    from . import run_impl

    flag_vals, _batch_files = run_impl.split_flag_args(flag_args, opdef)
    return flag_vals


def _ac_run(incomplete, ctx, **_kw):
    from guild import config
    from guild import var

    with config.SetGuildHome(ctx.parent.params.get("guild_home")):
        runs = var.runs(
            sort=["-timestamp"],
            filter=lambda r: r.id.startswith(incomplete),
        )
    return [run.id for run in runs]


def run_params(fn):
    click_util.append_params(
        fn,
        [
            click.Argument(
                ("flags",), metavar="[FLAG=VAL...]", nargs=-1, autocompletion=_ac_flag
            ),
            click.Option(
                ("-l", "--label"), metavar="LABEL", help="Set a label for the run."
            ),
            click.Option(
                ("-t", "--tag", "tags"),
                metavar="TAG",
                help="Associate TAG with run. May be used multiple times.",
                multiple=True,
            ),
            click.Option(
                ("-c", "--comment"),
                metavar="COMMENT",
                help="Comment associated with the run.",
            ),
            click.Option(
                ("-ec", "--edit-comment"),
                help="Use an editor to type a comment.",
                is_flag=True,
            ),
            click.Option(
                ("-e", "--edit-flags"),
                help="Use an editor to review and modify flags.",
                is_flag=True,
            ),
            click.Option(
                ("-d", "--run-dir"),
                metavar="DIR",
                autocompletion=click_util.completion_dir,
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
                autocompletion=_ac_run,
            ),
            click.Option(
                ("--proto",),
                metavar="RUN",
                help=(
                    "Use the operation, flags and source code from RUN. Flags may "
                    "be added or redefined in this operation. Cannot "
                    "be used with --restart."
                ),
                autocompletion=_ac_run,
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
                ("-bl", "--batch-label"),
                metavar="LABEL",
                help="Label to use for batch runs. Ignored for non-batch runs.",
            ),
            click.Option(
                ("-bt", "--batch-tag", "batch_tags"),
                metavar="TAG",
                help=(
                    "Associate TAG with batch. Ignored for non-batch runs. "
                    "May be used multiple times."
                ),
                multiple=True,
            ),
            click.Option(
                ("-bc", "--batch-comment"),
                metavar="COMMENT",
                help="Comment associated with batch.",
            ),
            click.Option(
                ("-ebc", "--edit-batch-comment"),
                help="Use an editor to type a batch comment.",
                is_flag=True,
            ),
            click.Option(
                ("-o", "--optimizer"),
                metavar="ALGORITHM",
                help=(
                    "Optimize the run using the specified algorithm. See "
                    "Optimizing Runs for more information."
                ),
            ),
            click.Option(
                ("-O", "--optimize"),
                is_flag=True,
                help="Optimize the run using the default optimizer.",
            ),
            click.Option(
                ("-N", "--minimize"),
                metavar="COLUMN",
                help=(
                    "Column to minimize when running with an optimizer. See "
                    "help for compare command for details specifying a column. "
                    "May not be used with --maximize."
                ),
            ),
            click.Option(
                ("-X", "--maximize"),
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
                ("-m", "--max-trials"),
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
                ("--stage-trials",),
                is_flag=True,
                help=("For batch operations, stage trials without running them."),
            ),
            remote_support.remote_option("Run the operation remotely."),
            click.Option(
                ("-y", "--yes"),
                help="Do not prompt before running operation.",
                is_flag=True,
            ),
            click.Option(
                ("-f", "--force-flags"),
                help=(
                    "Accept all flag assignments, even for undefined or "
                    "invalid values."
                ),
                is_flag=True,
            ),
            click.Option(
                ("--force-deps",),
                help=("Continue even when a required resource is not resolved."),
                is_flag=True,
            ),
            click.Option(
                ("--stop-after",),
                metavar="N",
                type=click_util.NUMBER,
                help="Stop operation after N minutes.",
            ),
            click.Option(
                ("--fail-on-trial-error",),
                is_flag=True,
                help="Stop batch operations when a trial exits with an error.",
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
                ("-b", "--background"),
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
                ("-n", "--no-wait"),
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
                autocompletion=click_util.completion_filename,
            ),
            click.Option(
                ("--break", "break_"),
                metavar="LOCATION",
                help=(
                    "Set a breakpoint at the specified location for Python based "
                    "operations. Set `LOCATION` to `1` to break at line 1 of the "
                    "main module. See Breakpoints above for `LOCATION` format. Use "
                    "multiple times for more than one breakpoint."
                ),
                multiple=True,
            ),
            click.Option(
                ("--break-on-error",),
                help=(
                    "Enter the Python debugger at the point an error occurs "
                    "for Python based operations."
                ),
                is_flag=True,
            ),
            click.Option(("-q", "--quiet"), help="Do not show output.", is_flag=True),
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
            click.Option(("--run-id",), hidden=True),
        ],
    )
    return fn


@click.command()
@click.argument(
    "opspec", metavar="[[MODEL:]OPERATION]", required=False, autocompletion=_ac_opspec
)
@run_params
@click_util.use_args
def run(args):
    """Run an operation.

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

    ### Breakpoints

    Use `--break` to set breakpoints for Python based operations.
    `LOCATION` may be specified as `[FILENAME:]LINE` or as
    `MODULE.FUNCTION`.

    If `FILENAME` is not specified, the main module is assumed. Use
    the value ``1`` to break at the start of the main module (line 1).

    Relative file names are resolved relative to the their location in
    the Python system path. You can omit the `.py` extension.

    If a line number does not correspond to a valid breakpoint, Guild
    attempts to set a breakpoint on the next valid breakpoint line in
    the applicable module.

    """
    from . import run_impl

    run_impl.main(args)
