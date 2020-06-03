# Staged error

These tests illustrate the behavior of a dependency error for a staged
run.

Delete runs in preparation:

    >>> quiet("guild runs rm -y")

Let's create a simple operation that will fail when started. It fails
due to a dependency resolution error.

    >>> project_dir = mkdtemp()
    >>> write(path(project_dir, "guild.yml"), """
    ... upstream: guild.pass
    ... downstream:
    ...   main: guild.pass
    ...   requires:
    ...     - operation: upstream
    ... """)

    >>> cd(project_dir)

Stage the downstream op:

    >>> run("guild run downstream --stage -y")
    WARNING: cannot find a suitable run for required resource 'upstream'
    Resolving upstream dependency
    Skipping resolution of operation:upstream because it's being staged
    downstream staged as ...
    To start the operation, use 'guild run --start ...'
    <exit 0>

The runs:

    >>> run("guild runs")
    [1:...]  downstream  ...  staged
    <exit 0>

Start the staged run:

    >>> run("guild run --start `guild select` -y")
    Resolving upstream dependency
    guild: run failed because a dependency was not met: could not resolve
    'operation:upstream' in upstream resource: no suitable run for upstream
    <exit 1>

The runs:

    >>> run("guild runs")
    [1:...]  downstream  ...  error
    <exit 0>
