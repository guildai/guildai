# Restarting runs

The user can restarts a run using the `--restart` option.

Use the `optimizers` project for our tests.

    >>> use_project("optimizers")

Run `echo.py` with the default flag values.

    >>> run("guild run echo.py -y")
    1.0 2 'a'

Run `echo.py` a second time with explicit flag values.

    >>> run("guild run echo.py x=2.0 y=3 z=b -y")
    2.0 3 'b'

    >>> run("guild runs -s")
    [1]  echo.py  completed  x=2.0 y=3 z=b
    [2]  echo.py  completed  x=1.0 y=2 z=a

Restart the latest run. Guild restarts it using its original flag
values.

    >>> last_run = run_capture("guild select")

    >>> run(f"guild run --restart {last_run} -y")
    2.0 3 'b'

    >>> run(f"guild select -a flags {last_run}")
    x: 2.0
    y: 3
    z: b

Restart the run with a modified flag value.

    >>> run(f"guild run --restart {last_run} x=10 -y")
    10 3 'b'

    >>> run(f"guild select -a flags {last_run}")
    x: 10
    y: 3
    z: b

Restart it again, this time with no explicit flag values. Guild uses
the flag values from the last restart.

    >>> run(f"guild run --restart {last_run} -y")
    10 3 'b'

    >>> run(f"guild select -a flags {last_run}")
    x: 10
    y: 3
    z: b

## Restart with `--needed`

When run with `--restart`, the `--needed` option tells Guild to run
the operation only if needs to be based on its status and the command
flag values. If the run-to-be-restarted is not completed or different
flag values are specified for the command, Guild restarts the
run. Otherwise it skips the restart and shows a message.

For additional tests related to *needed*, see
[`needed.md`](needed.md).

Attempt to restart the latest run using the `--needed` flag. In this
case Guild skips the restart because it is not needed.

    >>> run(f"guild run --restart {last_run} --needed -y")
    Skipping run because flags have not changed (--needed specified)

    >>> run(f"guild select -a flags {last_run}")
    x: 10
    y: 3
    z: b

Restart using explicit flag values that equal those from the
restarting run. Guild again skips the run because it's already
completed and the flag values have not changed.

    >>> run(f"guild run --restart {last_run} --needed x=10 y=3 -y")
    Skipping run because flags have not changed (--needed specified)

    >>> run(f"guild select -a flags {last_run}")
    x: 10
    y: 3
    z: b

Restart using modified flag values. In this case, Guild considers the
restart to be needed and proceeds.

    >>> run(f"guild run --restart {last_run} --needed x=100 -y")
    100 3 'b'

    >>> run(f"guild select -a flags {last_run}")
    x: 100
    y: 3
    z: b

## Run params for restarts

The `op_util` module provides the function `run_params_for_restart`
that returns a list of run params that should be used when restarting
a particular run. The params are based on the params that were used
when originally running or staging the run.

    >>> from guild.op_util import run_params_for_restart

Get the run params for restarting the latest run.

    >>> from guild import run as runlib

    >>> last_run = runlib.for_dir(run_capture("guild select --dir"))
    >>> pprint(run_params_for_restart(last_run))
    {'force_flags': False,
     'gpus': None,
     'max_trials': None,
     'maximize': None,
     'minimize': None,
     'no_gpus': False,
     'opt_flags': [],
     'optimizer': None,
     'random_seed': ...}

## Check for restart

`op_util.restart_needed` determined whether or not a run needs to be
restarted based on a set of flag values.

    >>> from guild.op_util import restart_needed

Show the latest run flag values.

    >>> pprint(last_run.get("flags"))
    {'x': 100, 'y': 3, 'z': 'b'}

Use `restart_needed` to check whether or not various flag values
combinations would triggr a restart when `--needed` is specified.

    >>> restart_needed(last_run, {})
    True

    >>> restart_needed(last_run, {"x": 100})
    True

    >>> restart_needed(last_run, {"x": 100, "y": 3})
    True

    >>> restart_needed(last_run, {"x": 100, "y": 3, "z": "b"})
    False

    >>> restart_needed(last_run, {"x": 100, "y": 3, "z": "b", "a": 0})
    True

## Restarts and Source Code

By default, a restart uses unmodified soure code.

To illustate, create a custom project with a sample hello script.

    >>> use_project(mkdtemp())

    >>> write("hello.py", "print('hello-1')\n")

Run the script.

    >>> run("guild run hello.py -y")
    hello-1

    >>> run("guild cat -p hello.py")
    print('hello-1')

Modify the script to print a different message.

    >>> write("hello.py", "print('hello-2')\n")

Restart the run.

    >>> last_run = run_capture("guild select")

    >>> run(f"guild run --restart {last_run} -y")
    hello-1

    >>> run("guild cat -p hello.py")
    print('hello-1')

Restart the run with `--fource-sourcecode`.

    >>> run(f"guild run --restart {last_run} --force-sourcecode -y")
    hello-2

    >>> run("guild cat -p hello.py")
    print('hello-2')
