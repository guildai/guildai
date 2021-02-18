# Run Status

These tests are not exhaustive. The test a subset of the possible run
status.

    >>> gh = mkdtemp()
    >>> symlink(sample("runs"), path(gh, "runs"))

    >>> _run = run
    >>> def run(cmd):
    ...     _run(cmd, env={"GUILD_HOME": gh})

    >>> run("guild runs")
    [1:42803252]  mnist:evaluate  2017-09-30 11:53:39  completed
    [2:7d145216]  mnist:train     2017-09-30 11:53:21  error
    [3:360192fd]  mnist:train     2017-09-30 11:53:05  pending
    <exit 0>

## Completed

    >>> run("guild runs --completed")
    [1:42803252]  mnist:evaluate  2017-09-30 11:53:39  completed
    <exit 0>

    >>> run("guild runs -Sc")
    [1:42803252]  mnist:evaluate  2017-09-30 11:53:39  completed
    <exit 0>

## Error

    >>> run("guild runs --error")
    [1:7d145216]  mnist:train  2017-09-30 11:53:21  error
    <exit 0>

    >>> run("guild runs -Se")
    [1:7d145216]  mnist:train  2017-09-30 11:53:21  error
    <exit 0>

## Pending

    >>> run("guild runs --completed")
    [1:42803252]  mnist:evaluate  2017-09-30 11:53:39  completed
    <exit 0>

    >>> run("guild runs -Sc")
    [1:42803252]  mnist:evaluate  2017-09-30 11:53:39  completed
    <exit 0>

## Multiple

    >>> run("guild runs --completed --error")
    [1:42803252]  mnist:evaluate  2017-09-30 11:53:39  completed
    [2:7d145216]  mnist:train     2017-09-30 11:53:21  error
    <exit 0>

    >>> run("guild runs -Sec")
    [1:42803252]  mnist:evaluate  2017-09-30 11:53:39  completed
    [2:7d145216]  mnist:train     2017-09-30 11:53:21  error
    <exit 0>

    >>> run("guild runs -Scp")
    [1:42803252]  mnist:evaluate  2017-09-30 11:53:39  completed
    [2:360192fd]  mnist:train     2017-09-30 11:53:05  pending
    <exit 0>
