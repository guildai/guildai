# Breakpoints

Guild supports break points for Python based operations. We use sample
scripts to illustrate.

    >>> gh = mkdtemp()
    >>> cd(sample("scripts"))

## Break on Line Number

To break on the first breakable line of the main module, use `1` with
`break`.

Breakpoints are set on the first breakable line equal to or greater
than the specified line. In the case of `breakable_lines.py`, the
first breakable line it 5.

    >>> from guild import python_util
    >>> python_util.first_breakable_line("breakable_lines.py")
    5

NOTE: Breakpoints for Python 2 are not cleanly supported. When one or
more breakpoints are set, execution first stops within
`guild.op_main`. The user is responsible for manually continuing to
the first set breakpoint. This issue does not exist with Python 3.

Here's the behavior on Python 2:

    >>> run("guild run breakable_lines.py --break 1 -y",
    ...     timeout=2, guild_home=gh)  # doctest: -PY3
    Breakpoint 1 at .../.guild/sourcecode/breakable_lines.py:5
    > .../guild/op_main.py(...)exec_script()
    -> mod_name = _module_name_for_info(module_info)
    (Pdb)
    <exit ...>

Note that the correct breakpoints are set. However, the code breaks
initially within `guild.op_main`.

The correct behavior is supported in Python 3:

    >>> run("guild run breakable_lines.py --break 1 -y",
    ...     timeout=2, guild_home=gh)  # doctest: -PY2
    Breakpoint 1 at .../.guild/sourcecode/breakable_lines.py:5
    > .../.guild/sourcecode/breakable_lines.py(5)<module>()
    -> def foo():
    (Pdb)
    <exit ...>

Break accepts file names with line numbers.

    >>> run("guild run breakable_lines.py --break breakable_lines:41 -y",
    ...     timeout=2, guild_home=gh)  # doctest: -PY2
    Breakpoint 1 at .../.guild/sourcecode/breakable_lines.py:41
    hello
    hello from loop
    hello from loop
    hello from while
    hello
    > .../.guild/sourcecode/breakable_lines.py(41)bar()
    -> print("hello bar from for")
    (Pdb)
    <exit ...>

It also accepts function names. Function names must be preceded by
their containing module.

    >>> run("guild run breakable_lines.py --break breakable_lines.bar -y",
    ...     timeout=2, guild_home=gh)  # doctest: -PY2
    Breakpoint 1 at .../.guild/sourcecode/breakable_lines.py:39
    hello
    hello from loop
    hello from loop
    hello from while
    hello
    > .../.guild/sourcecode/breakable_lines.py(40)bar()
    -> for i in range(2):
    (Pdb)
    <exit ...>

## Break on Error

Use `--break-on-error` to start a post mortem session on script error.

    >>> run("guild run error.py --break-on-error -y", timeout=2, guild_home=gh)
    Traceback (most recent call last):
      File ".../.guild/sourcecode/error.py", line 1, in <module>
        1 / 0
    ZeroDivisionError: ...
    Entering post mortem debug session
    > .../.guild/sourcecode/error.py(1)<module>()
    -> 1 / 0
    (Pdb)
    <exit ...>
