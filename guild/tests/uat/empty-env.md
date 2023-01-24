# Initial UAT env

The `models` command is used to list models. Initially there are
models available.

    >>> run("guild models")
    <exit 0>

Initially there are no models installed and so correspondingly there
are no available operations.

    >>> run("guild ops")
    <exit 0>

The test environment is configured to isolate runs to the
workspace. Initially there are no runs.

    >>> run("guild runs list")
    <exit 0>
