# Restarting runs

Runs can be restarted using the --restart option.

We'll use the `optimizers` project for our tests.

    >>> project = Project(sample("projects", "optimizers"))

And a helper to get the run ID for a 1-index based run:

    >>> def run_id(index):
    ...     return project.list_runs()[index-1].id

Let's generate a run:

    >>> project.run("echo.py")
    1.0 2 'a'

And our runs:

    >>> project.print_runs(flags=True, status=True)
    echo.py  x=1.0 y=2 z=a  completed

Let's run a second operation with explicit flag values:

    >>> project.run("echo.py", flags={"x": 2.0, "y": 3, "z": "b"})
    2.0 3 'b'

And our runs:

    >>> project.print_runs(flags=True, status=True)
    echo.py  x=2.0 y=3 z=b  completed
    echo.py  x=1.0 y=2 z=a  completed

Let's restart the last run (run 1) without specifying any flags:

    >>> project.run(restart=run_id(1))
    Restarting ...
    2.0 3 'b'

We can also use the operation name, which restarts the latest or
marked run matching the name:

    >>> project.run(restart="echo.py")
    Restarting ...
    2.0 3 'b'

Note the original flags are used and that these are not the default
flag values (which are represented in run 2).

Let's restart run 1 with a new value for x:

    >>> project.run(restart=run_id(1), flags={"x": 10})
    Restarting ...
    10 3 'b'

When we restart run 1 again, this time with no explicit flag values,
it uses the last-specified flag values:

    >>> project.run(restart=run_id(1))
    Restarting ...
    10 3 'b'

And again using the operation name:

    >>> project.run(restart="echo.py")
    Restarting ...
    10 3 'b'

We can use the `needed` flag to instruct Guild to run the operation
only if it needs to based on the specified flag values. If the flag
values are the same as the last run, the operation is skipped.

    >>> project.run(restart=run_id(1), needed=True)
    Restarting ...
    Skipping run because flags have not changed (--needed specified)

Let's request a run restart with needed using the same flag values
explicitly:

    >>> project.run(restart=run_id(1), flags={"x": 10, "y": 3, "z": "b"},
    ...             needed=True)
    Restarting ...
    Skipping run because flags have not changed (--needed specified)

If any flag value differs, the run proceeds:

    >>> project.run(restart=run_id(1), flags={"x": 100, "y": 3, "z": "b"},
    ...             needed=True)
    Restarting ...
    100 3 'b'

Finally, let's restart run 2 twice with the same flag values and the
needed flag.

    >>> project.run(restart=run_id(2), flags={"z": "d"}, needed=True)
    Restarting ...
    1.0 2 'd'

    >> project.run(restart=run_id(2), flags={"z": "d"}, needed=True)
    Restarting ...
    Skipping run because flags have not changed (--needed specified)

## Run params for restarts

The `op_util` module provides a function that returns a list of run
params that should be used when restarting a particular run. The
params are based on the params that were used when originally running
or staging the run.

    >>> from guild import op_util

    >>> pprint(op_util.run_params_for_restart(project.list_runs()[0]))
    {'disable_plugins': None,
     'force_flags': False,
     'gpus': None,
     'max_trials': None,
     'maximize': None,
     'minimize': None,
     'no_gpus': False,
     'opt_flags': [],
     'optimizer': None,
     'random_seed': ...}

## Check for restart

`op_util` also provides a check to determine whether or not a run
should be restarted based on a set of new flags.

Here are the flags for the latest run:

    >>> latest = project.list_runs()[0]
    >>> pprint(latest.get("flags"))
    {'x': 1.0, 'y': 2, 'z': 'd'}

And various checks for restart:

    >>> op_util.restart_needed(latest, {})
    True

    >>> op_util.restart_needed(latest, {"x": 1.0})
    True

    >>> op_util.restart_needed(latest, {"x": 1.0, "y": 2})
    True

    >>> op_util.restart_needed(latest, {"x": 1.0, "y": 2, "z": "d"})
    False

    >>> op_util.restart_needed(latest, {"x": 1.0, "y": 2, "z": "d", "a": 0})
    True
