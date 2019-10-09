# Run impl tests 2

Helpers (copied from `run-impl.md`):

    >>> def run_gh(cwd=None, guild_home=None, yes=True, **kw):
    ...     from guild import click_util
    ...     from guild.commands import run, run_impl2
    ...     ctx = run.run.make_context("", [])
    ...     ctx.params.update(kw)
    ...     ctx.params["yes"] = yes
    ...     args = click_util.Args(**ctx.params)
    ...     cwd = cwd or mkdtemp()
    ...     guild_home = guild_home or mkdtemp()
    ...     with SetCwd(cwd):
    ...         with SetGuildHome(guild_home):
    ...             with Env({"NO_RUN_OUTPUT_CAPTURE": "1",
    ...                       "NO_WARN_RUNDIR": "1"}):
    ...                 with LogCapture(stdout=True, strip_ansi_format=True):
    ...                     try:
    ...                         run_impl2.main(args)
    ...                     except SystemExit as e:
    ...                         if e.args[0] is not None:
    ...                             print(e.args[0])
    ...                         print("<exit %i>" % e.args[1]
    ...                               if len(e.args) > 1 else 1)
    ...     return guild_home

    >>> def run(*args, **kw):
    ...     run_gh(*args, **kw)

    >>> def init_gf(s):
    ...     cwd = mkdtemp()
    ...     write(path(cwd, "guild.yml"), s)
    ...     return cwd

    >>> from guild import run as runlib

## Restart

Restart an operation:

    >>> cwd = init_gf("""
    ... op:
    ...   exec: python -c 'import sys; sys.exit(${code})'
    ...   flags:
    ...     code: 0
    ... """)

    >>> guild_home = run_gh(cwd, flags=["code=11"])
    <exit 11>

    >>> run_id = dir(path(guild_home, "runs"))[0]
    >>> R = runlib.for_dir(path(guild_home, "runs", run_id))
    >>> R.get("env")["FLAG_CODE"]
    '11'

    >>> run(cwd, guild_home, restart=run_id, flags=["code=22"])
    <exit 22>

    >>> R.get("env")["FLAG_CODE"]
    '22'

Start a staged operation:

    >>> guild_home = run_gh(cwd, flags=["code=33"], stage=True)
    op staged as ...
    To start the operation, use 'guild run --start ...'

    >>> runs = dir(path(guild_home, "runs"))
    >>> len(runs)
    1

    >>> run_id = dir(path(guild_home, "runs"))[0]

    >>> run(cwd, guild_home, start=run_id)
    <exit 33>

    >>> run(cwd, guild_home, restart=run_id)
    <exit 33>

    >>> run(cwd, guild_home, restart=run_id, flags=["code=44"])
    <exit 44>

    >>> run(cwd, guild_home, restart=run_id)
    <exit 44>

    >>> runs = dir(path(guild_home, "runs"))
    >>> len(runs)
    1

## Batch operation errors

Optimizer flag with no optimizer:

    >>> cwd = init_gf("""
    ... op: { main: guild.pass }
    ... """)

    >>> run(cwd, opt_flags=["foo=123"])
    invalid optimizer flag foo=123: no optimizer specified
    <exit 1>

Invalid optimizer flag:

    >>> run(cwd, optimizer="+", opt_flags=["baz=789"])
    unsupported flag 'baz'
    Try 'guild run + --help-op' for a list of flags or use
    --force-flags to skip this check.
    <exit 1>

## Stage batch op
