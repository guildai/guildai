# Delete On Success

Guild operations can be configured to be automatically deleted on
success. We use the `delete-on-success` sample project to illustrate.

    >>> cd(sample("projects", "delete-on-success"))

Use an isolated env to test runs.

    >>> set_guild_home(mkdtemp())

Run the operation with label `run-1`.

    >>> run("guild run op -l run-1 -y")
    ???Deleting interim run ... ('op' is configured for deletion on success)
    <exit 0>

The run is automatically deleted on success.

    >>> run("guild runs")
    <exit 0>

The run is temporarily deleted -- you can show the run using the `-d,
--deleted` option.

    >>> run("guild runs -d")
    [1:...]  op  ...  completed  run-1
    <exit 0>

Use the option `--keep-run` to prevent it from being deleted.

    >>> run("guild run op -l run-2 --keep-run -y")
    <exit 0>

Show the runs.

    >>> run("guild runs")
    [1:...]  op  ...  completed  run-2
    <exit 0>

A failed run is not deleted, even when configured with
`delete-on-success`.

    >>> run("guild run op fail=yes -l run-3 -y")
    <exit 1>

    >>> run("guild runs")
    [1:...]  op  ...  error      run-3
    [2:...]  op  ...  completed  run-2
    <exit 0>
