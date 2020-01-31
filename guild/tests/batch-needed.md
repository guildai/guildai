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
    ...     project.run(op, restart=restart, needed=needed, flags=flags)

## Needed for non-restarts

Let's run an initial batch of a single `echo.py` operation using the
needed option:

    >>> run_echo(x=[1], needed=True)
    INFO: [guild] Running trial ...: echo.py (x=1, y=2, z=a)
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
    INFO: [guild] Running trial ...: echo.py (x=2, y=2, z=a)
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
    INFO: [guild] Running trial ...: echo.py (x=1, y=2, z=a)
    1 2 'a'
    INFO: [guild] Running trial ...: echo.py (x=2, y=2, z=a)
    2 2 'a'

Flags have to match previous batch runs. So if we run again with both
values for `x`:

    >>> run_echo(x=[1,2], needed=True)
    Skipping because the following runs match this operation (--needed specified):
      [...]  echo.py+  ...  completed

If we have two matching batch runs, both are listed in the skipping
message. Let's run with `x=[1]` again so we have two such runs:

    >>> run_echo(x=[1])
    INFO: [guild] Running trial ...: echo.py (x=1, y=2, z=a)
    1 2 'a'

When we specify needed, there are two runs that match:

    >>> run_echo(x=[1], needed=True)
    Skipping because the following runs match this operation (--needed specified):
      [...]  echo.py+  ...  completed
      [...]  echo.py+  ...  completed
