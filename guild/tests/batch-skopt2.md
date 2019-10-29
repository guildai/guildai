# Batch runs - skopt 2

These tests cover various ranges of dimensions that are not covered by
`batch-skopt`. The tests use the `echo2.py` script in the `optimizers`
sample project.

TODO remove env on op2 promote.

    >>> project = Project(sample("projects", "optimizers"), env={"OP2": "1"})

A helper to run a batch:

    >>> def run(optimizer, max_trials=2, **flags):
    ...     project.run(
    ...         "echo2.py",
    ...         flags=flags,
    ...         optimizer=optimizer,
    ...         max_trials=max_trials,
    ...         simplify_trial_output=True)

Running with fixed args (i.e. no search ranges).

    >>> run("gp")
    ERROR: [guild] flags for batch (b=yes, f=2.0, i=3, s=hello) do
    not contain any search dimensions
    Try specifying a range for one or more flags as NAME=[MIN:MAX].
    <exit 1>

    >>> run("random")
    ERROR: [guild] flags for batch (b=yes, f=2.0, i=3, s=hello) do
    not contain any search dimensions
    Try specifying a range for one or more flags as NAME=[MIN:MAX].
    <exit 1>

    >>> run("forest")
    ERROR: [guild] flags for batch (b=yes, f=2.0, i=3, s=hello) do
    not contain any search dimensions
    Try specifying a range for one or more flags as NAME=[MIN:MAX].
    <exit 1>

    >>> run("gbrt")
    ERROR: [guild] flags for batch (b=yes, f=2.0, i=3, s=hello) do
    not contain any search dimensions
    Try specifying a range for one or more flags as NAME=[MIN:MAX].
    <exit 1>

Running with a single category for `i`:

    >>> run("gp", i=[3]) # doctest: +REPORT_UDIFF
    Random start for optimization (1 of 2)
    Running trial: echo2.py (b=yes, f=2.0, i=3, s=hello)
    i: 3
    f: 2.000000
    b: True
    s: hello
    loss: 1.000000
    Random start for optimization (2 of 2)
    Running trial: echo2.py (b=yes, f=2.0, i=3, s=hello)
    i: 3
    f: 2.000000
    b: True
    s: hello
    loss: 1.000000
