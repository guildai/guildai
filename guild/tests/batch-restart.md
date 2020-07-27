# Batch runs - restarting

This test illustrates how a random optimized batch handles restarts.

In early versions of Guild, batch runs had a complex restart logic
that extended restarts into previously run trials. Guild now simply
re-runs the batch operation, which generated new runs.

If a user wants to restart batch trials, she can do so explicitly, per
trial, rather than via the original batch.

For our tests we work with the `optimizers` sample project:

    >>> project = Project(sample("projects", "optimizers"))

## Initial batch run

For our initial batch run, we use two values each for flags `x` and
`y`:

    >>> project.run("echo.py", flags={"x": [1.0,2.0], "y": [2,3]})
    INFO: [guild] Running trial ...: echo.py (x=1.0, y=2, z=a)
    1.0 2 'a'
    INFO: [guild] Running trial ...: echo.py (x=1.0, y=3, z=a)
    1.0 3 'a'
    INFO: [guild] Running trial ...: echo.py (x=2.0, y=2, z=a)
    2.0 2 'a'
    INFO: [guild] Running trial ...: echo.py (x=2.0, y=3, z=a)
    2.0 3 'a'

The runs:

    >>> project.print_runs(flags=True)
    echo.py   x=2.0 y=3 z=a
    echo.py   x=2.0 y=2 z=a
    echo.py   x=1.0 y=3 z=a
    echo.py   x=1.0 y=2 z=a
    echo.py+

When we restart the batch, it generated new trials.

    >>> batch = project.list_runs()[-1]

    >>> project.run(restart=batch.id)
    INFO: [guild] Running trial ...: echo.py (x=1.0, y=2, z=a)
    1.0 2 'a'
    INFO: [guild] Running trial ...: echo.py (x=1.0, y=3, z=a)
    1.0 3 'a'
    INFO: [guild] Running trial ...: echo.py (x=2.0, y=2, z=a)
    2.0 2 'a'
    INFO: [guild] Running trial ...: echo.py (x=2.0, y=3, z=a)
    2.0 3 'a'

And the runs:

    >>> project.print_runs(flags=True)
    echo.py   x=2.0 y=3 z=a
    echo.py   x=2.0 y=2 z=a
    echo.py   x=1.0 y=3 z=a
    echo.py   x=1.0 y=2 z=a
    echo.py+
    echo.py   x=2.0 y=3 z=a
    echo.py   x=2.0 y=2 z=a
    echo.py   x=1.0 y=3 z=a
    echo.py   x=1.0 y=2 z=a

We can restart the batch with a modified flag. It generates new runs
using the previous flags and the new values.

    >>> project.run(restart=batch.id, flags={"x": [4.0]})
    INFO: [guild] Running trial ...: echo.py (x=4.0, y=2, z=a)
    4.0 2 'a'
    INFO: [guild] Running trial ...: echo.py (x=4.0, y=3, z=a)
    4.0 3 'a'

And the runs:

    >>> project.print_runs(flags=True)
    echo.py   x=4.0 y=3 z=a
    echo.py   x=4.0 y=2 z=a
    echo.py+
    echo.py   x=2.0 y=3 z=a
    echo.py   x=2.0 y=2 z=a
    echo.py   x=1.0 y=3 z=a
    echo.py   x=1.0 y=2 z=a
    echo.py   x=2.0 y=3 z=a
    echo.py   x=2.0 y=2 z=a
    echo.py   x=1.0 y=3 z=a
    echo.py   x=1.0 y=2 z=a

Cleanup:

    >>> project.delete_runs()
    Deleted 11 run(s)

## Restarting staged runs

We can stage a batch, in which case it doesn't generate trials.

    >>> project.run("echo.py", flags={"x": [5.0], "y": [4,6]}, stage=True)
    echo.py+ staged as ...
    ...

    >>> project.print_runs()
    echo.py+

Restart the staged run:

    >>> batch = project.list_runs()[0]
    >>> project.run(restart=batch.id)
    INFO: [guild] Running trial ...: echo.py (x=5.0, y=4, z=a)
    5.0 4 'a'
    INFO: [guild] Running trial ...: echo.py (x=5.0, y=6, z=a)
    5.0 6 'a'

And our runs:

    >>> project.print_runs(flags=True)
    echo.py   x=5.0 y=6 z=a
    echo.py   x=5.0 y=4 z=a
    echo.py+

As with the previous example, we can restart using different flags.

    >>> project.run(restart=batch.id, flags={"x": [7.0]})
    INFO: [guild] Running trial ...: echo.py (x=7.0, y=4, z=a)
    7.0 4 'a'
    INFO: [guild] Running trial ...: echo.py (x=7.0, y=6, z=a)
    7.0 6 'a'

The runs:

    >>> project.print_runs(flags=True)
    echo.py   x=7.0 y=6 z=a
    echo.py   x=7.0 y=4 z=a
    echo.py+
    echo.py   x=5.0 y=6 z=a
    echo.py   x=5.0 y=4 z=a
