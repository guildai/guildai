# Remote Status

Remote status is determined by the following local run files:

- LOCK.remote
- TERMINATED.remote
- attrs/exit_status

If `LOCK.remote` exists, Guild considers the run to be running on the
remote.

Otherwise, Guild looks at `attrs/exit_status` to determine whether the
run completed successfully or not. A 0 exit status signifies
completed. A non-zero exit status signifies an error. If
`attrs/exit_status` does not exit, Guild considers it an error.

We use the `remote-status` sample project to test.

    >>> cd(sample("projects", "remote-status"))

Delete remote and local runs prior to running tests.

    >>> quiet("guild runs rm -r guild-uat -y")
    >>> run("guild runs -r guild-uat")
    <BLANKLINE>
    <exit 0>

    >>> quiet("guild runs rm -y")
    >>> run("guild runs")
    <BLANKLINE>
    <exit 0>

## Completed

Complete is indicated by an absence of `LOCK.remote` or
`TERMINATED.remote` and with an exit code of 0.

    >>> quiet("guild run sleep seconds=0 -r guild-uat -y")
    >>> quiet("guild pull guild-uat -y")
    >>> run("guild runs")
    [1:...]  gpkg.anonymous-.../sleep  ...  completed  seconds=0
    <exit 0>

There are no lock markers:

    >>> run("guild ls -nap 'LOCK*'")
    <BLANKLINE>
    <exit 0>

The exit status is `0`, which indicates a success.

    >>> run("guild cat -p .guild/attrs/exit_status")
    0
    <exit 0>

## Terminated

Terminated is indicated by a negative exit status code.

Start a remote run asynchronously and stop it immediately.

    >>> quiet("guild run sleep seconds=5 -r guild-uat -y --no-wait")
    >>> quiet("guild stop -r guild-uat -y")
    >>> run("guild runs -r guild-uat")
    [1:...]  gpkg.anonymous-.../sleep  ...  terminated  seconds=5
    [2:...]  gpkg.anonymous-.../sleep  ...  completed   seconds=0
    <exit 0>

Get the runs.

    >>> quiet("guild pull guild-uat -y")
    >>> run("guild runs")
    [1:...]  gpkg.anonymous-.../sleep  ...  terminated  seconds=5
    [2:...]  gpkg.anonymous-.../sleep  ...  completed   seconds=0
    <exit 0>

There are no lock markers.

    >>> run("guild ls -nap 'LOCK*'")
    <exit 0>

In this case, we also have an exit status. This is generated on the
remote server and reflects the true process exit code. Guild doesn't
use this status on the local server, however, because there's no
guarantee that this attribute is set for a terminated remote run.

    >>> run("guild cat -p .guild/attrs/exit_status")
    -15
    <exit 0>

## Running

Running is indicated by `LOCK.remote`.

Start a remote run asynchronously.

    >>> quiet("guild run sleep seconds=8 -r guild-uat -y --no-wait")

Wait a moment to let the run start on the remote.

    >>> sleep(2)

Check the run status.

    >>> run("guild runs -r guild-uat")
    [1:...]  gpkg.anonymous-.../sleep  ...  running     seconds=8
    [2:...]  gpkg.anonymous-.../sleep  ...  terminated  seconds=5
    [3:...]  gpkg.anonymous-.../sleep  ...  completed   seconds=0
    <exit 0>

Get the runs.

    >>> quiet("guild pull guild-uat -y")
    >>> run("guild runs")
    [1:...]  gpkg.anonymous-.../sleep  ...  running (guild-uat)  seconds=8
    [2:...]  gpkg.anonymous-.../sleep  ...  terminated           seconds=5
    [3:...]  gpkg.anonymous-.../sleep  ...  completed            seconds=0
    <exit 0>

The remote running status is signified by a remote lock.

    >>> run("guild ls -np '.guild/LOCK*'")
    .guild/LOCK.remote
    <exit 0>

This file contains the remote name.

    >>> run("guild cat -p .guild/LOCK.remote")
    guild-uat
    <exit 0>

The exit status attribute does not exit.

    >>> run("guild ls -np .guild/attrs/exit_status")
    <exit 0>

Sync with the remote run.

    >>> run("guild watch 1 -r guild-uat")
    Watching run ...
    Run ... stopped with a status of 'completed'
    <exit 0>

## Errors - normal

An error status may arise under several scenarios. These tests
illustrate a normal error, which occurs when the process exits with a
non-zero exit status.

    >>> run("guild run error -y -r guild-uat")
    Building package
    ...
    AssertionError
    Run ... stopped with a status of 'error'
    <exit 0>

    >>> run("guild runs -r guild-uat")
    [1:...]  gpkg.anonymous-.../error  ...  error
    [2:...]  gpkg.anonymous-.../sleep  ...  completed   seconds=8
    [3:...]  gpkg.anonymous-.../sleep  ...  terminated  seconds=5
    [4:...]  gpkg.anonymous-.../sleep  ...  completed   seconds=0
    <exit 0>

    >>> quiet("guild pull guild-uat -y")

    >>> run("guild runs")
    [1:...]  gpkg.anonymous-.../error  ...  error
    [2:...]  gpkg.anonymous-.../sleep  ...  completed   seconds=8
    [3:...]  gpkg.anonymous-.../sleep  ...  terminated  seconds=5
    [4:...]  gpkg.anonymous-.../sleep  ...  completed   seconds=0
    <exit 0>

There are no lock markers for this run.

    >>> run("guild ls -nap '*LOCK*'")
    <exit 0>

The exit status indicates the error.

    >>> run("guild cat -p .guild/attrs/exit_status")
    1
    <exit 0>

## Error - abnormal termination

An error status also arises when a process terminates abnormally.

The `kill` operation simulates this by sending SIGKILL to its parent
process, preventing Guild from clearing up LOCK and writing the exit
status.

We run with the `--no-wait` option because we aren't able to properly
wait on the process when it's killed.

    >>> run("guild run kill -y -r guild-uat --no-wait")
    Building package
    ...
    Starting kill on guild-uat as ...
    ... is running on guild-uat
    To watch use 'guild watch ... -r guild-uat'
    <exit 0>

Wait a moment for the remote run to terminate.

    >>> sleep(2)

    >>> run("guild runs -r guild-uat")
    [1:...]  gpkg.anonymous-.../kill   ...  error
    [2:...]  gpkg.anonymous-.../error  ...  error
    [3:...]  gpkg.anonymous-.../sleep  ...  completed   seconds=8
    [4:...]  gpkg.anonymous-.../sleep  ...  terminated  seconds=5
    [5:...]  gpkg.anonymous-.../sleep  ...  completed   seconds=0
    <exit 0>

The remote `LOCK` file still exists, even though the process terminated.

    >>> run("guild ls -np '.guild/LOCK*' -r guild-uat")
    .guild/LOCK
    <exit 0>

The remote exit status attribute is not written.

    >>> run("guild ls -nap .guild/attrs/exit_status -r guild-uat")
    <BLANKLINE>
    <exit 0>

Copy the runs from the remote.

    >>> quiet("guild pull guild-uat -y")

    >>> run("guild runs")
    [1:...]  gpkg.anonymous-.../kill   ...  error
    [2:...]  gpkg.anonymous-.../error  ...  error
    [3:...]  gpkg.anonymous-.../sleep  ...  completed   seconds=8
    [4:...]  gpkg.anonymous-.../sleep  ...  terminated  seconds=5
    [5:...]  gpkg.anonymous-.../sleep  ...  completed   seconds=0
    <exit 0>

Remote runs do not copy `LOCK` files.

    >>> run("guild ls -np '.guild/LOCK*'")
    <BLANKLINE>
    <exit 0>
