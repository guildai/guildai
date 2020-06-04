# Remote Dependencies

These tests illustate Guild behavior when running operations with
dependencies remotely.

Delete remote runs in preparation for tests.

    >>> quiet("guild runs rm -y -r guild-uat")

Guild resolves dependencies while running remote operations in the
foreground so that any dependency errors are generated before the
operation is put in the background.

Let's use a simple project with an operation dependency as an example.

    >>> project_dir = mkdtemp()

    >>> write(path(project_dir, "guild.yml"), """
    ... upstream: guild.pass
    ... downstream:
    ...   main: guild.pass
    ...   requires:
    ...    - operation: upstream
    ...      warn-if-empty: no
    ... """)

    >>> cd(project_dir)

Verify that there are no runs to satisfy downstream requirements:

    >>> run("guild runs -r guild-uat")
    <BLANKLINE>
    <exit 0>

Run the downstream op without an upstream op, which is required:

    >>> run("guild run downstream -r guild-uat -y")
    Getting remote run info
    WARNING: cannot find a suitable run for required resource 'upstream'
    Building package
    ...
    Starting downstream on guild-uat as ...
    WARNING: cannot find a suitable run for required resource 'upstream'
    Resolving upstream dependency
    guild: run failed because a dependency was not met: could not resolve
    'operation:upstream' in upstream resource: no suitable run for upstream
    <exit 1>

Let's run a remote upstream operation:

    >>> run("guild run upstream -r guild-uat -y")
    Building package
    ...
    Successfully installed ...
    Starting upstream on guild-uat as ...
    Run ... stopped with a status of 'completed'
    <exit 0>

Verify that we now have an upstream run:

    >>> run("guild runs -r guild-uat")
    [1:...]  gpkg.anonymous-.../upstream    ...  completed
    [2:...]  gpkg.anonymous-.../downstream  ...  error
    <exit 0>

Show run preview to confirm that Guild is finding the remote upstream
to provide as a default value.

    >>> run("guild run downstream -r guild-uat", timeout=5)
    Getting remote run info
    You are about to run downstream on guild-uat
      upstream: ...
    Continue? (Y/n)
    <exit -9>

Run downstream again:

    >>> run("guild run downstream -r guild-uat -y")
    Getting remote run info
    Building package
    ...
    Successfully installed gpkg.anonymous-...-0.0.0
    Starting downstream on guild-uat as ...
    Resolving upstream dependency
    Using run ... for upstream resource
    Run ... stopped with a status of 'completed'
    <exit 0>

Remote runs:

    >>> run("guild runs -r guild-uat")
    [1:...]  gpkg.anonymous-.../downstream  ...  completed  upstream=...
    [2:...]  gpkg.anonymous-.../upstream    ...  completed
    [3:...]  gpkg.anonymous-.../downstream  ...  error
    <exit 0>

Specify an invalid upstream run ID reference:

    >>> run("guild run downstream upstream=xxx -r guild-uat", timeout=5)
    Getting remote run info
    WARNING: cannot find a suitable run for required resource 'upstream'
    You are about to run downstream on guild-uat
      upstream: xxx
    Continue? (Y/n)
    <exit -9>

If we let this invalid value pass through, Guild runs the operation,
but it fails.

    >>> run("guild run downstream upstream=xxx -r guild-uat -y")
    Getting remote run info
    WARNING: cannot find a suitable run for required resource 'upstream'
    Building package
    ...
    Successfully installed gpkg.anonymous-...-0.0.0
    Starting downstream on guild-uat as ...
    WARNING: cannot find a suitable run for required resource 'upstream'
    Resolving upstream dependency
    guild: run failed because a dependency was not met: could not resolve
    'operation:upstream' in upstream resource: no suitable run for upstream
    <exit 1>
