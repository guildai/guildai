---
doctest: -WINDOWS
---

# Stopping Runs

The `stop` command stops runs. We use the `multiprocessing` sample
project to confirm that Guild stops all run OS processes.

    >>> cd(sample("projects", "multiprocessing"))

Use an isolated Guild home for these tests.

    >>> set_guild_home(mkdtemp())

Run `test.py` in the background. We use a label to identify the run in
steps below.

    >>> run("guild run test.py -l run-stop-test --background -y")
    test.py started in background as ... (pidfile ...)
    <exit 0>

The script prints associated OS pids associated. Wait a moment and
read these from the run output.

    >>> sleep(3)
    >>> out, exit = run_capture("guild cat --output -Fl run-stop-test")
    >>> exit
    0

Get the list of pids from the output.

    >>> pids = [int(s) for s in out.strip().split("\n")]

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
