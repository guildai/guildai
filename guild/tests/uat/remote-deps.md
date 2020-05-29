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

    >> run("guild run downstream -r guild-uat", timeout=15)

Run downstream again:

    >> run("guild run downstream -r guild-uat -y")

    >> TODO
