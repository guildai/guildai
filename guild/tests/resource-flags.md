# Resource flags

Guild provides a flag-like interface to specify alternative resource
sources or source locations. For example, a user may specify a
specific run for an operation dependency using the resource name or
a flag name configured for the dependency.

We use the `resource-flags` project for our tests.

    >>> gh = mkdtemp()
    >>> use_project("resource-flags", gh)

For reference, the project defines a simple operation that defines a
flag but does not require resource. This shows how real flags are
used.

    >>> run("guild run flag --help-op")
    Usage: guild run [OPTIONS] flag [FLAG]...
    Flags:
      foo  (default is 123)

    >>> run("guild run flag -y")
    --foo 123

## Basic resource defs

The `file-source` requires a single file.

    >>> run("guild run file-source --help-op")
    Usage: guild run [OPTIONS] file-source [FLAG]...
    <BLANKLINE>
    Use 'guild run --help' for a list of options.

The default resolved file is `foo.txt`.

    >>> run("guild run file-source -y")
    Resolving file:foo.txt

    >>> run("guild ls -n")
    foo.txt
    guild.yml

The Guild-generated identifiers for the resource and the resource
source are both `file:foo.txt`.

    >>> run("guild select --attr deps")
    file:foo.txt:
      file:foo.txt:
        paths:
          - .../samples/projects/resource-flags/foo.txt
          uri: file:foo.txt

We can use the resource URI as a flag name to set an alternative
source value.

    >>> run("guild run file-source file:foo.txt=bar.txt -y")
    Resolving file:foo.txt
    Using bar.txt for file:foo.txt
    --file:foo.txt bar.txt

    >>> run("guild ls -n")
    bar.txt
    guild.yml

## Named sources

The `file-source-with-name` operation defines a `name` attribute for
the resource source.

As with the previous example, Guild does not include this flag-like
setting in operation help.

    >>> run("guild run file-source-with-name --help-op")
    Usage: guild run [OPTIONS] file-source-with-name [FLAG]...
    <BLANKLINE>
    Single named file source
    <BLANKLINE>
    Use 'guild run --help' for a list of options.

The operation uses the source name when logging the resource
resolution. The default file is `foo.txt`.

    >>> run("guild run file-source-with-name -y")
    Resolving infile

    >>> run("guild ls -n")
    foo.txt
    guild.yml

Guild uses the source name as the resource name in this case.

    >>> run("guild select --attr deps")
    infile:
      infile:
        paths:
        - .../samples/projects/resource-flags/foo.txt
        uri: file:foo.txt

We can specify an alternative source using the source name.

    >>> run("guild run file-source-with-name infile=bar.txt -y")
    Resolving infile
    Using bar.txt for infile
    --infile bar.txt

    >>> run("guild ls -n")
    bar.txt
    guild.yml

The source URI is no longer an accepted assignment.

    >>> run("guild run file-source-with-name file:foo.txt=bar.txt -y")
    guild: unsupported flag 'file:foo.txt'
    Try 'guild run file-source-with-name --help-op' for a list of flags or
    use --force-flags to skip this check.
    <exit 1>

Note, we can use `--force-flags` to override this and push the
assignment through to the operation.

    >>> run("guild run file-source-with-name file:foo.txt=bar.txt --force-flags -y")
    Resolving infile
    --file:foo.txt bar.txt

In this case the resource and source names are still defined according
to the Guild file config and not the flag assignment.

    >>> run("guild select --attr deps")
    infile:
      infile:
        paths:
        - .../samples/projects/resource-flags/foo.txt
        uri: file:foo.txt

## Named resources with named sources

A resource can have a defined name, in which case that value is used
for logged messages. It is not used for source flag-assignments.

`file-source-with-name-2` is the same as `file-source-with-name` but
the resource is explicitly named as 'dependencies'.

We still set the source using the source name.

    >>> run("guild run file-source-with-name-2 infile=bar.txt -y")
    Resolving dependencies
    Using bar.txt for infile
    --infile bar.txt

Note that Guild resolves 'dependencies' in this case.

We cannot use `dependencies` in an assignment.

    >>> run("guild run file-source-with-name-2 dependencies=bar.txt -y")
    guild: unsupported flag 'dependencies'
    Try 'guild run file-source-with-name-2 --help-op' for a list of flags or
    use --force-flags to skip this check.
    <exit 1>

## Flag-named sources

Guild differentiates between a source *name* and a source *flag
name*. The source name is used when logging source-related
messages. The flag name is used as the flag interface.

If `flag-name` is specified but `name` is not, Guild uses `flag-name`
as the source name. If `name` is specified but `flag-name` is not,
Guild uses `name` as the flag name (see previous example).

`file-source-with-flag-name` defines a `flag-name` attribute for its
source.

However, this does not cause Guild to show any information about this
source in the operation help.

    >>> run("guild run file-source-with-flag-name --help-op")
    Usage: guild run [OPTIONS] file-source-with-flag-name [FLAG]...
    <BLANKLINE>
    Single file source with a flag name
    <BLANKLINE>
    Use 'guild run --help' for a list of options.

Guild uses the source flag name for the resource name by default.

    >>> run("guild run file-source-with-flag-name -y")
    Resolving infile

    >>> run("guild ls -n")
    foo.txt
    guild.yml

The source name is used as the default resource name.

    >>> run("guild select --attr deps")
    infile:
      infile:
        paths:
        - .../samples/projects/resource-flags/foo.txt
        uri: file:foo.txt

The source name is used to specify a different file for the
dependency.

    >>> run("guild run file-source-with-flag-name infile=bar.txt -y")
    Resolving infile
    Using bar.txt for infile
    --infile bar.txt

    >>> run("guild ls -n")
    bar.txt
    guild.yml

`file-source-with-name-and-flag-name` defines both a name and a flag
name for a resource source. As described above, Guild uses the `name`
attribute in logged messages. Users must use the flag name when
specifying alternative source values.

    >>> run("guild run file-source-with-name-and-flag-name -y")
    Resolving file

    >>> run("guild ls -n")
    foo.txt
    guild.yml

To use a different source, we must use the source flag name.

    >>> run("guild run file-source-with-name-and-flag-name input-file=bar.txt -y")
    Resolving file
    Using bar.txt for file
    --input-file bar.txt

    >>> run("guild ls -n")
    bar.txt
    guild.yml

    >>> run("guild select --attr deps")
    file:
      file:
        config: bar.txt
        paths:
        - .../samples/projects/resource-flags/bar.txt
        uri: file:foo.txt

We cannot use the source name when a flag name is defined for a
source.

    >>> run("guild run file-source-with-name-and-flag-name file=bar.txt -y")
    guild: unsupported flag 'file'
    Try 'guild run file-source-with-name-and-flag-name --help-op'
    for a list of flags or use --force-flags to skip this check.
    <exit 1>

## Explicit flags and resources

The `file-source-with-flag` operation defines a flag for a resource
source. The flag is associated with the source by the source `name`
attribute, which must equal the flag name.

With the explicit flag definition, Guild shows help for the flag.

    >>> run("guild run file-source-with-flag --help-op")
    Usage: guild run [OPTIONS] file-source-with-flag [FLAG]...
    <BLANKLINE>
    Single file source associated with a flag def
    <BLANKLINE>
    Use 'guild run --help' for a list of options.
    <BLANKLINE>
    Flags:
      infile  Path to infile (default is foo.txt)

By default `foo.txt` is resolved as the dependency.

    >>> run("guild run file-source-with-flag -y")
    Resolving infile
    Using foo.txt for infile
    --infile foo.txt

    >>> run("guild ls -n")
    foo.txt
    guild.yml

The `inline` flag is used to change the resolved source.

    >>> run("guild run file-source-with-flag infile=bar.txt -y")
    Resolving infile
    Using bar.txt for infile
    --infile bar.txt

    >>> run("guild ls -n")
    bar.txt
    guild.yml

## Operaiton source

The `op-source` operation requires the `upstream` operation.

As with other resources, this information is not provided in operation
help.

    >>> run("guild run op-source --help-op")
    Usage: guild run [OPTIONS] op-source [FLAG]...
    <BLANKLINE>
    Single unnamed operation source
    <BLANKLINE>
    Use 'guild run --help' for a list of options.

There are no `upstream` runs currently so the operation fails.

    >>> run("guild runs -Fo upstream -s")
    <exit 0>

    >>> run("guild run op-source -y")
    WARNING: cannot find a suitable run for required resource 'operation:upstream'
    Resolving operation:upstream
    guild: run failed because a dependency was not met: could not resolve
    'operation:upstream' in operation:upstream resource: no suitable run for upstream
    <exit 1>

Let's generate an `upstream` run.

    >>> run("guild run upstream -y")
    <exit 0>

And run `op-source` again.

    >>> run("guild run op-source -y")
    Resolving operation:upstream
    Using run ... for operation:upstream

Let's verify that the resolved `upstream` run is what we
expect. Here's a helper function that checks this:

    >>> def assert_resolved_run(
    ...     expected_run_select,
    ...     source_name="operation:upstream",
    ...     resource_name=None
    ... ):
    ...     resource_name = resource_name or source_name
    ...     expected_run_id = run_capture(f"guild select {expected_run_select}")
    ...     deps = yaml.safe_load(run_capture("guild select --attr deps"))
    ...     try:
    ...         actual_run_id = deps[resource_name][source_name]["config"]
    ...     except KeyError:
    ...         raise AssertionError((deps, gh)) from None
    ...     assert actual_run_id == expected_run_id, (expected_run_id, deps, gh)

Confirm that the resolved run is the latest `upstream`:

    >>> assert_resolved_run("-Fo upstream")

We can specify the run for the operation dependency using the
operation name `upstream`.

Let's first get the first `upstream` run ID.

    >>> first_upstream_run = run_capture("guild select -Fo upstream")

Run `op-source` with an explicit run ID using as assignment to
`upstream`.

    >>> run(f"guild run op-source upstream={first_upstream_run} -y")
    Resolving operation:upstream
    Using run ... for operation:upstream
    --upstream ...

    >>> assert_resolved_run(first_upstream_run)

We can also use the qualified name `operation:upstream` for the
operation dependency.

    >>> run(f"guild run op-source operation:upstream={first_upstream_run} -y")
    Resolving operation:upstream
    Using run ... for operation:upstream

    >>> assert_resolved_run(first_upstream_run)

## Named operation source

The operation `op-source-with-name` is the same as `op-source` but it
provides a name for the operation dependency.

Here are the current `upstream` runs:

    >>> run("guild runs -Fo upstream -s")
    [1]  upstream  completed

Let's create another run so we can resolve more than one possible
upstream run.

    >>> run("guild run upstream -y")
    <exit 0>

Run `op-source-with-name` using the defaults.

    >>> run("guild run op-source-with-name -y")
    Resolving upstream-run
    Using run ... for upstream-run

The resolved deps uses the source name.

    >>> run("guild select --attr deps")
    upstream-run:
      upstream-run:
        config: ...
        paths: []
        uri: operation:upstream

    >>> assert_resolved_run("-Fo upstream", "upstream-run")

## Operation source with flag name

`op-source-with-flag-name` specifies a flag name for the operation
source.

This information does not appear in operation help.

    >>> run("guild run op-source-with-flag-name --help-op")
    Usage: guild run [OPTIONS] op-source-with-flag-name [FLAG]...
    <BLANKLINE>
    Single unnamed operation with a flag name
    <BLANKLINE>
    Use 'guild run --help' for a list of options.

We can use the flag name to specify a run.

    >>> run(f"guild run op-source-with-flag-name upstream-run={first_upstream_run} -y")
    Resolving upstream-run
    Using run ... for upstream-run

    >>> run("guild select --attr deps")
    upstream-run:
      upstream-run:
        config: ...
        paths: []
        uri: operation:upstream

    >>> assert_resolved_run(first_upstream_run, "upstream-run")

We cannot use the default flag names because the explicitly defined
flag name specifies the interface.

    >>> run("guild run op-source-with-flag-name upstream={first_upstream_run} -y")
    guild: unsupported flag 'upstream'
    Try 'guild run op-source-with-flag-name --help-op' for a list of flags
    or use --force-flags to skip this check.
    <exit 1>

    >>> run("guild run op-source-with-flag-name operation:upstream={first_upstream_run} -y")
    guild: unsupported flag 'operation:upstream'
    Try 'guild run op-source-with-flag-name --help-op' for a list of flags
    or use --force-flags to skip this check.
    <exit 1>

## Exposing required operation with flags

`op-source-with-flag` specifies a flag def that's associated with a
resource source.

In this case, the flag info is shown in operation help.

    >>> run("guild run op-source-with-flag --help-op")
    Usage: guild run [OPTIONS] op-source-with-flag [FLAG]...
    <BLANKLINE>
    Single operation associated with a flag def
    <BLANKLINE>
    Use 'guild run --help' for a list of options.
    <BLANKLINE>
    Flags:
      upstream  Run ID for upstream run (defaults to latest non-error run)

We use the flag name to specify the upstream run.

    >>> run(f"guild run op-source-with-flag upstream={first_upstream_run} -y")
    Resolving operation:upstream
    Using run ... for operation:upstream
    --upstream ...

    >>> run("guild select --attr deps")
    operation:upstream:
      operation:upstream:
        config: ...
        paths: []
        uri: operation:upstream

    >>> assert_resolved_run(first_upstream_run)

We can alternatively use the fully qualified default source name
`operation:upstream`.

    >>> run("guild run op-source-with-flag operation:upstream=xxx -y")
    WARNING: cannot find a suitable run for required resource 'operation:upstream'
    Resolving operation:upstream
    guild: run failed because a dependency was not met: could not resolve
    'operation:upstream' in operation:upstream resource: no suitable run for
    upstream
    <exit 1>
