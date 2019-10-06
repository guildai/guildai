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

Start a staged operation:

    >>> cwd = init_gf("""
    ... op:
    ...   exec: python -c 'import sys; sys.exit(${code})'
    ...   flags:
    ...     code: 0
    ... """)

    >>> guild_home = run_gh(cwd, flags=["code=111"])
    <exit 111>

    >>> run_id = dir(path(guild_home, "runs"))[0]

    >>> R = runlib.from_dir(path(guild_home, "runs", run_id))
    >>> R.get("env")["FLAG_CODE"]
    '111'

    >>> run(cwd, guild_home, restart=run_id, flags=["code=222"])
    <exit 222>

    >>> R.get("env")["FLAG_CODE"]
    '222'
