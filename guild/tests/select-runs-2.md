# Select Runs pt 2

These tests are a continuation of [`select-runs.md`](select-runs.md).

They also use the `optimizers` project example.

    >>> cd(sample("projects", "optimizers"))

Isolate runs:

    >>> set_guild_home(mkdtemp())

Generate some runs.

    >>> run("guild run echo2.py f=1.0 --run-id=1 -y")
    ???i: 3
    f: 1.000000
    b: True
    s: hello
    loss: 0.000000
    <exit 0>

    >>> run("guild run echo2.py f=2.0 --run-id=2 -y")
    i: 3
    f: 2.000000
    b: True
    s: hello
    loss: 1.000000
    <exit 0>

    >>> run("guild run echo2.py f=3.0 --run-id=3 -y")
    i: 3
    f: 3.000000
    b: True
    s: hello
    loss: 2.000000
    <exit 0>

    >>> run("guild runs")
    [1:3]  echo2.py  ...  completed  b=yes f=3.0 i=3 s=hello
    [2:2]  echo2.py  ...  completed  b=yes f=2.0 i=3 s=hello
    [3:1]  echo2.py  ...  completed  b=yes f=1.0 i=3 s=hello
    <exit 0>

Select all files (`--all` option added in 0.7.4):

    >>> run("guild select --all")
    3
    2
    1
    <exit 0>

Select min and max `loss` runs.

    >>> run("guild select --min loss")
    1
    <exit 0>

    >>> run("guild select --max loss")
    3
    <exit 0>

Select min and max `f` flag vals.

    >>> run("guild select --min =f")
    1
    <exit 0>

    >>> run("guild select --max =f")
    3
    <exit 0>

Select min and max run IDs.

    >>> run("guild select --min .id")
    1
    <exit 0>

    >>> run("guild select --max .id")
    3
    <exit 0>
