---
doctest: -WINDOWS
---

# Batch Terminate Behavior

When a batch run is terminated, the batch stops any currently running
trials and exits. The stopped trial and the batch should show
terminated status.

Staged runs are left as they are. They can be deleted or started as
needed.

We use the `sleep` project for our tests.

    >>> cd(sample("projects", "sleep"))

Use an isolated Guild home.

    >>> set_guild_home(mkdtemp())

Start a batch of two runs in the background.

    >>> run("guild run sleep.py seconds=[99,99] --background --yes")
    + started in background as ... (pidfile ...)
    <exit 0>

Wait for the batch to stage and start a run.

    >>> sleep(4)

Show the runs.

    >>> run("guild runs")
    [1:...]  sleep.py   ...  running  seconds=99
    [2:...]  sleep.py   ...  pending  seconds=99
    [3:...]  sleep.py+  ...  running
    <exit 0>

Stop the batch run.

    >>> run("guild stop 3 -y")
    Stopping ... (pid ...)
    <exit 0>

Wait for the runs to stop;

    >>> sleep(10)

Show the runs after stopping the batch.

    >>> run("guild runs")
    [1:...]  sleep.py   ...  terminated  seconds=99
    [2:...]  sleep.py   ...  pending     seconds=99
    [3:...]  sleep.py+  ...  terminated
    <exit 0>

Show output for the batch.

    >>> out, exit_code = run_capture("guild cat 3 --output")
    >>> (out, exit_code)
    (..., 0)

    >>> print(out)
    INFO: [guild] Running trial ...: sleep.py (seconds=99)
    ...

    >>> "INFO: [guild] Stopping trial" in out, out
    (True, ...)

    >>> "INFO: [guild] Stopping batch (pending trials can be started as needed)" in out, out
    (True, ...)
