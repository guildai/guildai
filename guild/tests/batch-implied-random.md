# Batch runs - implied random optimizer

When a range is specified for a run without otherwise specifying an
optimizer, Guild implicitly uses the 'random' optimizer.

We'll use the `optimizers` sample project to illustrate.

    >>> project = Project(sample("projects", "optimizers"))

As a baseline, we'll run the `echo.py` script with some sample flags:

    >>> project.run("echo.py", flags={"x": 5.0, "y": 6, "z": "seven"},
    ...             max_trials=2)
    5.0 6 'seven'

We specify `max_trial` as a baseline - we use the same value in our
next run to control the number of generated trials. In this case, the
value is ignored.

And our runs:

    >>> project.print_runs(flags=True, status=True)
    echo.py  x=5.0 y=6 z=seven  completed

Next we'll specify a range for one of the values along with the same
value for `max_trials`:

    >>> project.run("echo.py", flags={"x": "[5.1:5.19]", "y": 6, "z": "seven"},
    ...             max_trials=2)
    INFO: [guild] Initialized trial ... (x=5.1..., y=6, z=seven)
    INFO: [guild] Running trial ...: echo.py (x=5.1..., y=6, z=seven)
    5.1... 6 'seven'
    INFO: [guild] Initialized trial ... (x=5.1..., y=6, z=seven)
    INFO: [guild] Running trial ...: echo.py (x=5.1..., y=6, z=seven)
    5.1... 6 'seven'

And our runs:

    >>> project.print_runs(flags=True, status=True)
    echo.py         x=5.1... y=6 z=seven  completed
    echo.py         x=5.1... y=6 z=seven  completed
    echo.py+random                        completed
    echo.py         x=5.0 y=6 z=seven     completed
