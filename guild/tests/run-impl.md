# Run impl tests

Helpers:

    >>> def run_gh(cwd=None, guild_home=None, **kw):
    ...     from guild.commands import run_impl
    ...     cwd = cwd or mkdtemp()
    ...     guild_home = guild_home or mkdtemp()
    ...     with SetCwd(cwd):
    ...         with SetGuildHome(guild_home):
    ...             with Env({"NO_RUN_OUTPUT": "1",
    ...                       "NO_WARN_RUNDIR": "1"}):
    ...                 with LogCapture(echo_to_stdout=True):
    ...                     try:
    ...                         run_impl.run(**kw)
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
    >>> from guild import run_util
    >>> from guild import var

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

    >>> run(cwd, gh, restart=run_id)
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
    guildfile:.../guild.yml... ... '' op

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
    cannot find definition for operation 'op' in run ...
    The definition is required when setting flags for start or restart.
    <exit 1>

It doesn't matter if the flags apply to the original operation or not.

    >>> run(cwd, gh, restart=run_id, flags=["other_flag=111"])
    cannot find definition for operation 'op' in run ...
    The definition is required when setting flags for start or restart.
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

## Dependencies

    >>> cwd = init_gf("""
    ... upstream:
    ...   main: guild.pass
    ...   requires:
    ...     - file: src.txt
    ... downstream:
    ...   main: guild.pass
    ...   requires:
    ...     - operation: upstream
    ... """)

Try to start downstream without required upstream op:

    >>> gh = run_gh(cwd, opspec="downstream")
    WARNING: cannot find a suitable run for required resource 'upstream'
    Resolving upstream dependency
    run failed because a dependency was not met: could not resolve
    'operation:upstream' in upstream resource: no suitable run for upstream
    <exit 1>

A run is create, but it has an error.

    >>> runs = dir(path(gh, "runs"))
    >>> len(runs)
    1

    >>> runlib.for_dir(path(gh, "runs", runs[0])).status
    'error'

Try to start upstream without required file:

    >>> run(cwd, opspec="upstream")
    Resolving file:src.txt dependency
    run failed because a dependency was not met: could not resolve
    'file:src.txt' in file:src.txt resource: cannot find source file 'src.txt'
    <exit 1>

Provide required file `src.txt`.

    >>> write(path(cwd, "src.txt"), "hello")

Run upstream again.

    >>> gh = run_gh(cwd, opspec="upstream")
    Resolving file:src.txt dependency

    >>> runs = var.runs(path(gh, "runs"))
    >>> len(runs)
    1
    >>> pprint(runs[0].get("deps"))
    {'file:src.txt': {'file:src.txt': {'paths': ['.../src.txt'],
                                       'uri': 'file:src.txt'}}}

    >>> cat(path(runs[0].dir, "src.txt"))
    hello

Run downstream again.

    >>> run(cwd, gh, opspec="downstream")
    Resolving upstream dependency
    Using run ... for upstream resource

    >>> runs = var.runs(path(gh, "runs"), sort=["-timestamp"])
    >>> len(runs)
    2

    >>> deps = runs[0].get("deps")
    >>> pprint(deps)
    {'upstream': {'operation:upstream': {'config': '...',
                                         'paths': ['../.../src.txt'],
                                         'uri': 'operation:upstream'}}}

The 'config' item associated with an operation dependency (source) is
the resolved run ID.

    >>> (deps["upstream"]["operation:upstream"]["config"] == runs[1].id,
    ...  (deps, runs[1].id))
    (True, ...)

    >>> cat(path(runs[0].dir, "src.txt"))
    hello

Run upstream again - this generates a new run that is used by
downstream by default.

    >>> run(cwd, gh, opspec="upstream")
    Resolving file:src.txt dependency

Mark the upstream runs to differentiate them from the previous
upstream run.

    >>> runs = var.runs(path(gh, "runs"), sort=["-timestamp"])

    >>> upstream_1 = runs[2]
    >>> upstream_1.opref.to_opspec()
    'upstream'

    >>> write(path(upstream_1.dir, "marker"), "upstream_1")

    >>> upstream_2 = runs[0]
    >>> upstream_2.opref.to_opspec()
    'upstream'

    >>> write(path(upstream_2.dir, "marker"), "upstream_2")

Run downstream with the default (second) upstream.

    >>> run(cwd, gh, opspec="downstream")
    Resolving upstream dependency
    Using run ... for upstream resource

Run downstream again but with the first upstream.

    >>> run(cwd, gh, opspec="downstream",
    ...     flags=["upstream=%s" % upstream_1.id])
    Resolving upstream dependency
    Using run ... for upstream resource

Verify that our two downstreams are using the expected upstreams by
looking for the markers.

    >>> runs = var.runs(path(gh, "runs"), sort=["-timestamp"])

The latest downstream is using upstream_1.

    >>> runs[0].opref.to_opspec()
    'downstream'

    >>> cat(path(runs[0].dir, "marker"))
    upstream_1

The previous upstream is using upstream_2.

    >>> runs[1].opref.to_opspec()
    'downstream'

    >>> cat(path(runs[1].dir, "marker"))
    upstream_2

## Staging dependencies

Guild stages dependencies differently depending on whether or not they
are operations. Operations are not resolved at stage time. All other
resource types are resolved at stage time.

    >>> cwd = init_gf("""
    ... upstream:
    ...   main: guild.pass
    ...   requires:
    ...     - file: src.txt
    ... downstream:
    ...   main: guild.pass
    ...   requires:
    ...     - operation: upstream
    ... """)

When we stage downstream, which requires on upstream, we succeed -
Guild doesn't attempt to resolve operation dependencies when staging.

    >>> gh = run_gh(cwd, opspec="downstream", stage=True)
    WARNING: cannot find a suitable run for required resource 'upstream'
    Resolving upstream dependency
    Skipping resolution of operation:upstream because it's being staged
    downstream staged as ...
    To start the operation, use 'guild run --start ...'

When we try to start the operation, however, we get an error because
there's not suitable upstream run.

    >>> runs = var.runs(path(gh, "runs"))
    >>> len(runs)
    1

    >>> run(cwd, gh, restart=runs[0].short_id)
    Resolving upstream dependency
    run failed because a dependency was not met: could not resolve
    'operation:upstream' in upstream resource: no suitable run for upstream
    <exit 1>

Let's try to stage upstream - the operation fails because other
resources are resolved during stage.

    >>> run(cwd, gh, opspec="upstream", stage=True)
    Resolving file:src.txt dependency
    run failed because a dependency was not met: could not resolve
    'file:src.txt' in file:src.txt resource: cannot find source file 'src.txt'
    <exit 1>

Let's create the required `src.txt` file:

    >>> write(path(cwd, "src.txt"), "yo")

And stage upstream again.

    >>> run(cwd, gh, opspec="upstream", stage=True)
    Resolving file:src.txt dependency
    upstream staged as ...
    To start the operation, use 'guild run --start ...'

Let's stage downstream again.

    >>> run(cwd, gh, opspec="downstream", stage=True)
    Resolving upstream dependency
    Skipping resolution of operation:upstream because it's being staged
    downstream staged as ...
    To start the operation, use 'guild run --start ...'

This staged run is configured to use the currently staged upstream.

    >>> runs = var.runs(path(gh, "runs"), sort=["-timestamp"])
    >>> staged_downstream = runs[0]
    >>> staged_upstream = runs[1]

    >>> (staged_downstream.get("flags")["upstream"] == staged_upstream.id,
    ...  (staged_downstream.get("flags"), staged_upstream.id))
    (True, ...)

If we run upstream, this will not effect the staged downstream.

    >>> run(cwd, gh, opspec="upstream")
    Resolving file:src.txt dependency

Let's run the staged downstream.

    >>> run(cwd, gh, restart=staged_downstream.id)
    Resolving upstream dependency
    Using run ... for upstream resource

The resolved dep for the downstream corresponds to the staged
upstream, not the latest upstream.

    >>> downstream_deps = staged_downstream.get("deps")
    >>> (staged_upstream.id ==
    ...  downstream_deps["upstream"]["operation:upstream"]["config"],
    ...  (downstream_deps, staged_upstream.id))
    (True, ...)

## Restarts and resolved resources

Once a resource is resolved for a run, Guild will not re-resolve
it. It will fail with an error message if a resource flag is specified
for a restart.

    >>> cwd = init_gf("""
    ... upstream:
    ...   main: guild.pass
    ... downstream:
    ...   main: guild.pass
    ...   requires:
    ...     - operation: upstream
    ... """)

Create an upstream run.

    >>> gh = run_gh(cwd, opspec="upstream")

Create a downstream run.

    >>> run(cwd, gh, opspec="downstream")
    Resolving upstream dependency
    Using run ... for upstream resource
    WARNING: nothing resolved for operation:upstream

Note the warning - upstream doesn't provide any files to resolve.

Restart the downstream run.

    >>> runs = var.runs(path(gh, "runs"), sort=["-timestamp"])
    >>> len(runs)
    2
    >>> downstream = runs[0]
    >>> downstream.opref.to_opspec()
    'downstream'

    >>> run(cwd, gh, restart=downstream.id)
    Resolving upstream dependency
    Skipping resolution of operation:upstream because it's already resolved

Note that a new run was NOT generated.

    >>> runs = var.runs(path(gh, "runs"), sort=["-timestamp"])
    >>> len(runs)
    2
    >>> runs[0].id == downstream.id
    True

Restart the downstream run with an upstream flag.

    >>> upstream = runs[1]
    >>> upstream.opref.to_opspec()
    'upstream'

    >>> run(cwd, gh, restart=downstream.id, flags=["upstream=%s" % upstream.id])
    cannot specify a value for 'upstream' when restarting ... - resource has
    already been resolved
    <exit 1>

## Run a batch

    >>> cwd = mkdtemp()
    >>> touch(path(cwd, "pass.py"))

    >>> gh = run_gh(cwd, opspec="pass.py", flags=["a=[1,2,3]"],
    ...             force_flags=True, quiet=True)

    >>> runs = var.runs(path(gh, "runs"), sort=["timestamp"])
    >>> len(runs)
    4

    >>> run_util.format_operation(runs[0])
    'pass.py+'

    >>> runs[0].get("flags")
    {}

    >>> run_util.format_operation(runs[1])
    'pass.py'

    >>> runs[1].get("flags")
    {'a': 1}

    >>> run_util.format_operation(runs[2])
    'pass.py'

    >>> runs[2].get("flags")
    {'a': 2}

    >>> run_util.format_operation(runs[3])
    'pass.py'

    >>> runs[3].get("flags")
    {'a': 3}

## Run in Background (Windows)

Guild doesn't support running in background on Windows.

    >>> cwd = mkdtemp()
    >>> touch(path(cwd, "pass.py"))

With `--background` flag:

    >>> _ = run_gh(cwd, opspec="pass.py", background=True)  # doctest: +WINDOWS_ONLY
    Run in background is not supported on Windows.
    <exit 1>
    
With `--pidfile` option:

    >>> _ = run_gh(cwd, opspec="pass.py", pidfile="not-used")  # doctest: +WINDOWS_ONLY
    Run in background is not supported on Windows.
    <exit 1>
