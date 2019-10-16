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

## Stage

Stage Python op:

    >>> cwd = mkdtemp()
    >>> python_script = path(cwd, "run.py")
    >>> touch(python_script)

    >>> gh = run_gh(cwd, opspec="run.py", stage=True)
    run.py staged as ...
    To start the operation, use 'guild run --start ...'

    >>> find(gh)
    ???
    runs/.../.guild/ENV
    runs/.../.guild/STAGED
    runs/.../.guild/attrs/...
    runs/.../.guild/opref
    runs/.../.guild/sourcecode/run.py

Staged Python op in explicit run dir:

    >>> run_dir = mkdtemp()
    >>> run(cwd, opspec="run.py", stage=True, run_dir=run_dir)
    run.py staged in '...'
    To start the operation, use "(cd '...' && source .guild/ENV
    && ... -um guild.op_main run)"

    >>> find(run_dir)
    .guild/ENV
    .guild/STAGED
    .guild/attrs/...
    .guild/opref
    .guild/sourcecode/run.py

Staged exec op:

    >>> cwd = init_gf("""
    ... op:
    ...   exec: run.sh
    ... """)

    >>> run(cwd, opspec="op", stage=True)
    op staged as ...
    To start the operation, use 'guild run --start ...'

Stage exec op in explicit run dir:

    >>> run(cwd, opspec="op", stage=True, run_dir=mkdtemp())
    op staged in '...'
    To start the operation, use "(cd '...' && source .guild/ENV && run.sh)"

## Restart

Restart an operation:

    >>> cwd = init_gf("""
    ... op:
    ...   exec: python -c 'import sys; sys.exit(${code})'
    ...   flags:
    ...     code: 0
    ... """)

    >>> gh = run_gh(cwd, flags=["code=11"])
    <exit 11>

    >>> run_id = dir(path(gh, "runs"))[0]
    >>> R = runlib.for_dir(path(gh, "runs", run_id))
    >>> R.get("env")["FLAG_CODE"]
    '11'

    >>> run(cwd, gh, restart=run_id, flags=["code=22"])
    <exit 22>

    >>> R.get("env")["FLAG_CODE"]
    '22'

Start a staged operation:

    >>> gh = run_gh(cwd, flags=["code=33"], stage=True)
    op staged as ...
    To start the operation, use 'guild run --start ...'

    >>> runs = dir(path(gh, "runs"))
    >>> len(runs)
    1

    >>> run_id = dir(path(gh, "runs"))[0]

    >>> run(cwd, gh, start=run_id)
    <exit 33>

    >>> run(cwd, gh, restart=run_id)
    <exit 33>

    >>> run(cwd, gh, restart=run_id, flags=["code=44"])
    <exit 44>

    >>> run(cwd, gh, restart=run_id)
    <exit 44>

    >>> runs = dir(path(gh, "runs"))
    >>> len(runs)
    1

Missing required op config:

    >>> run_dir = path(gh, "runs", run_id)
    >>> os.remove(path(run_dir, ".guild", "attrs", "op"))

    >>> run(cwd, gh, restart=run_id)
    cannot restart run in ...: missing op configuration
    The run may not have been initialized correctly. Try starting the
    operation without the --start/--restart flag.
    <exit 1>

Corrupt op config:

    >>> write(path(run_dir, ".guild", "attrs", "op"), "{foo:123}")
    >>> run(cwd, gh, restart=run_id)
    cannot restart run in ...: invalid op configuration
    This may be an internal error. Please open an issue
    https://github.com/guildai/guildai/issues.
    <exit 1>

## Restart without opdef

A run can be restarted without when its opdef is missing. However,
user cannot specify flags.

Simple project with opdef:

    >>> cwd = init_gf("""
    ... op:
    ...   main: op ${foo} ${bar}
    ...   flags:
    ...     foo: 123
    ...     bar: 456
    ... """)

Script to write some files based on flag vals:

    >>> write(path(cwd, "op.py"), """
    ... import sys, time
    ... foo, bar = sys.argv[1:3]
    ... open(foo, "w").close()
    ... open(bar, "w").close()
    ... open(str(time.time()), "w").close()
    ... """)

Run with flags:

    >>> gh = run_gh(cwd, flags=["foo=321"])

    >>> run_id = dir(path(gh, "runs"))[0]
    >>> run_dir = path(gh, "runs", run_id)

    >>> cat(path(run_dir, ".guild", "opref"))
    guildfile:.../guild.yml ... '' op

    >>> cat(path(run_dir, ".guild", "attrs", "cmd"))
    - ...
    - -um
    - guild.op_main
    - op
    - '321'
    - '456'
    - --
    - --bar
    - '456'
    - --foo
    - '321'

    >>> cat(path(run_dir, ".guild", "attrs", "flags"))
    bar: 456
    foo: 321

    >>> dir(run_dir)
    ['.guild', '...', '321', '456']

Delete the project:

    >>> os.remove(path(cwd, "guild.yml"))

We can restart without flags:

    >>> run(cwd, gh, restart=run_id)

    >>> cat(path(run_dir, ".guild", "attrs", "flags"))
    bar: 456
    foo: 321

    >>> dir(run_dir)
    ['.guild', '...', '...', '321', '456']

However, if we specify any flags, Guild complains.

    >>> run(cwd, gh, restart=run_id, flags=["foo=111"])
    cannot set flags when restarting ...: configuration for
    operation 'op' is not available
    <exit 1>

It doesn't matter if the flags apply to the original operation or not.

    >>> run(cwd, gh, restart=run_id, flags=["other_flag=111"])
    cannot set flags when restarting ...: configuration for
    operation 'op' is not available
    <exit 1>

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

    >> "TODO"
