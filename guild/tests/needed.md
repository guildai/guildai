# Run as needed

The `--needed` flag can be specified for a run to indicate that the
operation should be run only if needed - i.e. only if there isn't
already another run available with the same flags.

An available run is a run of the same operation having the same flag
values.

To illustrate we'll use the `echo.py` script in the `optimizers`
project:

    >>> project = Project(sample("projects", "optimizers"))

Verifying that there are no runs associated with the project:

    >>> project.print_runs()

Let's run `echo.py` for the first time without any options:

    >>> project.run("echo.py")
    1.0 2 'a'

Next we'll run using the needed option:

    >>> project.run("echo.py", needed=True)
    Skipping because the following runs match this operation (--needed specified):
      [...]  echo.py  ...  completed

When we run using a different set of flags and the needed option:

    >>> project.run("echo.py", flags={"x": 2.0}, needed=True)
    2.0 2 'a'

And again, the same command:

    >>> project.run("echo.py", flags={"x": 2.0}, needed=True)
    Skipping because the following runs match this operation (--needed specified):
      [...]  echo.py  ...  completed

And our runs:

    >>> project.print_runs(flags=True, status=True)
    echo.py  x=2.0 y=2 z=a  completed
    echo.py  x=1.0 y=2 z=a  completed

## Needed and pending

A pending run is not considered when checking for runs when needed is
specified.

Let's modify our latest run, where `x` equals 2.0, to be pending:

    >>> latest_run = project.list_runs()[0]
    >>> latest_run.get("flags")["x"]
    2.0
    >>> touch(latest_run.guild_path("PENDING"))

Verify our run status:

    >>> project.print_runs(flags=True, status=True)
    echo.py  x=2.0 y=2 z=a  pending
    echo.py  x=1.0 y=2 z=a  completed

Let's run with `x` equal to 2.0 and with needed:

    >>> project.run("echo.py", flags={"x": 2.0}, needed=True)
    2.0 2 'a'

In this case, the run proceeded:

    >>> project.print_runs(flags=True, status=True)
    echo.py  x=2.0 y=2 z=a  completed
    echo.py  x=2.0 y=2 z=a  pending
    echo.py  x=1.0 y=2 z=a  completed

## Needed and restarts

The needed flag can be used with the `--restart` flag with a slightly
different meaning. When needed is specified for a restart, Guild does
not check for other available runs but instead checks the specified
restart run. If the restart run has the same flags as specified in the
run command and the needed option is used, Guild will skip the
restart.

Let's restart the latest run without the needed option as a baseline:

    >>> latest_run = project.list_runs()[0]
    >>> project.run(restart=latest_run.id)
    Restarting ...
    2.0 2 'a'

Now we'll restart it with the needed option:

    >>> project.run(restart=latest_run.id, needed=True)
    Restarting ...
    Skipping run because flags have not changed (--needed specified)

However, when we use a different set of flags for the restart:

    >>> project.run(restart=latest_run.id, flags={"x": 3.0}, needed=True)
    Restarting ...
    3.0 2 'a'

And our runs:

    >>> project.print_runs(flags=True, status=True)
    echo.py  x=3.0 y=2 z=a  completed
    echo.py  x=2.0 y=2 z=a  pending
    echo.py  x=1.0 y=2 z=a  completed

When we restart a pending run with needed, it is restarted even if the
flags match:

    >>> pending_run = project.list_runs()[1]
    >>> pending_run.status
    'pending'

    >>> project.run(restart=pending_run.id, needed=True)
    Restarting ...
    2.0 2 'a'

And our runs:

    >>> project.print_runs(flags=True, status=True)
    echo.py  x=2.0 y=2 z=a  completed
    echo.py  x=3.0 y=2 z=a  completed
    echo.py  x=1.0 y=2 z=a  completed
