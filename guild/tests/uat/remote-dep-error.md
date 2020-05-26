# Remote Dependency Error

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
    ... """)

    >>> cd(project_dir)

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
