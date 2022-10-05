# Dependencies 4

These tests cover optional dependencies, added in 0.8.2.

Tests use the `resources-3` project.

    >>> cd(sample("projects", "resources-3"))

Use an isolated Guild env.

    >>> set_guild_home(mkdtemp())

Verify project operations.

    >>> run("guild ops")
    missing-file
    self-ref
    <exit 0>

The env is empty.

    >>> run("guild runs")
    <exit 0>

The `missing-file` operation defines a dependency on a single missing
file. The source is marked as optional.

    >>> run("guild run missing-file -y")
    Resolving file:missing.txt dependency
    Could not resolve file:missing.txt - skipping because dependency is optional
    <exit 0>

A successful run is generated.

    >>> run("guild runs")
    [1:...]  missing-file  ...  completed
    <exit 0>

The debug option can be used to show resolution error detail.

    >>> run("guild --debug run missing-file -y")
    ???
    Resolving file:missing.txt dependency
    DEBUG: [guild] could not resolve 'file:missing.txt' in file:missing.txt
    resource: cannot find source file 'missing.txt'
    Could not resolve file:missing.txt - skipping because dependency is optional
    ...
    <exit 0>

The `self-ref` operation requires a run of 'self-ref'. It is also
marked as optional.

    >>> run("guild run self-ref -y")
    Resolving self-ref dependency
    Could not resolve operation:self-ref - skipping because dependency is optional
    file not found - creating
    <exit 0>

A successful run is generated.

    >>> run("guild runs -n1")
    [1:...]  self-ref  ...  completed
    <exit 0>

The run generated a new 'file'.

    >>> run("guild ls -n")
    file
    <exit 0>

When we run `self-ref` again, it finds a required run and links 'file'.

    >>> run("guild run self-ref -y")
    Resolving self-ref dependency
    Using run ... for self-ref resource
    file found
    <exit 0>

    >>> run("guild ls -n")
    file
    <exit 0>
