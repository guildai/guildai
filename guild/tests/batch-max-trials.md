# Batch max trials

    >>> project = Project(sample("projects", "max-trials"))

A helper:

    >>> def last_run_max_trials():
    ...     return project.list_runs()[0].get("max_trials")

Optimizer (batch) operations may define default max trials via a
`max_trials` flag default.

The `opt-1` operation doesn't define a `max_trials` attribute.

    >>> project.run("op", optimizer="opt-1")
    >>> print(last_run_max_trials())
    None

The `opt-2` operation defined `max_trials` with a default of 5.

    >>> project.run("op", optimizer="opt-2")
    >>> last_run_max_trials()
    5

We can explicitly set the number of max trials.

    >>> project.run("op", optimizer="opt-1", max_trials=1)
    >>> last_run_max_trials()
    1

When we restart a run, the last max trials is preserved.

    >>> project.run(restart=project.list_runs()[0].id)
    >>> last_run_max_trials()
    1

We can redefine the max trials on a restart.

    >>> project.run(restart=project.list_runs()[0].id, max_trials=2)
    >>> last_run_max_trials()
    2

Max trials for non-batch runs aren't saved.

    >>> project.run("op")
    >>> print(last_run_max_trials())
    None

Neither are they for batch protos.

    >>> project.run("op", optimize=True, max_trials=10)

Note that we used the `optimize` flag rather than specify an optimizer
operation. The `op` operation defines the optimizers it supports and
Guild selects the default optimizer. In this cases it's the optimizer
with the lowest lexicographic value for name.

    >>> last_run = project.list_runs()[0]
    >>> last_run.opref.to_opspec()
    'opt-1'

The optimizer run has max trials.

    >>> last_run.get("max_trials")
    10

However, it's run proto does not.

    >>> print(last_run.batch_proto.get("max_trials"))
    None

Built-in optimizers define their own default max trials.

    >>> from guild import op_util

Here's the random optimizer:

    >>> random_opdef = op_util.opdef_for_opspec("random")

They provide the value as via a `default_max_trials` attribute.

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

## Max trials and default batch ops

Default batch ops generate as many trials as needed based on flag
values.

    >>> project.run("op", flags={"x": "range[1:30]"})
    INFO: [guild] Running trial ...: op (x=1)
    INFO: [guild] Running trial ...: op (x=2)
    ...
    INFO: [guild] Running trial ...: op (x=30)

## Warnings

Run a non-batch specifying `max_trials`.

    >>> project.run("op", max_trials=1)
    WARNING: not a batch run - ignoring --max-trials
