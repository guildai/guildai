# Dependencies 4

These tests cover optional dependencies, added in 0.8.2.

Tests use the `resources-3` project.

    >>> use_project("resources-3")

Verify project operations.

    >>> run("guild ops")
    missing-file
    self-ref

The `missing-file` operation defines a dependency on a single missing file. The
source is marked as optional.

    >>> run("guild run missing-file -y")
    Resolving file:missing.txt
    Could not resolve file:missing.txt - skipping because dependency is optional

The run succeeds.

    >>> run("guild runs -s")
    [1]  missing-file  completed

The debug option can be used to show resolution error detail.

    >>> run("guild --debug run missing-file -y")
    ???
    Resolving file:missing.txt
    DEBUG: [guild] could not resolve 'file:missing.txt' in file:missing.txt
    resource: cannot find source file 'missing.txt'
    Could not resolve file:missing.txt - skipping because dependency is optional
    ...
    <exit 0>

The `self-ref` operation requires a run of 'self-ref'. It is also marked as
optional.

    >>> run("guild run self-ref -y")
    Resolving operation:self-ref
    Could not resolve operation:self-ref - skipping because dependency is optional
    file not found - creating

    >>> run("guild runs -sn1")
    [1]  self-ref  completed

The run generated a new 'file'.

    >>> run("guild ls -ng")
    file

When we run `self-ref` again, it finds a required run and links 'file'.

    >>> run("guild run self-ref -y")
    Resolving operation:self-ref
    Using run ... for operation:self-ref
    file found

We can see resolved dependencies using the `-d/--dependencies` option to `ls`.

    >>> run("guild ls -nd")
    file
