# Guild API (private)

NOTE: This module tests the internal `guild._api` module. This is not
an officially supported public API and should not be relied on for
long term support.

    >>> from guild import _api as gapi

Guild home for tests:

    >>> gh = mkdtemp()

We use the `optimizers` project for tests.

    >>> project_dir = sample("projects/optimizers")

## Run

The `run` function runs an operation.

We run `echo.py` to illustate.

We use pipes to capture output for tests here, otherwise output leaks
outside the doctest framework.

    >>> import subprocess

    >>> out, err = gapi.run("echo.py", cwd=project_dir, guild_home=gh,
    ...                     stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    >>> out.rstrip()  # rstrip to normalize line endings
    "1.0 2 'a'"

    >>> err
    ''

An generates a `RunError`.

    >>> try:
    ...     gapi.run("undefined", cwd=project_dir, guild_home=gh,
    ...              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    ... except gapi.RunError as e:
    ...     e.output, e.returncode
    (('', "guild: operation 'undefined' is not defined for this project..."), 1)

`run_capture_output` always captures output. stderr uses stdout to
provide a single `output` return value.

    >>> out = gapi.run_capture_output("echo.py", cwd=project_dir, guild_home=gh)

    >>> out.rstrip()  # rstrip to normalize line endings
    "1.0 2 'a'"

Errors are similarly denoted by `RunError`.

    >>> try:
    ...     gapi.run_capture_output("undefined", cwd=project_dir, guild_home=gh)
    ... except gapi.RunError as e:
    ...     e.output, e.returncode
    ("guild: operation 'undefined' is not defined for this project...", 1)

Note that `e.output` is a single string value in this case, rather
than a tuple of `out` and `err` output.

`run_quiet` returns no output, but raises `RunError` on error.

    >>> gapi.run_quiet("echo.py", cwd=project_dir, guild_home=gh)

    >>> try:
    ...     gapi.run_quiet("undefined", cwd=project_dir, guild_home=gh)
    ... except gapi.RunError as e:
    ...     e.output, e.returncode
    ("guild: operation 'undefined' is not defined for this project...", 1)

Note that the return error output is the same as
`run_capture_output` - stderr and stdout are combined.

## Runs List

Use `runs_list` to return a list of runs.

    >>> runs = gapi.runs_list(guild_home=gh)
    >>> len(runs)
    3

Use `limit` to limit the number of returned runs.

    >>> runs = gapi.runs_list(guild_home=gh, limit=2)
    >>> len(runs)
    2

## Current Run

Use `current_run` to return the run designed by the env vars `RUN_DIR`
and `RUN_ID`.

Let's use the lastest run dir.

    >>> latest_run = gapi.runs_list(guild_home=gh)[0]

    >>> with Env({"RUN_DIR": latest_run.dir,
    ...           "RUN_ID": latest_run.id}):
    ...     current_run = gapi.current_run()

    >>> current_run.id == latest_run.id, (current_run.id, latest_run.id)
    (True, ...)

    >>> current_run.dir == latest_run.dir, (current_run.dir, latest_run.dir)
    (True, ...)

If `RUN_DIR` is not specified, `NoCurrentRun` is raised.

    >>> with Env({"RUN_DIR": ""}):
    ...     gapi.current_run()
    Traceback (most recent call last):
    NoCurrentRun

## Mark Runs

Mark runs using `mark`.

    >>> print(latest_run.get("marked"))
    None

    >>> gapi.mark([latest_run.id], guild_home=gh)
    Marked 1 run(s)

    >>> latest_run.get("marked")
    True

    >>> gapi.mark([latest_run.id], clear=True, guild_home=gh)
    Unmarked 1 run(s)

    >>> print(latest_run.get("marked"))
    None

## Compare Runs

Use `compare` to compare runs.

    >>> gapi.compare(guild_home=gh)
    [['run', 'operation', 'started', 'time', 'status', 'label', 'x', 'y', 'z'],
     ['...', 'echo.py', '...', '...', 'completed', 'x=1.0 y=2 z=a', 1.0, 2, 'a'],
     ['...', 'echo.py', '...', '...', 'completed', 'x=1.0 y=2 z=a', 1.0, 2, 'a'],
     ['...', 'echo.py', '...', '...', 'completed', 'x=1.0 y=2 z=a', 1.0, 2, 'a']]

## Publish Runs

Use `publish` to publish runs.

Use a temp location to publish runs to.

    >>> publish_dest = mkdtemp()

    >>> gapi.publish(dest=publish_dest, guild_home=gh)
    Publishing [...] echo.py... using ...
    Publishing [...] echo.py... using ...
    Publishing [...] echo.py... using ...
    Refreshing runs index
    Published runs using ...

    >>> len(dir(publish_dest))
    5

## Package

Use `package` to package a project. Use CAPTURE_OUTPUT flag to direct
output to stdout for doctests.

We use the `package` sample to illustrate.

    >>> with Env({"CAPTURE_OUTPUT": "1"}):
    ...     gapi.package(cwd=sample("projects/package"))
    running bdist_wheel
    running build
    running build_py
    ...

## Select Run

Use `select` to select a run using some criteria.

    >>> run_1 = gapi.select("1", guild_home=gh)

    >>> run_1.id == latest_run.id, (run_1, latest_run)
    (True, ...)

## Runs Delete

Delete runs using `runs_delete`.

The function takes the same argument as the command.

Runs may be specified using run IDs:

    >>> gapi.runs_delete([latest_run.id], guild_home=gh)
    Deleted 1 run(s)

Or indexes:

    >>> gapi.runs_delete(["1"], guild_home=gh)
    Deleted 1 run(s)

If arguments aren't specified, all runs are deleted.

    >>> gapi.runs_delete(guild_home=gh)
    Deleted 1 run(s)
