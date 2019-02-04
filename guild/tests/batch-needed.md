# Batch runs - running as needed

The `--needed` flag can be specified for a run to indicate that the
operation should be run only if needed - i.e. only if there isn't
already another run available with the same flags.

For general tests on the needed option, see [needed.md](needed.md).

For our tests we use the `optimizers` sample project.

    >>> project = Project(sample("projects", "optimizers"))

Here's a helper for running echo:

    >>> def run_echo(needed=False, restart=None, **flags):
    ...     op = "echo.py" if not restart else None
    ...     project.run(op, restart=restart, needed=needed,
    ...                 flags=flags, simplify_trial_output=True)

## Needed for non-restarts

Let's run an initial batch of a single `echo.py` operation using the
needed option:

    >>> run_echo(x=[1], needed=True)
    Initialized trial (x=1, y=2, z=a)
    Running trial: echo.py (x=1, y=2, z=a)
    1 2 'a'

Here are our runs:

    >>> project.print_runs(flags=True, status=True)
    echo.py   x=1 y=2 z=a  completed
    echo.py+               completed

Let's run the same operation, again with the needed option:

    >>> run_echo(x=[1], needed=True)
    Skipping because the following runs match this operation (--needed specified):
      [...]  echo.py+  ...  completed

Our runs again - nothing new:

    >>> project.print_runs(flags=True, status=True)
    echo.py   x=1 y=2 z=a  completed
    echo.py+               completed

Next we'll run with a different set of flags, again with the needed
option:

    >>> run_echo(x=[2], needed=True)
    Initialized trial (x=2, y=2, z=a)
    Running trial: echo.py (x=2, y=2, z=a)
    2 2 'a'

As expected we have a new batch run and trial:

    >>> project.print_runs(flags=True, status=True)
    echo.py   x=2 y=2 z=a  completed
    echo.py+               completed
    echo.py   x=1 y=2 z=a  completed
    echo.py+               completed

Let's again request a batch run, specifying a flag set of an existing
batch:

    >>> run_echo(x=[2], needed=True)
    Skipping because the following runs match this operation (--needed specified):
      [...]  echo.py+  ...  completed

If we request a batch run with any new set of flags - even if some of
the specified flag values correspond to existing trials, we get a new
batch run. Here we run a batch using both previous values for `x`:

    >>> run_echo(x=[1,2], needed=True)
    Initialized trial (x=1, y=2, z=a)
    Running trial: echo.py (x=1, y=2, z=a)
    1 2 'a'
    Initialized trial (x=2, y=2, z=a)
    Running trial: echo.py (x=2, y=2, z=a)
    2 2 'a'

Flags have to match previous batch runs. So if we run again with both
values for `x`:

    >>> run_echo(x=[1,2], needed=True)
    Skipping because the following runs match this operation (--needed specified):
      [...]  echo.py+  ...  completed

If we have two matching batch runs, both are listed in the skipping
message. Let's run with `x=[1]` again so we have two such runs:

    >>> run_echo(x=[1])
    Initialized trial (x=1, y=2, z=a)
    Running trial: echo.py (x=1, y=2, z=a)
    1 2 'a'

When we specify needed, there are two runs that match:

    >>> run_echo(x=[1], needed=True)
    Skipping because the following runs match this operation (--needed specified):
      [...]  echo.py+  ...  completed
      [...]  echo.py+  ...  completed

## Needed for restarts

Using the needed option when restarting a batch run has a different
meaning. Guild restarts the batch operation indicating that it should
run trials only if needed. Needed in this case is determined by run
status: if the run is completed or terminated it is considered
satisfied and won't be considered needed for restart.

Let's run a new batch in a fresh workspace.

    >>> project.delete_runs()
    Deleted 9 run(s)

    >>> run_echo(x=[1,2])
    Initialized trial (x=1, y=2, z=a)
    Running trial: echo.py (x=1, y=2, z=a)
    1 2 'a'
    Initialized trial (x=2, y=2, z=a)
    Running trial: echo.py (x=2, y=2, z=a)
    2 2 'a'

Here's our batch run:

    >>> batch_run = project.list_runs()[-1]
    >>> batch_run.opref.to_opspec()
    '+'

Let's first restart the batch without the needed option:

    >>> run_echo(restart=batch_run.id)
    Restarting ...
    Initialized trial (x=1, y=2, z=a)
    Running trial: echo.py (x=1, y=2, z=a)
    1 2 'a'
    Initialized trial (x=2, y=2, z=a)
    Running trial: echo.py (x=2, y=2, z=a)
    2 2 'a'

In this case, both trials are restarted.

Here are our runs:

    >>> project.print_runs(flags=True, status=True)
    echo.py   x=2 y=2 z=a  completed
    echo.py   x=1 y=2 z=a  completed
    echo.py+               completed

Next we'll restart with the needed option:

    >>> run_echo(restart=batch_run.id, needed=True)
    Restarting ...
    Initialized trial (x=1, y=2, z=a)
    Skipping trial because flags have not changed (--needed specified)
    Initialized trial (x=2, y=2, z=a)
    Skipping trial because flags have not changed (--needed specified)

And our runs after:

    >>> project.print_runs(flags=True, status=True)
    echo.py+               completed
    echo.py   x=2 y=2 z=a  completed
    echo.py   x=1 y=2 z=a  completed

Note that the batch operation is listed first - it was restarted and
so gets a new start time.

If we delete one of the trials and restart with the needed option, the
deleted trials is run.

    >>> project.delete_runs([project.list_runs()[1].id])
    Deleted 1 run(s)

Our runs after deleting one trial:

    >>> project.print_runs(flags=True, status=True)
    echo.py+               completed
    echo.py   x=1 y=2 z=a  completed

Restart the batch with needed:

    >>> run_echo(restart=batch_run.id, needed=True)
    Restarting ...
    Skipping trial because flags have not changed (--needed specified)
    Initialized trial (x=2, y=2, z=a)
    Running trial: echo.py (x=2, y=2, z=a)
    2 2 'a'

And our runs after the restart:

    >>> project.print_runs(flags=True, status=True)
    echo.py   x=2 y=2 z=a  completed
    echo.py+               completed
    echo.py   x=1 y=2 z=a  completed
