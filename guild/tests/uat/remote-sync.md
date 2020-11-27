# Remote Sync

Start a long running operation on remote. We use an operation in the
`parallel-runs` example that let's us sleep for a specified number of
seconds.

    >>> cd(example("parallel-runs"))

Start the op. This runs for 10 seconds. We use '--no-wait' to avoid
watching the run so we can run commands while it's running.

    >>> run("guild run op sleep=10 -r guild-uat --no-wait -y")
    Building package
    ...
    Successfully installed gpkg.anonymous-...
    Starting op on guild-uat as ...
    ... is running on guild-uat
    To watch use 'guild watch ... -r guild-uat'
    <exit 0>

To check the run status locally, we need to pull the run.

    >>> run("guild pull guild-uat 1 -y")
    Getting remote run info
    Copying ...
    <exit 0>

The run status is running. It also reflects the remote it's running
on.

    >>> run("guild runs -n1")
    [1:...]  gpkg.anonymous.../op  ...  running (guild-uat)  sleep=10
    <exit 0>

The remote associated with a local run is saved in
`.guild/LOCK.remote`.

    >>> run("guild cat -p .guild/LOCK.remote")
    guild-uat
    <exit 0>

With a local run, we can use `sync` to synchronize runs with their
associated remotes.

    >>> run("guild sync")
    Syncing ...
    Copying ...
    <exit 0>

    >>> run("guild runs -n1")
    [1:...]  gpkg.anonymous.../op  ...  running (guild-uat)  sleep=10
    <exit 0>

Wait for the run to ostensibly finish.

    >>> sleep(12)

The run status is the same. We need to sync again to bring the local
run status up-to-date.

    >>> run("guild runs -n1")
    [1:...]  gpkg.anonymous.../op  ...  running (guild-uat)  sleep=10
    <exit 0>

Run sync again.

    >>> run("guild sync")
    Syncing ...
    Copying ...
    <exit 0>

The local status reflects the remote status.

    >>> run("guild runs -n1")
    [1:...]  gpkg.anonymous.../op  ...  completed  sleep=10
    <exit 0>

The `LOCK.remote` file no longer exists as the run is not longer
running.

    >>> run("guild cat -p .guild/LOCK.remote")
    guild: .../.guild/LOCK.remote does not exist
    <exit 1>

When we sync again, nothing is sync'd because there are no running
ops.

    >>> run("guild sync")
    <BLANKLINE>
    <exit 0>
