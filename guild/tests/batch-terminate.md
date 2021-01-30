skip-windows: yes

# Batch Terminate Behavior

When a batch run is terminated, the batch stops any currently running
trials and exits. The stopped trial and the batch should show
terminated status.

Staged runs are left as they are. They can be deleted or started as
needed.

We use the `sleep` project for our tests.

    >>> cd(sample("projects", "sleep"))

Helper function to run commands within an isolated Guild home.

    >>> gh_env = {"GUILD_HOME": mkdtemp()}

    >>> def gh_run(cmd):
    ...     run(cmd, env=gh_env)

Start a batch of two runs in the background.

    >>> gh_run("guild run sleep.py seconds=[5,5] --background --yes")
    + started in background as ... (pidfile ...)
    <exit 0>

Wait for the batch to stage and start a run.

    >>> sleep(4)

Show the runs.

    >>> gh_run("guild runs")
    [1:...]  sleep.py   ...  running  seconds=5
    [2:...]  sleep.py   ...  staged   seconds=5
    [3:...]  sleep.py+  ...  running
    <exit 0>

Stop the batch run.

    >>> gh_run("guild stop 3 -y")
    Stopping ... (pid ...)
    <exit 0>

Wait for the runs to stop;

    >>> sleep(4)

Show the runs after stopping the batch.

    >>> gh_run("guild runs")
    [1:...]  sleep.py   ...  terminated  seconds=5
    [2:...]  sleep.py   ...  staged      seconds=5
    [3:...]  sleep.py+  ...  terminated
    <exit 0>

Show output for the batch.

    >>> gh_run("guild cat 3 --output")
    INFO: [guild] Running trial ...: sleep.py (seconds=5)
    INFO: [guild] Stopping trial (proc ...)
    INFO: [guild] Stopping batch (remaining staged trials may be started as needed)
    <exit 0>
