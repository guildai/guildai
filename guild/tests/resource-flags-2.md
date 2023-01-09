# Resource flags 2

These tests focus on the multi source operations in the
`resource-flags` project.

    >>> use_project("resource-flags")

## Source defaults

The `multi-source` operation defines two sources: one for a file and
another for an operation. It does not provide additional name or flag
info for these dependencies.

Operation dependencies are automatically promoted to flag defs unless
otherwise specified.

    >>> run("guild run multi-source --help-op")
    Usage: guild run [OPTIONS] multi-source [FLAG]...
    Flags:
      operation:upstream

The default operation behavior:

    >>> run("guild run multi-source -y")
    WARNING: cannot find a suitable run for required resource 'operation:upstream'
    Resolving file:foo.txt
    Resolving operation:upstream
    guild: run failed because a dependency was not met: could not resolve
    'operation:upstream' in operation:upstream resource: no suitable run for
    upstream
    <exit 1>

Let's provide the required `upstream` run.

    >>> run("guild run upstream -y")
    <exit 0>

    >>> run("guild run multi-source -y")
    Resolving file:foo.txt
    Resolving operation:upstream
    Using run ... for operation:upstream
    <exit 0>

    >>> run("guild runs -s")
    [1]  multi-source  completed  operation:upstream=...
    [2]  upstream      completed
    [3]  multi-source  error

    >>> run("guild ls -n")
    foo.txt
    guild.yml

Because the file source does not provide a flag name, we cannot change
the fila using flag syntax.

    >>> run("guild run multi-source file:foo.txt=bar.txt -y")
    guild: unsupported flag 'file:foo.txt'
    Try 'guild run multi-source --help-op' for a list of flags or
    use --force-flags to skip this check.
    <exit 1>

However, we can force the flag assignment, which will be used to
configure the source.

    >>> run("guild run multi-source file:foo.txt=bar.txt --force-flags -y")
    Resolving file:foo.txt
    Using bar.txt for file:foo.txt
    Resolving operation:upstream
    Using run ... for operation:upstream
    --file:foo.txt bar.txt

    >>> run("guild runs -s")
    [1]  multi-source  completed  file:foo.txt=bar.txt operation:upstream=...
    [2]  multi-source  completed  operation:upstream=...
    [3]  upstream      completed
    [4]  multi-source  error

    >>> run("guild ls -n")
    bar.txt
    guild.yml

Operations, on the other hand, are automatically exposed as flags. The
flag is named using the canonical source name (its URI)

    >>> first_upstream_run = run_capture("guild select -Fo upstream")

    >>> run(f"guild run multi-source operation:upstream={first_upstream_run} -y")
    Resolving file:foo.txt
    Resolving operation:upstream
    Using run ... for operation:upstream
    <exit 0>

    >>> run("guild runs -s")
    [1]  multi-source  completed  operation:upstream=...

The generated flag def uses an alias, which lets us specify only the
operation name.

    >>> run(f"guild run multi-source upstream={first_upstream_run} -y")
    Resolving file:foo.txt
    Resolving operation:upstream
    Using run ... for operation:upstream
    <exit 0>

    >>> run("guild runs -s -n1")
    [1]  multi-source  completed  operation:upstream=...

## Named sources

When source are named, users must use the specified source name when
overriding default values.

`multi-source-with-name` adds names to the two sources --- the
operation is named using `name` and the file is named using
`flag-name`.

    >>> run("guild run multi-source-with-names --help-op")
    Usage: guild run [OPTIONS] multi-source-with-names [FLAG]...
    Flags:
      infile        (default is foo.txt)
      upstream-run

If we try to use URIs to specify source config, Guild fails with an
error message.

    >>> run("guild run multi-source-with-names file:foo.txt=xxx -y")
    guild: unsupported flag 'file:foo.txt'
    Try 'guild run multi-source-with-names --help-op' for a list of flags
    or use --force-flags to skip this check.
    <exit 1>

    >>> run("guild run multi-source-with-names operation:upstream=xxx -y")
    guild: unsupported flag 'operation:upstream'
    Try 'guild run multi-source-with-names --help-op' for a list of flags
    or use --force-flags to skip this check.
    <exit 1>

We must use the source names.

    >>> run(
    ...     "guild run multi-source-with-names "
    ...     f"infile=bar.txt upstream-run={first_upstream_run} -y"
    ... )
    Resolving infile
    Using bar.txt for infile
    Resolving upstream-run
    Using run ... for upstream-run
    <exit 0>

    >>> run("guild runs -s -n1")
    [1]  multi-source-with-names  completed  infile=bar.txt upstream-run=...
    <exit 0>

    >>> run("guild ls -n")
    bar.txt
    guild.yml
