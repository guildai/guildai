# API Example

This test runs the Guild AI `api`.

    >>> cd(example("api"))

    >>> quiet("guild runs rm -y")

Generate some runs:

    >>> run("guild run op x=[1,2,3] -y")
    INFO: [guild] Running trial ...: op (x=1)
    loss: ...
    INFO: [guild] Running trial ...: op (x=2)
    loss: ...
    INFO: [guild] Running trial ...: op (x=3)
    loss: ...
    <exit 0>

Summarize the runs using a high min loss to ensure that all runs are
summarized:

    >>> run("guild run summary min-loss=999 -y")
    run operation             started     time     status label    x  step      loss
    0  ...        op ...  ...  completed   x=3  3.0     0  ...
    1  ...        op ...  ...  completed   x=2  2.0     0  ...
    2  ...        op ...  ...  completed   x=1  1.0     0  ...
    3  ...       op+ ...  ...  completed        NaN     0 ...
    <exit 0>

Filter by marked - should get no runs:

    >>> run("guild run summary min-loss=999 use-marked=yes -y")
    Empty DataFrame
    Columns: [run, operation, started, time, status, label]
    Index: []
    <exit 0>

Mark a run:

    >>> run("guild mark -Fo op 1 -y")
    Marked 1 run(s)
    <exit 0>

Filter again by marked - should get one run:

    >>> run("guild run summary min-loss=999 use-marked=yes -y")
    run operation             started     time     status label  x  step      loss
    0  ...        op ...  ...  completed   x=3  3     0  ...
    <exit 0>
