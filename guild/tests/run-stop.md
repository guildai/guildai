---
doctest: -WINDOWS -MACOS
---

# Stopping Runs

The `stop` command stops runs. We use the `multiprocessing` sample
project to confirm that Guild stops all run OS processes.

    >>> use_project("multiprocessing")

Run `test.py` in the background. We use a label to identify the run in
steps below.

    >>> run("guild run test.py -l run-stop-test --background -y")
    test.py started in background as ... (pidfile ...)
    <exit 0>

The script prints associated OS pids. Wait a moment and read these
from the run output.

    >>> sleep(2)
    >>> out = run_capture("guild cat --output -Fl run-stop-test")

Get the list of pids from the output.

    >>> pids = [int(s) for s in out.split("\n") if s]

Verify that the pids are alive.

    >>> import psutil

    >>> [(psutil.pid_exists(pid), pid) for pid in pids]
    [(True, ...), (True, ...), (True, ...), (True, ...)]

Stop the run.

    >>> run("guild stop -Fl run-stop-test -y", timeout=10)
    Stopping ... (pid ...)
    <exit 0>

Wait for the run processes to terminate and verify that they are no
longer running.

    >>> sleep(1)

    >>> [(psutil.pid_exists(pid), pid) for pid in pids]
    [(False, ...), (False, ...), (False, ...), (False, ...)]

## Handling unstopped runs

In cases where Guild cannot stop a run - e.g. the run takes too long
to stop or refuses to stop on `SIGINT`, the `stop` commands exits with
an error message.

To illustrate, we use `ignore_signint.py`, which ignores `INT`
signals.

Run `ignore_signint.py` in the background so we can stop it.

    >>> run("guild run ignore_sigint.py --background -y")
    ignore_sigint.py started in background as ... (pidfile ...)

Guild writes the run pid to `.guild/LOCK`.

    >>> pid = run_capture("guild cat -p .guild/LOCK")

Wait a moment and check the run status.

    >>> sleep(1)

    >>> run("guild runs -s -Fo ignore_sigint.py")
    [1]  ignore_sigint.py  running  seconds=5

Try to stop run using a short timeout.

    >>> run("guild runs stop --timeout 1 -y")
    Stopping ... (pid ...)
    The following processes did not stop as expected: ...
    <exit 1>

Stop the run using the `--force` option.

    >>> run("guild runs stop --force --timeout 1 -y")
    Stopping ... (pid ...)

Show the run status.

    >>> run("guild runs -s -Fo ignore_sigint.py")
    [1]  ignore_sigint.py  terminated  seconds=5

Attempt to stop the run again. Guild prints a message and exits
normally - stopping a run that isn't running is not treated as an
error.

    >>> run("guild stop 1 -y")
    Run ... is not running
    <exit 0>

Confirm that the run process does not exist.

    >>> run(f"kill -9 {pid}")
    ??? kill: No such process
    <exit 1>
