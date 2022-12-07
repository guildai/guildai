# Resource flags

Guild provides a flag-like interface to specify alternative resources
or resource locations. For example, a user may specify a specific run
for an 'operation' dependency using the resource name or a flag name
configured for the dependency.

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

The `resource-default` operation does not define any flags but
requires a file `foo.txt`.

    >>> run("guild run resource-default --help-op")
    Usage: guild run [OPTIONS] resource-default [FLAG]...
    <BLANKLINE>
    Use 'guild run --help' for a list of options.

The operation requires `foo.txt`.

    >>> run("guild run resource-default -y")
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

Because the resource does not define a `flag-name`, we can't specify
an alternative file. Let's try using the resource source identifier
`file:foo.txt`

    >>> run("guild run resource-default file:foo.txt=bar.txt -y")
    guild: unsupported flag 'file:foo.txt'
    Try 'guild run resource-default --help-op' for a list of flags or
    use --force-flags to skip this check.
    <exit 1>

We can, however, force Guild to accept the alternative path using
`--force-flags`.

    >>> run("guild run resource-default file:foo.txt=bar.txt --force-flags -y")
    Resolving file:foo.txt
    Using bar.txt for file:foo.txt
    --file:foo.txt bar.txt

    >>> run("guild ls -n")
    bar.txt
    guild.yml

## Named resources

The `resource-name` operation provides a `name` attribute for the
resource source.

Guild's operation help text does not say anything about this resource,
however.

    >>> run("guild run resource-name --help-op")
    Usage: guild run [OPTIONS] resource-name [FLAG]...
    <BLANKLINE>
    Defines a resource with a name.
    <BLANKLINE>
    Use 'guild run --help' for a list of options.

The operation uses the provided name when logging its resolution. The
default file is `foo.txt`.

    >>> run("guild run resource-name -y")
    Resolving infile

    >>> run("guild ls -n")
    foo.txt
    guild.yml

We still cannot specify an alternative file using flag assignment syntax.

    >>> run("guild run resource-name foo=bar.txt -y")
    guild: unsupported flag 'foo'
    Try 'guild run resource-name --help-op' for a list of flags or use
    --force-flags to skip this check.
    <exit 1>

As with the previous example, we can use `--force-flags` to bypass the
check.

    >>> run("guild run resource-name infile=bar.txt --force-flags -y")
    Resolving infile
    Using bar.txt for infile
    --infile bar.txt

    >>> run("guild ls -n")
    bar.txt
    guild.yml

## Flag-named resources

`resource-flag-name` provides a `flag-name` attribute for a resource.

    >>> run("guild run resource-flag-name --help-op")
    Usage: guild run [OPTIONS] resource-flag-name [FLAG]...
    <BLANKLINE>
    Defines a resource with a flag name.
    <BLANKLINE>
    Use 'guild run --help' for a list of options.

Despite providing flag-related information for a resource, Guild still
doesn't provide information for setting this value in the operation
help. It should.

Guild uses the flag name when logging the resource resolution.

    >>> run("guild run resource-flag-name -y")
    Resolving infile

    >>> run("guild ls -n")
    foo.txt
    guild.yml

Provided the user knows about the flag name, she can set it directly
for a run.

    >>> run("guild run resource-flag-name infile=bar.txt -y")
    Resolving infile
    Using bar.txt for infile
    --infile bar.txt

    >>> run("guild ls -n")
    bar.txt
    guild.yml

`resource-name-and-flag-name` defines both a name and a flag name for
a resource source. When resolving the resource, Guild uses `name` when
both `name` and `flag-name` are defined.

    >>> run("guild run resource-name-and-flag-name -y")
    Resolving input file

    >>> run("guild ls -n")
    foo.txt
    guild.yml

When specifying an alternative resource, we use flag name.

    >>> run("guild run resource-name-and-flag-name input-file=bar.txt -y")
    Resolving input file
    Using bar.txt for input file
    --input-file bar.txt

    >>> run("guild ls -n")
    bar.txt
    guild.yml

## Explicit flags and resources

The `flag-and-resource` operation provides additional flag information
about a resource. It uses `foo` for a resource flag name.

With the explicit flag definition, Guild shows help for the flag.

    >>> run("guild run flag-and-resource --help-op")
    Usage: guild run [OPTIONS] flag-and-resource [FLAG]...
    <BLANKLINE>
    Use 'guild run --help' for a list of options.
    <BLANKLINE>
    Flags:
      infile  Path to infile (default is foo.txt)

The operation uses 'foo.txt' to resolve the infile resource.

    >>> run("guild run flag-and-resource -y")
    Resolving infile
    Using foo.txt for infile
    --infile foo.txt

    >>> run("guild ls -n")
    foo.txt
    guild.yml

The flag value is used to resolve the `inline` dependency.

    >>> run("guild run flag-and-resource infile=bar.txt -y")
    Resolving infile
    Using bar.txt for infile
    --infile bar.txt

    >>> run("guild ls -n")
    bar.txt
    guild.yml

## Required operation

The `resource-op` operation requires the `flag` operation.

As with other resources, this information is not provided in operation
help.

    >>> run("guild run resource-op --help-op")
    Usage: guild run [OPTIONS] resource-op [FLAG]...
    <BLANKLINE>
    Use 'guild run --help' for a list of options.

We have a `flag` run available for resolution.

    >>> run("guild runs -Fo flag -s")
    [1]  flag  completed  foo=123

When we run `resource-op`, Guild uses this run to resolve the
dependency.

    >>> run("guild run resource-op -y")
    Resolving operation:flag
    Using run ... for operation:flag

Helper to verify that the expected run is resolved.

    >>> def assert_resolved_run(expected_run_select, resource_name="operation:flag"):
    ...     expected_run_id = run_capture(f"guild select {expected_run_select}")
    ...     deps = yaml.safe_load(run_capture("guild select --attr deps"))
    ...     try:
    ...         actual_run_id = deps[resource_name][resource_name]["config"]
    ...     except KeyError:
    ...         raise AssertionError((deps, gh)) from None
    ...     assert actual_run_id == expected_run_id, (expected_run_id, deps, gh)

    >>> assert_resolved_run("-Fo flag")

We can specify an alternative run for the operation dependency using
the `flag` flag, provided we include `--force-flags`.

Without `--force-flags`:

    >>> run("guild run resource-op flag=xxx -y")
    guild: unsupported flag 'flag'
    Try 'guild run resource-op --help-op' for a list of flags or use
    --force-flags to skip this check.
    <exit 1>

With `--force-flags`:

    >>> run("guild run resource-op flag=xxx --force-flags -y")
    WARNING: cannot find a suitable run for required resource 'operation:flag'
    Resolving operation:flag
    guild: run failed because a dependency was not met: could not resolve
    'operation:flag' in operation:flag resource: no suitable run for flag
    <exit 1>

We currently only have one `flag` run to resolve.

    >>> run("guild runs -Fo flag -s")
    [1]  flag  completed  foo=123

Let's create another `flag` run.

    >>> run("guild run flag foo=456 -y")
    --foo 456

We can specify the original `flag` run using the operation name and
`--force-flags`.

    >>> first_flag_run_id = run_capture("guild select -Fo flag 2")
    >>> run(f"guild run resource-op flag={first_flag_run_id} --force-flags -y")
    Resolving operation:flag
    Using run ... for operation:flag
    --flag ...

    >>> assert_resolved_run("-Fo flag 2")

We can also use a more qualified name for the operation dependency. In
the above example we used `flag`. Here we use `operation:flag`:

    >>> run(f"guild run resource-op operation:flag={first_flag_run_id} --force-flags -y")
    Resolving operation:flag
    Using run ... for operation:flag

    >>> assert_resolved_run("-Fo flag 2")

## Exposing required operation with flags

In the previous section we have to use `--force-flags` to bypass
Guild's check for flags to configure alternative run IDs for the
required operation.

We can define a flag for the operation to officially support a flag
interface for the operation. Operation `resource-op-with-flag` defines
a flag named `flag`, which is the same as the resource name.

    >>> run("guild run resource-op-with-flag --help-op")
    Usage: guild run [OPTIONS] resource-op-with-flag [FLAG]...
    <BLANKLINE>
    Use 'guild run --help' for a list of options.
    <BLANKLINE>
    Flags:
      flag  Run ID for 'flag' run (defaults to latest non-error run)

We can run this operation with a `flag` value without needing
`--force-flags`.

    >>> run(f"guild run resource-op-with-flag flag={first_flag_run_id} -y")
    Resolving operation:flag
    Using run ... for operation:flag
    --flag ...

    >>> assert_resolved_run("-Fo flag 2")

If we use the operation name `operation:flag`, we need to use
`--force-flags` to bypass Guild's flag checks.

    >>> run("guild run resource-op-with-flag operation:flag=xxx -y")
    guild: unsupported flag 'operation:flag'
    Try 'guild run resource-op-with-flag --help-op' for a list of flags
    or use --force-flags to skip this check.
    <exit 1>

    >>> run("guild run resource-op-with-flag operation:flag=xxx --force-flags -y")
    WARNING: cannot find a suitable run for required resource 'operation:flag'
    Resolving operation:flag
    guild: run failed because a dependency was not met: could not resolve
    'operation:flag' in operation:flag resource: no suitable run for flag
    <exit 1>

## Named resource

`resource-op-with-name` defines a name for the required operation.

This does not surface to the user in help.

    >>> run("guild run resource-op-with-name --help-op")
    Usage: guild run [OPTIONS] resource-op-with-name [FLAG]...
    <BLANKLINE>
    Use 'guild run --help' for a list of options.

As with the default operation name, we can't use the name as a flag.

    >>> run("guild run resource-op-with-name flag-run=xxx -y")
    guild: unsupported flag 'flag-run'
    Try 'guild run resource-op-with-name --help-op' for a list of flags or
    use --force-flags to skip this check.
    <exit 1>

With `--force-flags` Guild will use the resource name to read the
user-specified run ID.

    >>> run(f"guild run resource-op-with-name flag-run={first_flag_run_id} --force-flags -y")
    Resolving flag-run
    Using run ... for flag-run

    >>> assert_resolved_run("-Fo flag 2", resource_name="flag-run")

## Names resource with flags

The `resource-op-with-name-and-flag` operation defines both a name and
a flag for the required operation.

As with the previous flag examples, the flag is shown in help.

    >>> run("guild run resource-op-with-name-and-flag --help-op")
    Usage: guild run [OPTIONS] resource-op-with-name-and-flag [FLAG]...
    <BLANKLINE>
    Use 'guild run --help' for a list of options.
    <BLANKLINE>
    Flags:
      flag-run  Run ID for 'flag' run (defaults to latest non-error run)

    >>> run("guild run resource-op-with-name-and-flag -y")
    Resolving flag-run
    Using run ... for flag-run
    --FLAG_RUN ...

    >>> assert_resolved_run("-Fo flag", resource_name="flag-run")

Note that Guild uses the `arg-name` defined for the flag in the args
passed to the script.

We don't need to use `--force-flags` in for this operation.

    >>> run(f"guild run resource-op-with-name-and-flag flag-run=xxx -y")
    WARNING: cannot find a suitable run for required resource 'flag-run'
    Resolving flag-run
    guild: run failed because a dependency was not met: could not resolve
    'operation:flag' in flag-run resource: no suitable run for flag
    <exit 1>
