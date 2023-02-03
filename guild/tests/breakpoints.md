---
doctest: +FIXME_CI  # Issue appears specific to CI env (can't reproduce over ssh - may be tty related)
---

# Breakpoints

Guild supports break points for Python based operations. We use sample
scripts to illustrate.

    >>> set_guild_home(mkdtemp())
    >>> cd(sample("scripts"))

For tests below that wait for a prompt, we use a configurable timeout.

    >>> prompt_timeout = float(os.getenv("BREAKPOINT_PROMPT_TIMEOUT") or 2)

## Break on Line Number

To break on the first breakable line of the main module, use `1` with
`break`.

Breakpoints are set on the first breakable line equal to or greater
than the specified line. In the case of `breakable_lines.py`, the
first breakable line it 5.

    >>> from guild import python_util
    >>> python_util.first_breakable_line("breakable_lines.py")
    5

    >>> run("guild run breakable_lines.py --break 1 -y", timeout=prompt_timeout)
    Breakpoint 1 at .../breakable_lines.py:5
    > .../breakable_lines.py(5)<module>()
    -> def foo():
    (Pdb)
    <exit ...>

Break accepts file names with line numbers.

    >>> run("guild run breakable_lines.py --break breakable_lines:41 -y",
    ...     timeout=prompt_timeout)
    Breakpoint 1 at .../breakable_lines.py:41
    hello
    hello from loop
    hello from loop
    hello from while
    hello
    > .../breakable_lines.py(41)bar()
    -> print("hello bar from for")
    (Pdb)
    <exit ...>

It also accepts function names. Function names must be preceded by
their containing module.

    >>> run("guild run breakable_lines.py --break breakable_lines.bar -y",
    ...     timeout=prompt_timeout)
    Breakpoint 1 at .../breakable_lines.py:39
    hello
    hello from loop
    hello from loop
    hello from while
    hello
    > .../breakable_lines.py(40)bar()
    -> for i in range(2):
    (Pdb)
    <exit ...>

## Break on Error

Use `--break-on-error` to start a post mortem session on script error.

    >>> run("guild run error.py --break-on-error -y", timeout=prompt_timeout)
    Traceback (most recent call last):
      File ".../error.py", line 1, in <module>
        1 / 0
        ...
    ZeroDivisionError: ...
    Entering post mortem debug session
    > .../error.py(1)<module>()
    -> 1 / 0
    (Pdb)
    <exit ...>
