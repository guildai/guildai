# Batch max trials

These tests demonstrate Guild's support of max trials.

    >>> use_project("max-trials")

Optimizer (batch) operations may define default max trials using
`default-max-trials` for the operation. This value is used when
determining the maximum trials run for a batch when `--max-trials` is
not specified in the `run` command.

`opt-1` does not define `default-max-trials`. When we use it for a
batch run, the max trials attribute is unspecified (null).

    >>> run("guild run op --optimizer opt-1 -y")
    <exit 0>

    >>> run("guild runs -s")
    [1]  op+opt-1  completed

    >>> run("guild select --attr max_trials")
    guild: no such run attribute 'max_trials'
    <exit 1>

`opt-2` operation defines `default-max-trials` as 5. This is used when
`--max-trials` is not specified for the `run` command.

    >>> run("guild run op --optimizer opt-2 -y")
    <exit 0>

    >>> run("guild select --attr max_trials")
    5

When we specify `--max-trials` for the `run` command, that value is
used instead of the default.

    >>> run("guild run op -o opt-1 --max-trials 1 -y")
    <exit 0>

    >>> run("guild select --attr max_trials")
    1

When we restart a run, the last max trials is preserved.

    >>> last_run = run_capture("guild select")

    >>> run(f"guild run --restart {last_run} -y")
    <exit 0>

    >>> run("guild select --attr max_trials")
    1

We can redefine the max trials on a restart.

    >>> run(f"guild run --restart {last_run} --max-trials 2 -y")
    <exit 0>

    >>> run("guild select --attr max_trials")
    2

Max trials for non-batch runs aren't saved.

    >>> run("guild run op -y")
    <exit 0>

    >>> run("guild select --attr max_trials")
    guild: no such run attribute 'max_trials'
    <exit 1>

    >>> run("guild run op --max-trials 3 -y")
    WARNING: not a batch run - ignoring --max-trials

    >>> run("guild select --attr max_trials")
    guild: no such run attribute 'max_trials'
    <exit 1>

## Built-in optimizers

Built-in optimizers define their own default max trials.

    >>> from guild import op_util

The 'random' optimizer defines a default max trials of 20.

    >>> random_opdef = op_util.opdef_for_opspec("random")
    >>> random_opdef.default_max_trials
    20

The default batch (grid) optimizer is None. This means that there is
no limit - the total generated trials list is used without sampling.

    >>> batch_opdef = op_util.opdef_for_opspec("+")
    >>> print(batch_opdef.default_max_trials)
    None

Other optimizers:

    >>> op_util.opdef_for_opspec("gp").default_max_trials
    20

    >>> op_util.opdef_for_opspec("forest").default_max_trials
    20

    >>> op_util.opdef_for_opspec("gbrt").default_max_trials
    20

## Max trials and default batches

Default batches generate as many trials as needed based on flag
values.

    >>> run("guild run op x=range[1:30] -y")
    INFO: [guild] Running trial ...: op (x=1)
    INFO: [guild] Running trial ...: op (x=2)
    ...
    INFO: [guild] Running trial ...: op (x=30)
