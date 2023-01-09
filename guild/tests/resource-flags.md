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

The `file-source` requires a single file. It does not define
`flag-name` and so is not configurable using flag assignment.

    >>> run("guild run file-source --help-op")
    Usage: guild run [OPTIONS] file-source [FLAG]...
    <BLANKLINE>
    Use 'guild run --help' for a list of options.

The configured resolved file is `foo.txt`.

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

`file` resources cannot be reconfigured using flag assignments.

    >>> run("guild run file-source file:foo.txt=bar.txt -y")
    guild: unsupported flag 'file:foo.txt'
    Try 'guild run file-source --help-op' for a list of flags or use
    --force-flags to skip this check.
    <exit 1>

However, we can force a new value using the default source name and
`--force-flags`.

    >>> run("guild run file-source file:foo.txt=bar.txt --force-flags -y")
    Resolving file:foo.txt
    Using bar.txt for file:foo.txt
    --file:foo.txt bar.txt

The specified file is used when resolving the source.

    >>> run("guild ls -n")
    bar.txt
    guild.yml

This value is recorded in the run dependencies.

    >>> run("guild select --attr deps")
    file:foo.txt:
      file:foo.txt:
        config: bar.txt
        paths:
        - .../samples/projects/resource-flags/bar.txt
        uri: file:foo.txt

## Named sources

The `file-source-with-name` operation defines a `name` attribute for
the resource source.

The `name` attribute in this case is only used when describing the
source. It does not imply a resource flags.

    >>> run("guild run file-source-with-name --help-op")
    Usage: guild run [OPTIONS] file-source-with-name [FLAG]...
    <BLANKLINE>
    Single named file source
    <BLANKLINE>
    Use 'guild run --help' for a list of options.

The operation uses the source name when logging the resource
resolution.

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

We cannot specify an alternative source using the source name.

    >>> run("guild run file-source-with-name infile=bar.txt -y")
    guild: unsupported flag 'infile'
    Try 'guild run file-source-with-name --help-op' for a list of flags or
    use --force-flags to skip this check.
    <exit 1>

    >>> run("guild run file-source-with-name file:foo.txt=bar.txt -y")
    guild: unsupported flag 'file:foo.txt'
    Try 'guild run file-source-with-name --help-op' for a list of flags or
    use --force-flags to skip this check.
    <exit 1>

We can use `--force-flags` to override this and push the assignment
through to the operation. However, only the source name is applied
when resolving the source path.

If we force the URI as a flag, that value is passed through to the run
command.

    >>> run("guild run file-source-with-name file:foo.txt=bar.txt --force-flags -y")
    Resolving infile
    --file:foo.txt bar.txt

However, it has no effect on the source resolution. The default value
`foo.txt` is still used.

    >>> run("guild ls -n")
    foo.txt
    guild.yml

    >>> run("guild select --attr deps")
    infile:
      infile:
        paths:
        - .../samples/projects/resource-flags/foo.txt
        uri: file:foo.txt

When we use the resource name `infile`, the assigned value is
similarly passed to the run command.

    >>> run("guild run file-source-with-name infile=bar.txt --force-flags -y")
    Resolving infile
    Using bar.txt for infile
    --infile bar.txt

In this case, the value is used when resolving the source.

    >>> run("guild ls -n")
    bar.txt
    guild.yml

The modified source configuration and path is reflected in the run
dependencies.

    >>> run("guild select --attr deps")
    infile:
      infile:
        config: bar.txt
        paths:
        - .../samples/projects/resource-flags/bar.txt
        uri: file:foo.txt

## Named resources with named sources

A resource can have a defined name, in which case that value is used
for logged messages. It too cannot be used for source
flag-assignments.

`file-source-with-name-2` is the same as `file-source-with-name` but
the resource is named as 'dependencies'.

The resource name is used to describe the resource.

    >>> run("guild run file-source-with-name-2 -y")
    Resolving dependencies

This name is used when recording the dependencies.

    >>> run("guild select --attr deps")
    dependencies:
      infile:
        paths:
        - .../samples/projects/resource-flags/foo.txt
        uri: file:foo.txt

We cannot use `dependencies` in an assignment.

    >>> run("guild run file-source-with-name-2 dependencies=bar.txt -y")
    guild: unsupported flag 'dependencies'
    Try 'guild run file-source-with-name-2 --help-op' for a list of flags or
    use --force-flags to skip this check.
    <exit 1>

And we still can't set the source using the resource name.

    >>> run("guild run file-source-with-name-2 infile=bar.txt -y")
    guild: unsupported flag 'infile'
    Try 'guild run file-source-with-name-2 --help-op' for a list of flags or
    use --force-flags to skip this check.
    <exit 1>

## Flag-named sources

To enable flag assignment for a `file` resource, we need to provide a
`flag-name` source attribute. Guild differentiates between a source
*name* and a source *flag name*. The source name is used when logging
source-related messages. The flag name is used as the flag interface.

`file-source-with-flag-name` defines a `flag-name` attribute for its
source.

    >>> run("guild run file-source-with-flag-name --help-op")
    Usage: guild run [OPTIONS] file-source-with-flag-name [FLAG]...
    Flags:
      infile  (default is foo.txt)

Guild uses the source flag name for the resource name by default.

    >>> run("guild run file-source-with-flag-name -y")
    Resolving infile
    Using foo.txt for infile

    >>> run("guild ls -n")
    foo.txt
    guild.yml

The source name is used as the default resource name.

    >>> run("guild select --attr deps")
    infile:
      infile:
        config: foo.txt
        paths:
        - .../samples/projects/resource-flags/foo.txt
        uri: file:foo.txt

The source name is used to specify a different file for the
dependency.

    >>> run("guild run file-source-with-flag-name infile=bar.txt -y")
    Resolving infile
    Using bar.txt for infile

    >>> run("guild ls -n")
    bar.txt
    guild.yml

    >>> run("guild select --attr deps")
    infile:
      infile:
        config: bar.txt
        paths:
        - .../samples/projects/resource-flags/bar.txt
        uri: file:foo.txt

`file-source-with-name-and-flag-name` defines both a name and a flag
name for a resource source. As described above, Guild uses the `name`
attribute in logged messages. Users must use the flag name when
specifying alternative source values.

    >>> run("guild run file-source-with-name-and-flag-name --help-op")
    Usage: guild run [OPTIONS] file-source-with-name-and-flag-name [FLAG]...
    Flags:
      input-file  (default is foo.txt)

    >>> run("guild run file-source-with-name-and-flag-name -y")
    Resolving file
    Using foo.txt for file

    >>> run("guild ls -n")
    foo.txt
    guild.yml

To use a different source, we must use the source flag name.

    >>> run("guild run file-source-with-name-and-flag-name input-file=bar.txt -y")
    Resolving file
    Using bar.txt for file

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

The `file-source-with-flag` operation defines an explicit flag for a
resource source. The flag is associated with the source by the source
`flag-name` attribute, which must match the flag name.

Guild uses the explicit flag definition for help.

    >>> run("guild run file-source-with-flag --help-op")
    Usage: guild run [OPTIONS] file-source-with-flag [FLAG]...
    Flags:
      infile  Path to infile (default is foo.txt)

By default `foo.txt` is resolved as the dependency.

    >>> run("guild run file-source-with-flag -y")
    Resolving infile
    Using foo.txt for infile

    >>> run("guild ls -n")
    foo.txt
    guild.yml

    >>> run("guild select --attr deps")
    infile:
      infile:
        config: foo.txt
        paths:
        - .../samples/projects/resource-flags/foo.txt
        uri: file:foo.txt

The `inline` flag is used to change the resolved source.

    >>> run("guild run file-source-with-flag infile=bar.txt -y")
    Resolving infile
    Using bar.txt for infile

    >>> run("guild ls -n")
    bar.txt
    guild.yml

    >>> run("guild select --attr deps")
    infile:
      infile:
        config: bar.txt
        paths:
        - .../samples/projects/resource-flags/bar.txt
        uri: file:foo.txt

`file-source-with-flag-2` explicitly re-enables the flag argument,
which is otherwise implicitly disabled by the resource flag. It
renames the default arg name to `infile-path`. It also sets the flag
type to `path`, which has the effect of resolving the value as an
absoluate path.

    >>> run("guild run file-source-with-flag-2 -y")
    Resolving infile
    Using foo.txt for infile
    --infile-path .../samples/projects/resource-flags/foo.txt

    >>> run("guild ls -n")
    foo.txt
    guild.yml

Use an alternative path.

    >>> run("guild run file-source-with-flag-2 infile=bar.txt -y")
    Resolving infile
    Using bar.txt for infile
    --infile-path .../samples/projects/resource-flags/bar.txt

    >>> run("guild ls -n")
    bar.txt
    guild.yml

## Operation source

The `op-source` operation requires the `upstream` operation.

As with other resources, this information is not provided in operation
help.

    >>> run("guild run op-source --help-op")
    Usage: guild run [OPTIONS] op-source [FLAG]...
    Flags:
      operation:upstream

There are no `upstream` runs currently so the operation fails.

    >> run("guild runs -Fo upstream -s")
    <exit 0>

    >>> run("guild run op-source -y")
    WARNING: cannot find a suitable run for required resource 'operation:upstream'
    Resolving operation:upstream
    guild: run failed because a dependency was not met: could not resolve
    'operation:upstream' in operation:upstream resource: no suitable run for upstream
    <exit 1>

Generate an `upstream` run.

    >>> run("guild run upstream -y")
    <exit 0>

Run `op-source` again.

    >>> run("guild run op-source -y")
    Resolving operation:upstream
    Using run ... for operation:upstream

Verify that the resolved `upstream` run is what we expect. Here's a
helper function that checks this:

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

    >>> assert_resolved_run(first_upstream_run)

We can also use the qualified name `operation:upstream` for the
operation dependency.

    >>> run(f"guild run op-source operation:upstream={first_upstream_run} -y")
    Resolving operation:upstream
    Using run ... for operation:upstream

    >>> assert_resolved_run(first_upstream_run)

## Named operation source

The operation `op-source-with-name` is the same as `op-source` but it
provides a name for the operation dependency. The name is used for the
flag name.

    >>> run("guild run op-source-with-name --help-op")
    Usage: guild run [OPTIONS] op-source-with-name [FLAG]...
    Flags:
      the-upstream-run

The current `upstream` runs:

    >>> run("guild runs -Fo upstream -s")
    [1]  upstream  completed

Create another run so we can resolve more than one possible upstream
run.

    >>> run("guild run upstream -y")
    <exit 0>

    >>> run("guild runs -Fo upstream -s")
    [1]  upstream  completed
    [2]  upstream  completed

Run `op-source-with-name` using the defaults.

    >>> run("guild run op-source-with-name -y")
    Resolving the-upstream-run
    Using run ... for the-upstream-run

The resolved deps uses the source name.

    >>> run("guild select --attr deps")
    the-upstream-run:
      the-upstream-run:
        config: ...
        paths: []
        uri: operation:upstream

    >>> assert_resolved_run("-Fo upstream", "the-upstream-run")

Generate another run using the first upstream run.

    >>> run(f"guild run op-source-with-name the-upstream-run={first_upstream_run} -y")
    Resolving the-upstream-run
    Using run ... for the-upstream-run

    >>> assert_resolved_run(first_upstream_run, "the-upstream-run")

With an explicitly configure source name, we can no longer use the
operation name as flags.

    >>> run(f"guild run op-source-with-name operation:upstream={first_upstream_run} -y")
    guild: unsupported flag 'operation:upstream'
    Try 'guild run op-source-with-name --help-op' for a list of flags or
    use --force-flags to skip this check.
    <exit 1>

    >>> run(f"guild run op-source-with-name upstream={first_upstream_run} -y")
    guild: unsupported flag 'upstream'
    Try 'guild run op-source-with-name --help-op' for a list of flags or
    use --force-flags to skip this check.
    <exit 1>

## Operation source with flag name

`op-source-with-flag-name` specifies a flag name for the operation
source.

    >>> run("guild run op-source-with-flag-name --help-op")
    Usage: guild run [OPTIONS] op-source-with-flag-name [FLAG]...
    Flags:
      upstream-run

Use the flag name to specify a run.

    >>> run(f"guild run op-source-with-flag-name upstream-run={first_upstream_run} -y")
    Resolving upstream-run
    Using run ... for upstream-run

    >>> assert_resolved_run(first_upstream_run, "upstream-run")

Note the flag name is used as the resource name in user messages. It's
also used as the name when recording the dependency.

    >>> run("guild select --attr deps")
    upstream-run:
      upstream-run:
        config: ...
        paths: []
        uri: operation:upstream

We cannot use the default flag names because the explicitly defined
flag name specifies the interface.

    >>> run("guild run op-source-with-flag-name operation:upstream={first_upstream_run} -y")
    guild: unsupported flag 'operation:upstream'
    Try 'guild run op-source-with-flag-name --help-op' for a list of flags or
    use --force-flags to skip this check.
    <exit 1>

    >>> run("guild run op-source-with-flag-name upstream={first_upstream_run} -y")
    guild: unsupported flag 'upstream'
    Try 'guild run op-source-with-flag-name --help-op' for a list of flags or
    use --force-flags to skip this check.
    <exit 1>

## Operation source with name and flag name

The operation `op-source-with-name-and-flag-name` defines both a name
and a flag name.

The flag name is used for the flag interface.

    >>> run("guild run op-source-with-name-and-flag-name --help-op")
    Usage: guild run [OPTIONS] op-source-with-name-and-flag-name [FLAG]...
    Flags:
      upstream-flag-name

    >>> run(f"guild run op-source-with-name-and-flag-name upstream-flag-name={first_upstream_run} -y")
    Resolving upstream-name
    Using run ... for upstream-name

The source name is used when recording the dependency.

    >>> run("guild select --attr deps")
    upstream-name:
      upstream-name:
        config: ...
        paths: []
        uri: operation:upstream

We cannot use the source name as a flag.

    >>> run(f"guild run op-source-with-name-and-flag-name upstream-name={first_upstream_run} -y")
    guild: unsupported flag 'upstream-name'
    Try 'guild run op-source-with-name-and-flag-name --help-op' for a list of flags or
    use --force-flags to skip this check.
    <exit 1>

## Exposing required operation with flags

`op-source-with-flag` specifies a flag def that's associated with a
resource source.

    >>> run("guild run op-source-with-flag --help-op")
    Usage: guild run [OPTIONS] op-source-with-flag [FLAG]...
    Flags:
      operation:upstream  Run ID for upstream run (defaults to
                          latest non-error run)

We use the flag name to specify the upstream run.

    >>> run(f"guild run op-source-with-flag operation:upstream={first_upstream_run} -y")
    Resolving operation:upstream
    Using run ... for operation:upstream

    >>> assert_resolved_run(first_upstream_run)

    >>> run("guild select --attr deps")
    operation:upstream:
      operation:upstream:
        config: ...
        paths: []
        uri: operation:upstream

Because the user provides an explicit flag definition - and that
definition does not provide an alias - we cannot use the flag name
`upstream`.

    >>> run("guild run op-source-with-flag upstream=xxx -y")
    guild: unsupported flag 'upstream'
    Try 'guild run op-source-with-flag --help-op' for a list of flags or
    use --force-flags to skip this check.
    <exit 1>

`op-source-with-flag-2` provides a source name `upstream`, which is
used for the flag name.

    >>> run("guild run op-source-with-flag-2 --help-op")
    Usage: guild run [OPTIONS] op-source-with-flag-2 [FLAG]...
    Flags:
      upstream  Run ID for upstream run (defaults to latest non-error run)

The operation explicitly enables the operation argument with
`arg-skip: no`. This causes Guild to pass the flag option with the
resolved run ID to the underlying run process.

    >>> run(f"guild run op-source-with-flag-2 upstream={first_upstream_run} -y")
    Resolving upstream
    Using run ... for upstream
    --upstream ...

    >>> assert_resolved_run(first_upstream_run, "upstream")

The name is used when recording the dependency.

    >>> run("guild select --attr deps")
    upstream:
      upstream:
        config: ...
        paths: []
        uri: operation:upstream

The operation defines the alias `an-upstream-run` for the resource
flag.

    >>> run(f"guild run op-source-with-flag-2 an-upstream-run={first_upstream_run} -y")
    Resolving upstream
    Using run ... for upstream
    --upstream ...

    >>> assert_resolved_run(first_upstream_run, "upstream")

The name is still used when recording the dependency.

    >>> run("guild select --attr deps")
    upstream:
      upstream:
        config: ...
        paths: []
        uri: operation:upstream

## Invalid config

The project under the `warnings` subdirectory contains invalid
configuration that generates warnings when loaded.

    >>> use_project(path("resource-flags", "warnings"))

    >>> run("guild help")  # doctest: +REPORT_UDIFF
    WARNING: flag 'infile' for operation file-source-with-invalid-type is
    configured with type 'number' - this value cannot be used because it
    conflicts with the dependency 'infile' - ignoring configured value
    WARNING: flag 'op-dep' for operation op-source-with-invalid-type is
    configured with type 'number' - this value cannot be used because it
    conflicts with the dependency 'op-dep' - ignoring configured value
    ...
    <exit 0>

Despite specifying types that would cause run errors, the operations
succeed because the configured values are ignored.

    >>> run("guild run file-source-with-invalid-type -y")
    WARNING: flag 'infile' for operation file-source-with-invalid-type...
    WARNING: flag 'op-dep' for operation op-source-with-invalid-type...
    Resolving infile
    Using ../foo.txt for infile

    >>> run("guild run op-source-with-invalid-type -y")
    WARNING: flag 'infile' for operation file-source-with-invalid-type...
    WARNING: flag 'op-dep' for operation op-source-with-invalid-type...
    Resolving op-dep
    Using run ... for op-dep
