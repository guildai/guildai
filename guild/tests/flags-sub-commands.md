# Sub-command Flag Support

We use the `sub-commands` sample project for our tests below.

    >>> cd(sample("projects", "sub-commands"))

Isolate any runs for our tests.

    >>> set_guild_home(mkdtemp())

Help for the project.

    >>> run("guild help")
    ???
    BASE OPERATIONS
    <BLANKLINE>
        argparse-a
          Flags:
            a-foo  (default is 2)
    <BLANKLINE>
        argparse-b
          Flags:
            b-foo  (default is 3)
    <BLANKLINE>
        click-a
          Flags:
            a-foo  (default is 5)
    <BLANKLINE>
        click-b
          Flags:
            b-foo  (default is 6)
    <BLANKLINE>
        click-b-sub
          Flags:
            b-sub-foo  (default is 7)
    <exit 0>

Run the operations with default flag vals.

    >>> run("guild run argparse-a -y")
    base_foo=1
    a_foo=2
    <exit 0>

    >>> run("guild run argparse-b -y")
    base_foo=1
    b_foo=3
    <exit 0>

    >>> run("guild run click-a -y")
    base-foo=4
    a-foo=5
    <exit 0>

The following error is expected. The operation is configured to use
the `b` command, which is a Click group.

    >>> run("guild run click-b -y")  # doctest: -PY36
    base-foo=4
    Usage: args_click.py b [OPTIONS] COMMAND [ARGS]...
    Try 'args_click.py b --help' for help.
    <BLANKLINE>
    Error: Missing command.
    <exit 2>

    >>> run("guild run click-b-sub -y")
    base-foo=4
    b-foo=6
    b-sub-f=7
    <exit 0>

Run with modified flag vals.

    >>> run("guild run argparse-a a-foo=22 -y")
    base_foo=1
    a_foo=22
    <exit 0>

    >>> run("guild run argparse-b b-foo=33 -y")
    base_foo=1
    b_foo=33
    <exit 0>

    >>> run("guild run click-a a-foo=55 -y")
    base-foo=4
    a-foo=55
    <exit 0>

    >>> run("guild run click-b-sub b-sub-foo=77 -y")
    base-foo=4
    b-foo=6
    b-sub-f=77
    <exit 0>

View the runs.

    >>> run("guild runs") # doctest: -PY36
    [1:...]  click-b-sub  ...  completed  b-sub-foo=77
    [2:...]  click-a      ...  completed  a-foo=55
    [3:...]  argparse-b   ...  completed  b-foo=33
    [4:...]  argparse-a   ...  completed  a-foo=22
    [5:...]  click-b-sub  ...  completed  b-sub-foo=7
    [6:...]  click-b      ...  error      b-foo=6
    [7:...]  click-a      ...  completed  a-foo=5
    [8:...]  argparse-b   ...  completed  b-foo=3
    [9:...]  argparse-a   ...  completed  a-foo=2
    <exit 0>
