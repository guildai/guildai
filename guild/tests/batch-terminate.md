# Batch Terminate Behavior

When a batch run is terminated, the batch stops any currently running
trials and exits. The stopped trial and the batch should show
terminated status.

Staged runs are left as they are. They can be deleted or started as
needed.

We use the `sleep` project for our tests.

    >>> project = Project(sample("projects", "sleep"))

Start a batch of two runs in the background.

    >>> project.run("sleep.py", flags={"seconds": [5, 5]}, background=True)
    + started in background as ... (pidfile ...)

Wait for the batch to stage and start a run.

    >>> sleep(4)

Show the runs.

    >>> project.print_runs(status=True)
    sleep.py   running
    sleep.py   staged
    sleep.py+  running

Stop the batch run.

    >>> with StderrCapture() as out:
    ...     project.stop_runs([3])
    >>> out.print()
    Stopping ... (pid ...)

Wait for the runs to stop;

    >>> sleep(4)

Show the runs after stopping the batch.

    >>> project.print_runs(status=True)
    sleep.py   terminated
    sleep.py   staged
    sleep.py+  terminated

Show output for the batch.

    >>> runs = project.list_runs()

    >>> cat(runs[2].guild_path("output"))
    INFO: [guild] Running trial ...: sleep.py (seconds=5)
    INFO: [guild] Stopping trial (proc ...)
    INFO: [guild] Stopping batch (remaining staged trials may be started as needed)
    <BLANKLINE>
