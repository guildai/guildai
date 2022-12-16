# Dependencies 3

This is a continuation of the dependencies test. Tests below run
operations to verify expected functionality.

Tests use the `resources-2` project.

    >>> cd(sample("projects", "resources-2"))

Use an isolated Guild env.

    >>> set_guild_home(mkdtemp())

Verify project operations.

    >>> run("guild ops")
    no-replace-dep-copy
    no-replace-dep-link
    replace-dep-copy
    replace-dep-link
    resolve-twice
    <exit 0>

## Resolving twice

If a resource is resolved again, Guild skips the second resolution and
prints a warning message.

    >>> run("guild run resolve-twice -y")
    Resolving file:file-1
    Resolving file:file-1
    Skipping resolution of file:file-1 because it's already resolved
    <exit 0>

## Replacing existing resources

When a file is resolved and already exists for a run, Guild logs a
warning message and skips the file by default. The operations
`no-replace-dep-*` are configured to resolve two resources to the same
target. The second resource is configured to skip the resolution on
conflict.

Link target version:

    >>> run("guild run no-replace-dep-link -y")
    Resolving file:file-0
    Resolving file:file-1
    WARNING: .../file-1 already exists, skipping link
    <exit 0>

Copy target version:

    >>> run("guild run no-replace-dep-copy -y")
    Resolving file:file-0
    Resolving file:file-1
    WARNING: .../file-1 already exists, skipping copy
    <exit 0>

The `replace-dep-*` operations set `replace-existing` to true. In both
cases Guild overwrites the source code copies.

Link target version:

    >>> run("guild run replace-dep-link -y")
    Resolving file:file-0
    Resolving file:file-1
    <exit 0>

Copy target version:

    >>> run("guild run replace-dep-copy -y")
    Resolving file:file-0
    Resolving file:file-1
    <exit 0>
