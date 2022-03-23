# Run Status

These tests are not exhaustive. The test a subset of the possible run
status.

    >>> gh = mkdtemp()
    >>> symlink(sample("runs"), path(gh, "runs"))
    >>> set_guild_home(gh)

    >>> run("guild runs")
    ???
    [...:42803252]  mnist:evaluate  ...  completed
    [...:7d145216]  mnist:train     ...  error
    [...:360192fd]  mnist:train     ...  pending
    <exit 0>

## Completed

    >>> run("guild runs --completed")
    ???
    [...:42803252]  mnist:evaluate  ...  completed
    <exit 0>

    >>> run("guild runs -Sc")
    ???
    [...:42803252]  mnist:evaluate  ...  completed
    <exit 0>

## Error

    >>> run("guild runs --error")
    ???
    [...:7d145216]  mnist:train  ...  error
    <exit 0>

    >>> run("guild runs -Se")
    ???
    [...:7d145216]  mnist:train  ...  error
    <exit 0>

## Pending

    >>> run("guild runs --completed")
    ???
    [...:42803252]  mnist:evaluate  ...  completed
    <exit 0>

    >>> run("guild runs -Sc")
    ???
    [...:42803252]  mnist:evaluate  ...  completed
    <exit 0>

## Multiple

    >>> run("guild runs --completed --error")
    ???
    [...:42803252]  mnist:evaluate  ...  completed
    [...:7d145216]  mnist:train     ...  error
    <exit 0>

    >>> run("guild runs -Sec")
    ???
    [...:42803252]  mnist:evaluate  ...  completed
    [...:7d145216]  mnist:train     ...  error
    <exit 0>

    >>> run("guild runs -Scp")
    ???
    [...:42803252]  mnist:evaluate  ...  completed
    [...:360192fd]  mnist:train     ...  pending
    <exit 0>

## Unsupported Status Chars

    >>> run("guild runs -Sxyz")
    guild: unrecognized status char 'x' in option '-S'
    Try 'guild runs --help' for more information.
    <exit 1>
