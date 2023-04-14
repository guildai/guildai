# Run as needed

A user can specify `--needed` for a run to indicate that the operation
should be run only if there isn't another run available for the
specified operation with the same flag values. Guild does not consider
`error` status runs (i.e. failed runs) when

To illustrate we'll use the `echo.py` script in the `optimizers`
project.

    >>> use_project("optimizers")

Run `echo.py`. Use `--run-id` so we can assert matching runs below.

    >>> run("guild run echo.py --run-id aaa -y")
    1.0 2 'a'

Run `echo.py` with `--needed`. Guild skips the operation because it
finds an available run.

    >>> run("guild run echo.py --needed --run-id bbb -y")
    Skipping because the following runs match this operation (--needed specified):
      [aaa]  echo.py  ...  completed  x=1.0 y=2 z=a

Guild did not generate a second run.

    >>> run("guild runs")
    [1:aaa]  echo.py  ...  completed  x=1.0 y=2 z=a

Run again with `--needed` but with different flag values.

    >>> run("guild run echo.py x=2.0 --needed --run-id ccc -y")
    2.0 2 'a'

Guild generates a second run.

    >>> run("guild runs")
    [1:ccc]  echo.py  ...  completed  x=2.0 y=2 z=a
    [2:aaa]  echo.py  ...  completed  x=1.0 y=2 z=a
    <exit 0>

Run again with the same flags.

    >>> run("guild run echo.py x=2.0 --needed --run-id ddd -y")
    Skipping because the following runs match this operation (--needed specified):
      [ccc]  echo.py  ...  completed  x=2.0 y=2 z=a

Guild does not generate a run in this case.

    >>> run("guild runs")
    [1:ccc]  echo.py  ...  completed  x=2.0 y=2 z=a
    [2:aaa]  echo.py  ...  completed  x=1.0 y=2 z=a

## Needed and run status

Reset the project.

    >>> use_project("optimizers")

Guild considers `error` status to always require a restart.

Use `fail.py` to illustrate.

    >>> run("guild run fail.py --run-id aaa -y")
    ???
    Exception: FAIL
    <exit 1>

    >>> run("guild runs")
    [1:aaa]  fail.py  ...  error  code=1

Run `fail.py` again with `--needed` and without chaning the flag
values. Had the first run completed, the `--needed` flag would cause
Guild to skip the run. In this case, Guild does not consider the
previous failed run in its check for available runs.

    >>> run("guild run fail.py --run-id bbb --needed -y")
    ???
    Exception: FAIL
    <exit 1>

Guild generates another run.

    >>> run("guild runs")
    [1:bbb]  fail.py  ...  error  code=1
    [2:aaa]  fail.py  ...  error  code=1

Run `fail.py` with `code=0`, which cause the operation to complete
without error.

    >>> run("guild run fail.py code=0 --run-id ccc -y")
    <exit 0>

    >>> run("guild runs")
    [1:ccc]  fail.py  ...  completed  code=0
    [2:bbb]  fail.py  ...  error      code=1
    [3:aaa]  fail.py  ...  error      code=1

Run `fail.py` with the default flags and `--needed`. Again, Guild runs
the operation because it can't find a non-error run with the same flag
values.

    >>> run("guild run fail.py --run-id ddd --needed -y")
    ???
    Exception: FAIL
    <exit 1>

    >>> run("guild runs")
    [1:ddd]  fail.py  ...  error      code=1
    [2:ccc]  fail.py  ...  completed  code=0
    [3:bbb]  fail.py  ...  error      code=1
    [4:aaa]  fail.py  ...  error      code=1

Run `fail.py` with `--needed` and `fail=no`. In thie case, Guild finds
the previous completed run with matching flag values and skips the
run.

    >>> run("guild run fail.py code=0 --run-id eee --needed -y")
    Skipping because the following runs match this operation (--needed specified):
      [ccc]  fail.py  ...  completed  code=0

Guild does not generate a new run.

    >>> run("guild runs")
    [1:ddd]  fail.py  ...  error      code=1
    [2:ccc]  fail.py  ...  completed  code=0
    [3:bbb]  fail.py  ...  error      code=1
    [4:aaa]  fail.py  ...  error      code=1

## Needed and restarts

When used with `--restart`, `--needed` has a different meaning. When
needed is specified for a restart, Guild does not check for other
available runs but instead checks the specified restart run. Guild
checks the run status and flag values of the restart run and only
restarts if the status is non-error (terminated or completed) or the
flag values are different.

Reset the project.

    >>> use_project("optimizers")

Run `echo.py`.

    >>> run("guild run echo.py --run-id aaa -y")
    1.0 2 'a'

Restart the run without `--needed`. Guild always restarts the run.

    >>> run("guild run --restart aaa -y")
    1.0 2 'a'

Restart the run with `--needed`.

    >>> run("guild run --restart aaa --needed -y")
    Skipping run because flags have not changed (--needed specified)

    >>> run("guild runs")
    [1:aaa]  echo.py  ...  completed  x=1.0 y=2 z=a

Change a flag value for restart.

    >>> run("guild run --restart aaa --needed x=2.0 -y")
    2.0 2 'a'

    >>> run("guild runs")
    [1:aaa]  echo.py  ...  completed  x=2.0 y=2 z=a

### Run status and restarts

Guild considers run status when `--needed` is specified for restart.

Guild uses the following rules when applying run status to a restart
needed check:

| status       | restart needed                            |
|--------------|-------------------------------------------|
| `completed`  | check flags                               |
| `terminated` | check flags                               |
| `running`    | not applicable (Guild refuses to restart) |
| `pending`    | always restart                            |
| `staged`     | always restart                            |
| `error`      | always restart                            |

#### Completed

The baseline state is completed. This is one of two states that Guild
considers suitable for accepting a run as "available" - i.e. not
needing a restart.

    >>> run("guild runs")
    [1:aaa]  echo.py  ...  completed  x=2.0 y=2 z=a

    >>> run("guild run --restart aaa --needed -y")
    Skipping run because flags have not changed (--needed specified)

#### Terminated

Terminated is inferred from a negative exit status. This occurs when
the run process receives an interrupt - e.g. from the user pressing
`Ctrl-c` or a `SIGINT` sent to the process.

Simulate a terminated status.

    >>> aaa_dir = run_capture("guild select --dir aaa")
    >>> aaa_exit_status_path = path(aaa_dir, ".guild/attrs/exit_status")

    >>> write(aaa_exit_status_path, "-9")

    >>> run("guild runs")
    [1:aaa]  echo.py  ...  terminated  x=2.0 y=2 z=a

Restart with `--needed`. Guild considers "terminated" to be a
non-error status and uses terminated runs when resolving operation
dependencies. Guild assumes in this case that the user intentionally
stops a run because it's reached an acceptable level of training
performance.

NOTE: This behavior may change in the future. See
https://github.com/guildai/guildai/issues/493 for details.

    >>> run("guild run --restart aaa --needed -y")
    Skipping run because flags have not changed (--needed specified)

#### Running

Guild does not attempt to restart a running process.

Guild infers that a run is running if it has a `LOCK` file containing
an active OS process.

Simulate a running run using the current test process (i.e. the
process running these examples) in the `LOCK` file.

    >>> aaa_lock_path = path(aaa_dir, ".guild/LOCK")
    >>> write(aaa_lock_path, str(os.getpid()))
    >>> rm(aaa_exit_status_path)

    >>> run("guild runs")
    [1:aaa]  echo.py  ...  running  x=2.0 y=2 z=a

Attempt to restart the running run.

    >>> run("guild run --restart aaa --needed -y")
    guild: cannot restart run aaa because it's running
    Use 'guild stop aaa' to stop it first and try again.
    <exit 1>

Remove the lock file.

    >>> rm(aaa_lock_path)

#### Pending

Guild always restarats a pending run. Guild infers this status by the
presence of a `PENDING` sentinel.

    >>> aaa_pending_path = path(aaa_dir, ".guild/PENDING")
    >>> touch(aaa_pending_path)

    >>> run("guild runs")
    [1:aaa]  echo.py  ...  pending  x=2.0 y=2 z=a

Attempt to restart the run.

    >>> run("guild run --restart aaa --needed -y")
    2.0 2 'a'

    >>> run("guild runs")
    [1:aaa]  echo.py  ...  completed  x=2.0 y=2 z=a

#### Staged

User can stage runs using the `--stage` option. When staging a run,
Guild initializes the run to ensure it can be started using a
subsequent `run` command with the `--start` option.

`--start` and `--restart` are interchangeable. The separate options
exist to improve the clarity of the start/restart command. However, to
Guild, the behavior is identical for either option.

Guild infers a staged status by the presence of a `STAGED` sentinel.

    >>> aaa_staged_path = path(aaa_dir, ".guild/STAGED")
    >>> touch(aaa_staged_path)

    >>> run("guild runs")
    [1:aaa]  echo.py  ...  staged  x=2.0 y=2 z=a

Restart the staged run with `--needed`. Guild always considers
"staged" to need a restart.

    >>> run("guild run --restart aaa --needed -y")
    2.0 2 'a'

The run is completed.

    >>> run("guild runs")
    [1:aaa]  echo.py  ...  completed  x=2.0 y=2 z=a

#### Error

Guild infers an "error" status by a non-zero, non-negative exit
status.

Simulate an error status.

    >>> write(aaa_exit_status_path, "1")

    >>> run("guild runs")
    [1:aaa]  echo.py  ...  error  x=2.0 y=2 z=a

Restart the run with `--needed`. Guild always considers "error" to
need a restart.

    >>> run("guild run --restart aaa --needed -y")
    2.0 2 'a'

The run is completed.

    >>> run("guild runs")
    [1:aaa]  echo.py  ...  completed  x=2.0 y=2 z=a
