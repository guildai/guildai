# Restarting runs

Runs can be restarted using the --restart option.

To run some operations, we'll need a workspace.

    >>> workspace = mkdtemp()

We'll run operations from the `optimizers` project, which provides an
`echo` operation.

    >>> project = sample("projects", "optimizers")

Here's our run helper:

    >>> def run(restart=None, needed=False, **flags):
    ...     out = gapi.run_capture_output(
    ...        "echo.py",
    ...        flags=flags,
    ...        restart=restart,
    ...        needed=needed,
    ...        cwd=project,
    ...        guild_home=workspace)
    ...     print(out.strip())

And a helper for listing runs:

    >>> def list_runs():
    ...     for i, run in enumerate(gapi.runs_list(guild_home=workspace)):
    ...         pprint((i + 1, run.get("flags")))

And another helper to get the run ID for a 1-index based run:

    >>> def run_id(index):
    ...     return gapi.runs_list(guild_home=workspace)[index-1].id

Let's generate a run:

    >>> run()
    1.0 2 'a'

And list our runs:

    >>> list_runs()
    (1, {'x': 1.0, 'y': 2, 'z': 'a'})

Let's run a second operation with explicit flag values:

    >>> run(x=2.0, y=3, z="b")
    2.0 3 'b'

And our runs:

    >>> list_runs()
    (1, {'x': 2.0, 'y': 3, 'z': 'b'})
    (2, {'x': 1.0, 'y': 2, 'z': 'a'})

Let's restart run 1 without specifying any flags:

    >>> run_1 = run_id(1)
    >>> run(restart=run_1)
    Restarting ...
    2.0 3 'b'

Note the original flags are used and that these are not the default
flag values (which are represented in run 2).

Let's restart run 1 with a new value for x:

    >>> run(restart=run_1, x=10)
    Restarting ...
    10 3 'b'

When we restart run 1 again, this time with no explicit flag values,
it uses the last-specified flag values:

    >>> run(restart=run_1)
    Restarting ...
    10 3 'b'

We can use the `needed` flag to instruct Guild to run the operation
only if it needs to based on the specified flag values. If the flag
values are the same as the last run, the operation is skipped.

    >>> run(restart=run_1, needed=True)
    Restarting ...
    Skipping run because flags have not changed (--needed specified)

Let's request a run using the same flag values explicitly:

    >>> run(restart=run_1, x=10, y=3, z="b", needed=True)
    Restarting ...
    Skipping run because flags have not changed (--needed specified)

If any flag value differs, the run proceeds:

    >>> run(restart=run_1, x=100, y=3, z="b", needed=True)
    Restarting ...
    100 3 'b'

Finally, let's restart run 2 twice with the same flag values and the
needed flag.

    >>> run_2 = run_id(2)

    >>> run(restart=run_2, z="d", needed=True)
    Restarting ...
    1.0 2 'd'

    >>> run(restart=run_2, z="d", needed=True)
    Restarting ...
    Skipping run because flags have not changed (--needed specified)
