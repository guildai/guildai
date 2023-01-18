# Run impl tests

These tests demonstrate various run behavior. There may be overlap
between these tests and others in the Guild test suite.

NOTE: The original tests here made calls to `guild.commands.run_impl`
directly in an apparent attempt to perform lower level testing. The
tests were inscrutable, however. It was unclear what benefit the lower
level approach provided beyond running Guild commands in a controlled
environment.

The current tests follow the same course but use `run()` commands
along with the now standard pattern of changing the cwd for project
isolation and setting Guild home for run isolation.

## Staging

Create a no-op Python script.

    >>> cd(mkdtemp())
    >>> set_guild_home(mkdtemp())
    >>> touch("run.py")

Stage a run in the default run location.

    >>> run("guild run run.py --stage -y")
    run.py staged as ...
    To start the operation, use 'guild run --start ...'

    >>> run("guild runs -s")
    [1]  run.py  staged

Staged files:

    >>> run("guild ls --all -n")  # doctest: +REPORT_UDIFF
    .guild/
    .guild/ENV
    .guild/STAGED
    .guild/attrs/
    .guild/attrs/cmd
    .guild/attrs/deps
    .guild/attrs/flags
    .guild/attrs/host
    .guild/attrs/id
    .guild/attrs/initialized
    .guild/attrs/op
    .guild/attrs/platform
    .guild/attrs/plugins
    .guild/attrs/random_seed
    .guild/attrs/run_params
    .guild/attrs/sourcecode_digest
    .guild/attrs/started
    .guild/attrs/user
    .guild/attrs/user_flags
    .guild/manifest
    .guild/opref
    run.py

Stage a run in an explicit run directory:

    >>> run_dir = mkdtemp()

    >>> run(f"guild run run.py --stage --run-dir {run_dir} -y")
    run.py staged in '...'
    To start the operation, use "(cd '...' && source .guild/ENV
    && ... -um guild.op_main run)"

Files in run directory:

    >>> find(run_dir)  # doctest: +REPORT_UDIFF
    .guild/ENV
    .guild/STAGED
    .guild/attrs/cmd
    .guild/attrs/deps
    .guild/attrs/flags
    .guild/attrs/host
    .guild/attrs/id
    .guild/attrs/initialized
    .guild/attrs/op
    .guild/attrs/platform
    .guild/attrs/plugins
    .guild/attrs/random_seed
    .guild/attrs/run_params
    .guild/attrs/sourcecode_digest
    .guild/attrs/started
    .guild/attrs/user
    .guild/attrs/user_flags
    .guild/manifest
    .guild/opref
    run.py

Create an operation def in the current directory that defines an
`exec` command.

    >>> cd(mkdtemp())
    >>> set_guild_home(mkdtemp())
    >>> write("guild.yml", """
    ... op:
    ...   exec: run.sh
    ... """)

Stage the operation.

    >>> run("guild run op --stage -y")
    op staged as ...
    To start the operation, use 'guild run --start ...'

    >>> run("guild runs -s")
    [1]  op  staged

Show all files for the staged run.

    >>> run("guild ls -na")  # doctest: +REPORT_UDIFF
    .guild/
    .guild/ENV
    .guild/STAGED
    .guild/attrs/
    .guild/attrs/cmd
    .guild/attrs/deps
    .guild/attrs/flags
    .guild/attrs/host
    .guild/attrs/id
    .guild/attrs/initialized
    .guild/attrs/op
    .guild/attrs/platform
    .guild/attrs/plugins
    .guild/attrs/random_seed
    .guild/attrs/run_params
    .guild/attrs/sourcecode_digest
    .guild/attrs/started
    .guild/attrs/user
    .guild/attrs/user_flags
    .guild/manifest
    .guild/opref
    guild.yml

Stage exec op in explicit run dir.

    >>> run_dir = mkdtemp()

    >>> run(f"guild run op --stage --run-dir {run_dir} -y")
    op staged in '...'
    To start the operation, use "(cd '...' && source .guild/ENV && run.sh)"

Files in the run directory:

    >>> find(run_dir)  # doctest: +REPORT_UDIFF
    .guild/ENV
    .guild/STAGED
    .guild/attrs/cmd
    .guild/attrs/deps
    .guild/attrs/flags
    .guild/attrs/host
    .guild/attrs/id
    .guild/attrs/initialized
    .guild/attrs/op
    .guild/attrs/platform
    .guild/attrs/plugins
    .guild/attrs/random_seed
    .guild/attrs/run_params
    .guild/attrs/sourcecode_digest
    .guild/attrs/started
    .guild/attrs/user
    .guild/attrs/user_flags
    .guild/manifest
    .guild/opref
    guild.yml

## Restart

Create a sample operation that uses `exec` to run a Python command
using a flag value.

    >>> cd(mkdtemp())
    >>> set_guild_home(mkdtemp())
    >>> write("guild.yml", """
    ... op:
    ...   exec: python -c 'import sys; sys.exit(${code})'
    ...   flags:
    ...     code: 0
    ... """)

Run the operation (we can omit the operation name because Guild uses
'op' by default).

    >>> run("guild run code=11 -y")
    <exit 11>

    >>> run("guild runs -s")
    [1]  op  error  code=11

Flags used for the run:

    >>> run("guild select --attr flags")
    code: 11

The `code` flag is encoded in the run env using the `FLAG_CODE`
variable.

    >>> env_str = run_capture("guild select --attr env")
    >>> yaml.safe_load(env_str)["FLAG_CODE"]
    '11'

Restart the run. Guild uses the original flag values for the new
process.

    >>> run_id = run_capture("guild select")
    >>> run(f"guild run --restart {run_id} -y")
    <exit 11>

    >>> run("guild runs -s")
    [1]  op  error  code=11

    >>> run("guild select --attr flags")
    code: 11

    >>> env_str = run_capture("guild select --attr env")
    >>> yaml.safe_load(env_str)["FLAG_CODE"]
    '11'

Restart the run using a different code flag.

    >>> run(f"guild run --restart {run_id} code=22 -y")
    <exit 22>

    >>> run("guild runs -s")
    [1]  op  error  code=22

    >>> run("guild select --attr flags")
    code: 22

    >>> env_str = run_capture("guild select --attr env")
    >>> yaml.safe_load(env_str)["FLAG_CODE"]
    '22'

### Starting staged runs

Guild does not differentiate between "start" and "restart" -- it's the
same operation. However, the `run` command accepts both `--start` and
`--restart` options. These can be used interchangeably according to
user intent.

By convention, when we start a staged run, we use `--start` and not
`--restart`.

To illustrate, we stage a run.

    >>> run("guild run code=33 --stage -y")
    op staged as ...
    To start the operation, use 'guild run --start ...'

    >>> run("guild runs -s")
    [1]  op  staged  code=33
    [2]  op  error   code=22

As an aside, the `flags` attribute is defined as with an executed run.

    >>> run("guild select --attr flags")
    code: 33

However, the `env` is not set for staged runs (this is deferred until execution).

    >>> run("guild select --attr env")
    guild: no such run attribute 'env'
    <exit 1>

Start the staged run.

    >>> run_id = run_capture("guild select")
    >>> run(f"guild run --start {run_id} -y")
    <exit 33>

    >>> run("guild runs -s")
    [1]  op  error  code=33
    [2]  op  error  code=22

    >>> run("guild select --attr flags")
    code: 33

    >>> env_str = run_capture("guild select --attr env")
    >>> yaml.safe_load(env_str)["FLAG_CODE"]
    '33'

Stage another run.

    >>> run("guild run code=44 --stage -y")
    op staged as ...
    To start the operation, use 'guild run --start ...'

    >>> run("guild runs -s")
    [1]  op  staged  code=44
    [2]  op  error   code=33
    [3]  op  error   code=22

    >>> run("guild select --attr flags")
    code: 44

Start the run with a different code.

    >>> run_id = run_capture("guild select")
    >>> run(f"guild run --start {run_id} code=55 -y")
    <exit 55>

    >>> run("guild runs -s")
    [1]  op  error  code=55
    [2]  op  error  code=33
    [3]  op  error  code=22

    >>> run("guild select --attr flags")
    code: 55

    >>> env_str = run_capture("guild select --attr env")
    >>> yaml.safe_load(env_str)["FLAG_CODE"]
    '55'

## Restart without opdef

A run can be restarted without when its opdef is missing. However,
user cannot specify flags.

Reset the environment.

    >>> cd(mkdtemp())
    >>> set_guild_home(mkdtemp())

Define an operation that writes files based on flag values. In
addition, it writes a file containing 'x' chars in its name, one 'x'
for each time the operation is run. This is used to track the
successful restart of the run.

    >>> write("guild.yml", """
    ... op:
    ...   main: op ${foo} ${bar}
    ...   flags:
    ...     foo: 123
    ...     bar: 456
    ... """)

    >>> write("op.py", """
    ... import sys, glob
    ... foo, bar = sys.argv[1:3]
    ... open(foo, "w").close()
    ... open(bar, "w").close()
    ... try:
    ...     xname = max(glob.glob("x*")) + "x"
    ... except ValueError:
    ...     xname = "x"
    ... open(xname, "w").close()
    ... """)

Generate a run:

    >>> run("guild run op foo=321 -y")
    <exit 0>

    >>> run("guild runs -s")
    [1]  op  completed  bar=456 foo=321

The run contains a single file 'x', indicating that it's been run
once.

    >>> run("guild ls -n")
    321
    456
    guild.yml
    op.py
    x

The run info:

    >>> run("guild runs info")
    id: ...
    operation: op
    from: .../guild.yml
    status: completed
    started: ...
    stopped: ...
    marked: no
    label: bar=456 foo=321
    sourcecode_digest: 04d76111543aff83d53d9573a293eba1
    vcs_commit:
    run_dir: ...
    command: ... -um guild.op_main op 321 456 -- --bar 456 --foo 321
    exit_status: 0
    pid:
    tags:
    flags:
      bar: 456
      foo: 321
    scalars:

With the project in place, we can restart the run using different flag
values.

    >>> run_id = run_capture("guild select")

    >>> run(f"guild run --restart {run_id} foo=123 bar=654 -y")
    <exit 0>

    >>> run("guild runs -s")
    [1]  op  completed  bar=654 foo=123

The script generates two additional files based on the new flag values
and writes 'xx' as it's the second time it's been run.

    >>> run("guild ls -n")
    123
    321
    456
    654
    guild.yml
    op.py
    x
    xx

The run info is updated accordingly:

    >>> run("guild runs info")
    id: ...
    operation: op
    from: .../guild.yml
    status: completed
    started: ...
    stopped: ...
    marked: no
    label: bar=654 foo=123
    sourcecode_digest: 04d76111543aff83d53d9573a293eba1
    vcs_commit:
    run_dir: ...
    command: ... -um guild.op_main op 123 654 -- --bar 654 --foo 123
    exit_status: 0
    pid:
    tags:
    flags:
      bar: 654
      foo: 123
    scalars:

If we delete the project config, we cannot restart the run using flag
values.

    >>> rm("guild.yml")

    >>> run(f"guild run --restart {run_id} foo=111 bar=222 -y")
    guild: cannot find definition for operation 'op' in run ...
    This is required when setting flags or using '--force-sourcecode'
    for restart or a new run.
    <exit 1>

We can restart the run if we don't specify new flag values.

    >>> run(f"guild run --restart {run_id} -y")
    <exit 0>

Here we see 'xxx', indicating that the operation has been successfully
run three times.

    >>> run("guild ls -n")
    123
    321
    456
    654
    guild.yml
    op.py
    x
    xx
    xxx

## Batch operation errors

When optimizer flags are specified for a run command, Guild requires
an optimizer. One must be specified for the run command or defined for
the operation.

Create a new operation that does not specify a default optimizer:

    >>> cd(mkdtemp())
    >>> set_guild_home(mkdtemp())

    >>> write("guild.yml", """
    ... op:
    ...   main: guild.pass
    ... """)

Run `op` with an optimizer flag but with no optimizer:

    >>> run("guild run op -Fo foo=123 -y")
    guild: invalid optimizer flag foo=123: no optimizer specified
    <exit 1>

If we specify an optimizer, we get an error message indicating that
the specified flag is invalid.

    >>> run("guild run op -Fo foo=123 -o random -y")
    guild: unsupported flag 'foo'
    Try 'guild run skopt:random --help-op' for a list of flags or
    use --force-flags to skip this check.
    <exit 1>

## Dependencies

Create a project that defines upstream and downstream operations:

    >>> cd(mkdtemp())
    >>> set_guild_home(mkdtemp())

    >>> write("guild.yml", """
    ... upstream:
    ...   main: guild.pass
    ...   requires:
    ...     - file: src.txt
    ... downstream:
    ...   main: guild.pass
    ...   sourcecode:
    ...     - exclude: src.txt
    ...   requires:
    ...     - operation: upstream
    ...       select: src.txt
    ... """)

Confirm that we don't have any runs:

    >>> run("guild runs -s")
    <exit 0>

If we run the downstream operation, we get a warning message that a
required upstream run isn't available and the run fails.

    >>> run("guild run downstream -y")
    WARNING: cannot find a suitable run for required resource 'operation:upstream'
    Resolving operation:upstream
    guild: run failed because a dependency was not met: could not resolve
    'operation:upstream' in operation:upstream resource: no suitable run for upstream
    <exit 1>

    >>> run("guild runs -s")
    [1]  downstream  error

When we run the upstream operation, the run fails because a required
file is missing.

    >>> run("guild run upstream -y")
    Resolving file:src.txt
    guild: run failed because a dependency was not met: could not resolve
    'file:src.txt' in file:src.txt resource: cannot find source file 'src.txt'
    <exit 1>

    >>> run("guild runs -s")
    [1]  upstream    error
    [2]  downstream  error
    <exit 0>

Define the required file:

    >>> write("src.txt", "hello")

Run upstream again.

    >>> run("guild run upstream -y")
    Resolving file:src.txt

    >>> run("guild ls -n")
    guild.yml
    src.txt

    >>> run("guild runs info --deps")
    id: ...
    operation: upstream
    from: .../guild.yml
    status: completed
    started: ...
    stopped: ...
    marked: no
    label:
    sourcecode_digest: c81c840dde4f3f7f7cae9399a04d134e
    vcs_commit:
    run_dir: ...
    command: ... -um guild.op_main guild.pass --
    exit_status: 0
    pid:
    tags:
    flags:
    scalars:
    dependencies:
      file:src.txt:
        file:src.txt:
          paths:
          - .../src.txt
          uri: file:src.txt

The dependencies for the run are defined in the `deps` attribute.

    >>> run("guild select --attr deps")
    file:src.txt:
      file:src.txt:
        paths:
        - .../src.txt
        uri: file:src.txt

With an upstream run to resolve, we can run the downstream operation.

    >>> run("guild run downstream -y")
    Resolving operation:upstream
    Using run ... for operation:upstream

    >>> run("guild runs -s")
    [1]  downstream  completed  operation:upstream=...
    [2]  upstream    completed
    [3]  upstream    error
    [4]  downstream  error

    >>> run("guild ls -n")
    guild.yml
    src.txt

    >>> run("guild select --attr deps")
    operation:upstream:
      operation:upstream:
        config: ...
        paths:
        - ../.../src.txt
        uri: operation:upstream

The 'config' attribute of an operation dependency is the resolved run
ID.

Create a helper function to confirm that a specific run is used for an
operation resolution.

    >>> def assert_resolved_run(expected_run_args, parent_run_args=""):
    ...     deps_encoded = run_capture(f"guild select {parent_run_args} --attr deps")
    ...     deps = yaml.safe_load(deps_encoded)
    ...     expected_run_id = run_capture(f"guild select {expected_run_args}")
    ...     resolved_run_id = deps["operation:upstream"]["operation:upstream"]["config"]
    ...     assert expected_run_id == resolved_run_id, (deps, expected_run_id)

Verify that the expected run was resolved.

    >>> assert_resolved_run("2")

Run upstream again. The second, most recent succesful run is used for
subsequent operation resolutions.

    >>> run("guild run upstream -y")
    Resolving file:src.txt

    >>> run("guild run downstream -y")
    Resolving operation:upstream
    Using run ... for operation:upstream

    >>> assert_resolved_run("2")

We can mark the first `upstream` run, which tells Guild to use that
run when resolving `upstream` operation dependencies.

    >>> run("guild mark 4 -y")
    Marked 1 run(s)

Run `downstream` again:

    >>> run("guild run downstream -y")
    Resolving operation:upstream
    Using run ... for operation:upstream

    >>> run("guild runs -s")
    [1]  downstream         completed  operation:upstream=...
    [2]  downstream         completed  operation:upstream=...
    [3]  upstream           completed
    [4]  downstream         completed  operation:upstream=...
    [5]  upstream [marked]  completed
    [6]  upstream           error
    [7]  downstream         error

Guild uses the marked run (run '5') to satisfy the upstream
dependency.

    >>> assert_resolved_run("5")

We can also use `select` with filters to find the marked run,

    >>> assert_resolved_run("-Fo upstream -Fm")

## Staging dependencies

Guild stages dependencies differently depending on whether or not they
are operations. Operations are not resolved at stage time. All other
resource types are resolved at stage time.

Create a new project to illustrate.

    >>> use_project(mkdtemp())
    >>> write("guild.yml", """
    ... upstream:
    ...   main: guild.pass
    ...   requires:
    ...     - file: src.txt
    ... downstream:
    ...   main: guild.pass
    ...   sourcecode:
    ...     - exclude: src.txt
    ...   requires:
    ...     - operation: upstream
    ...       select: src.txt
    ... """)

When we stage `downstream`, which requires `upstream`, we succeed -
Guild doesn't attempt to resolve operation dependencies when staging.

    >>> run("guild run downstream --stage -y")
    WARNING: cannot find a suitable run for required resource 'operation:upstream'
    Resolving operation:upstream
    Skipping resolution of operation:upstream because it's being staged
    downstream staged as ...
    To start the operation, use 'guild run --start ...'

When start the staged run we get an error because there's not suitable
upstream run.

    >>> staged_downstream = run_capture("guild select")

    >>> run(f"guild run --start {staged_downstream} -y")
    Resolving operation:upstream
    guild: run failed because a dependency was not met: could not
    resolve 'operation:upstream' in operation:upstream resource: no
    suitable run for upstream
    <exit 1>

Let's try to stage upstream - the operation fails because other
resources are resolved during stage.

    >>> run("guild run upstream --stage -y")
    Resolving file:src.txt
    guild: run failed because a dependency was not met: could not resolve
    'file:src.txt' in file:src.txt resource: cannot find source file 'src.txt'
    <exit 1>

Create the required `src.txt` file.

    >>> write("src.txt", "yo")

Stage an upstream run again, specifying a run ID to later verify that
this run is used by downstream.

    >>> run("guild run upstream --stage --run-id up1 -y")
    Resolving file:src.txt
    upstream staged as ...
    To start the operation, use 'guild run --start ...'

Our runs:

    >>> run("guild runs")
    [1:up1]  upstream    ...  staged
    [2:...]  upstream                         error
    [3:...]  downstream  ...  error

With a staged `upstream` run, Guild can resolve that dependency in
`downstream`.

    >>> run("guild run downstream --stage --run-id down1 -y")
    Resolving operation:upstream
    Skipping resolution of operation:upstream because it's being staged
    downstream staged as down1
    To start the operation, use 'guild run --start down1'

    >>> run("guild runs")
    [1:down1] downstream  ...  staged  operation:upstream=up1
    [2:up1]   upstream    ...  staged
    [3:...]   upstream         error
    [4:...]   downstream  ...  error

Staged `downstream` is configured to use the currently staged
upstream. However, the run fails because the resolved dependency is
staged and not completed.

    >>> run("guild run --start down1 -y")
    Resolving operation:upstream
    guild: run failed because a dependency was not met: could not
    resolve 'operation:upstream' in operation:upstream resource: no
    suitable run for upstream
    <exit 1>

Start the upstream run.

    >>> run("guild run --start up1 -y")
    Resolving file:src.txt
    Skipping resolution of file:src.txt because it's already resolved

The staged downstream now runs.

    >>> run("guild run --start down1 -y")
    Resolving operation:upstream
    Using run up1 for operation:upstream

    >>> run("guild runs")
    [1:down1] downstream  ...  completed  operation:upstream=up1
    [2:up1]   upstream    ...  completed
    [3:...]   upstream         error
    [4:...]   downstream  ...  error

    >>> run("guild select --attr deps")
    operation:upstream:
      operation:upstream:
        config: up1
        paths:
        - ../up1/src.txt
        uri: operation:upstream

## Restarts and resolved resources

See [restart-resolve.md](restart-resolve.md).

## Run a batch

Create a new project.

    >>> use_project(mkdtemp())

    >>> touch("pass.py")

Run a batch of three trials.

    >>> run("guild run pass.py a=[1,2,3] --force-flags --keep-batch -y")
    INFO: [guild] Running trial ...: pass.py (a=1)
    INFO: [guild] Running trial ...: pass.py (a=2)
    INFO: [guild] Running trial ...: pass.py (a=3)

    >>> run("guild runs -s")
    [1]  pass.py   completed  a=3
    [2]  pass.py   completed  a=2
    [3]  pass.py   completed  a=1
    [4]  pass.py+  completed

    >>> run("guild select --attr flags 1")
    a: 3

    >>> run("guild select --attr flags 2")
    a: 2

    >>> run("guild select --attr flags 3")
    a: 1

    >>> run("guild select --attr flags 4")
    {}

## Run in Background (Windows)

Guild doesn't support running in background on Windows.

To illustreate, create a new project.

    >>> use_project(mkdtemp())

    >>> touch("pass.py")

Attempt to run an operation in the background on Windows.

    >>> run("guild run pass.py --background -y")  # doctest: +WINDOWS_ONLY
    Run in background is not supported on Windows.
    <exit 1>

    >>> run("guild run pass.py --pidfile not0used -y")  # doctest: +WINDOWS_ONLY
    Run in background is not supported on Windows.
    <exit 1>
