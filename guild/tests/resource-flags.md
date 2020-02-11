# Resource flags

    >>> project = Project(sample("projects", "resource-flags"))

Guild file reference:

    >>> cat(path(project.cwd, "guild.yml"))  # doctest: +REPORT_UDIFF
    - operations:
        flag:
          main: guild.pass hello flag
          flags-dest: args
          flags:
            foo: 123
    <BLANKLINE>
        resource:
          main: guild.pass hello resource
          flags-dest: args
          requires:
            - file: foo.txt
              flag-name: foo
    <BLANKLINE>
        flag-and-resource:
          main: guild.pass hello flag-and-resource
          flags-dest: args
          flags:
            foo: 123
          requires:
            - file: foo.txt
              flag-name: foo
    <BLANKLINE>
        requires-flag:
          main: guild.pass hello requires-flag
          flags-dest: args
          requires:
            - operation: flag
    <BLANKLINE>
        requires-flag-2:
          main: guild.pass hello requires-flag-2
          flags-dest: args
          flags:
            flag: null
          requires:
            - operation: flag
    <BLANKLINE>
        requires-flag-3:
          main: guild.pass hello requires-flag-3
          flags-dest: args
          requires:
            - operation: flag
              name: foo
    <BLANKLINE>
        requires-flag-4:
          main: guild.pass hello requires-flag-4
          flags-dest: args
          flags:
            foo:
              default: invalid
              arg-name: FOO
          requires:
            - operation: flag
              name: foo

Operation defined with only `foo` flag:

    >>> project.run("flag")
    hello flag --foo 123

Operation defined with only `foo` resource:

    >>> project.run("resource")
    Resolving foo dependency
    hello resource

Run files:

    >>> project.ls()
    ['foo.txt']

We can use the resource flag name to specify a different resoure
source.

    >>> project.run("resource", flags={"foo": "bar.txt"})
    Resolving foo dependency
    Using bar.txt for foo resource
    hello resource --foo bar.txt

    >>> project.ls()
    ['bar.txt']

Operation defined with both flag and resource named `foo`:

    >>> project.run("flag-and-resource")
    Resolving foo dependency
    guild: run failed because a dependency was not met: could not
    resolve 'file:foo.txt' in foo resource: .../resource-flags/123
    does not exist
    <exit 1>

Note that the flag default `123` took precedence over the resource
default. We can set the flag howerver.

    >>> project.run("flag-and-resource", flags={"foo": "foo.txt"})
    Resolving foo dependency
    Using foo.txt for foo resource
    hello flag-and-resource --foo foo.txt

    >>> project.ls()
    ['foo.txt']

Operation that requires a `flag` run:

    >>> project.run("requires-flag")
    Resolving flag dependency
    Using output from run ... for flag resource
    hello requires-flag

Note that the `flag` argument was not included.

We can use the `flag` flag name to specify a different run. In this
case we'll specify an invalid run ID.

    >>> project.run("requires-flag", flags={"flag": "invalid"})
    WARNING: cannot find a suitable run for required resource 'flag'
    Resolving flag dependency
    guild: run failed because a dependency was not met: could not resolve
    'operation:flag' in flag resource: no suitable run for flag
    <exit 1>

The operation `requires-flag-2` defines a flag named `flag`, which is
the same as the resource name. In this case, the flag assumes the role
of the interface to the resource run ID.

    >>> project.run("requires-flag-2")
    Resolving flag dependency
    Using output from run ... for flag resource
    hello requires-flag-2 --flag ...

Note in this case the flag is included in the args because it's
defined as a flag.

`requires-flag-3` is like `requires-flag` but redefined the flag name
used for the resource.

    >>> project.run("requires-flag-3")
    Resolving foo dependency
    Using output from run ... for foo resource
    hello requires-flag-3

    >>> project.run("requires-flag-3", flags={"foo": "invalid"})
    WARNING: cannot find a suitable run for required resource 'foo'
    Resolving foo dependency
    guild: run failed because a dependency was not met: could not resolve
    'operation:flag' in foo resource: no suitable run for flag
    <exit 1>

Finally, `requires-flag-4` is like `requires-flag-3` but defines a
flag with the same name as the resource name. It also includes an
invalid default value for the required resource and a rename argument.

    >>> project.run("requires-flag-4")
    WARNING: cannot find a suitable run for required resource 'foo'
    Resolving foo dependency
    guild: run failed because a dependency was not met: could not resolve
    'operation:flag' in foo resource: no suitable run for flag
    <exit 1>

We can force a lookup by setting `foo` to an empty string.

    >>> project.run("requires-flag-4", {"foo": ""})
    Resolving foo dependency
    Using output from run ... for foo resource
    hello requires-flag-4 --FOO ...

Note that the argument `--FOO` is provided as specified by the `foo`
flag def for the operation.
