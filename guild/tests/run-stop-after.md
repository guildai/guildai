skip-windows: yes

NOTE: There is an issue with stop-after on Windows with the sample
script used below (sleep) that causes the process to require SIGKILL
(the Windows equivalent) and therefore to fail on Windows.

# Stopping a run after N seconds

The `--stop-after` option is used to stop a run after a number of
minutes have elapsed.

We use the `sleep` project to illustrate.

    >>> project = Project(sample("projects", "sleep"))

Record the time before starting the operation.

    >>> import time
    >>> time0 = time.time()

Start the operation with a high sleep time, stopping after a short
interval (note that stop after interval is minutes).

    >>> with Env({"STOP_AFTER_POLL_INTERVAL": "1"}):
    ...     project.run("sleep.py", flags={"seconds": 5.0}, stop_after=0.01)
    Stopping process early (pid ...) - 0.0 minute(s) elapsed
    <exit 241>

Record the run time and confirm that it is less than the specified
sleep time.

    >>> run_time = time.time() - time0
    >>> assert run_time < 5, run_time
