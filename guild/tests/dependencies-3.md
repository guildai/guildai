# Dependencies 3

This is a continuation of the dependencies test. Tests below run
operations to verify expected functionality.

Tests use the `resources-2` project.

    >>> cd(sample("projects", "resources-2"))

Use an isolated Guild env.

    >>> env = {"GUILD_HOME": mkdtemp()}

    >>> _run = run

    >>> def run(*args, **kw):
    ...     return _run(*args, env=env, **kw)

Verify project operations.

    >>> run("guild ops")
    no-replace-dep-copy
    no-replace-dep-link
    replace-dep-copy
    replace-dep-link
    <exit 0>

## Replacing existing resources

When a file is resolved and already exists for a run, Guild logs a
warning message and skips the file by default. The operations
`no-replace-dep-*` are configured to copy a file as both source code
and as a dependency. The file is first copied as source code and then
resolved as a dependency. Because the resource is configured to not
replace existing, Guild prints a wanting and skips the resolution.

Link target version:

    >>> run("guild run no-replace-dep-link -y")
    Resolving file:file-1 dependency
    WARNING: .../file-1 already exists, skipping link
    <exit 0>

Copy target version:

    >>> run("guild run no-replace-dep-copy -y")
    Resolving file:file-1 dependency
    WARNING: .../file-1 already exists, skipping copy
    <exit 0>

The `replace-dep-*` operations set `replace-existing` to true. In both
cases Guild overwrites the source code copies.

Link target version:

    >>> run("guild run replace-dep-link -y")
    Resolving file:file-1 dependency
    <exit 0>

Copy target version:

    >>> run("guild run replace-dep-copy -y")
    Resolving file:file-1 dependency
    <exit 0>
