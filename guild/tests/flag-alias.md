# Flag alias

These tests illustrate Guild's support of flag aliases.

A flag alias is an alternative name that can be specified in a `run`
command.

We use the `alias` project for these tests.

    >>> use_project("alias")

The `test` operation defines a single flag `x`.

    >>> run("guild help")
    OVERVIEW...
    BASE OPERATIONS
    <BLANKLINE>
        test
          Flags:
            x

We can run the operation as expected using the flag name `x`.

    >>> run("guild run test x=1 -y")
    --x 1

We can alternatively use the alias `xx`.

    >>> run("guild run test xx=2 -y")
    --x 2

The alias is only used when specifying flags for the command. It is
not saved with the run.

    >>> run("guild runs -s")
    [1]  test  completed  x=2
    [2]  test  completed  x=1

    >>> run("guild select --attr flags")
    x: 2

If we specify both the alias and the flag name, Guild generates an
error.

    >>> run("guild run test x=3 xx=4 -y")
    guild: cannot specify both alias 'x' and name for flag 'xx'
    Use --force-flags to skip this check.
    <exit 1>

We can use `--force-flags` to override this check. Note however, the
flag is not passed as an argument to the underlying script.

    >>> run("guild run test x=3 xx=4 --force-flags -y")
    --x 3

In this case, Guild saves uses both flags.

    >>> run("guild runs -s")
    [1]  test  completed  x=3 xx=4
    [2]  test  completed  x=2
    [3]  test  completed  x=1

    >>> run("guild select --attr flags")
    x: 3
    xx: 4
