# Op env

The environment used for an operation includes a combination of system
env, operation defined env, and run specific env.

This logic is implemented by `op._op_proc_env`.

    >>> from guild import op as oplib
    >>> op_env = oplib._op_proc_env

To illustrate, we need an operation:

    >>> op = oplib.Operation()

and a run:

    >>> from guild import run as runlib
    >>> run_dir = mkdtemp()
    >>> run = runlib.for_dir(run_dir)

For our tests, assert various locations:

    >>> cwd = os.getcwd()
    >>> guild_home = mkdtemp()

## Basic op env

With empty system env and op env:

    >>> op.cmd_env
    {}

    >>> with Env({}, replace=True):
    ...     with SetGuildHome(guild_home):
    ...         env = op_env(op, run)

    >>> sorted(env)
    ['CMD_DIR', 'GUILD_HOME', 'LOG_LEVEL', 'PYTHONPATH', 'RUN_DIR', 'RUN_ID']

    >>> env["CMD_DIR"] == cwd, (env, cwd)
    (True, ...)

    >>> env["GUILD_HOME"] == guild_home, (env, guild_home)
    (True, ...)

    >>> env["LOG_LEVEL"]
    '20'

    >>> env["RUN_DIR"] == run.dir, (env, run.dir)
    (True, ...)

    >>> env["RUN_ID"] == run.id, (env, run.id)
    (True, ...)

## System env

With some system env - a new var and a var that Guild defines.

    >>> with Env({"FOO": "env-foo", "GUILD_HOME": "env-guild-home"}, replace=True):
    ...     with SetGuildHome(guild_home):
    ...         env = op_env(op, run)

`FOO` is available, in addition to the vars above.

    >>> sorted(env)
    ['CMD_DIR', 'FOO', 'GUILD_HOME', 'LOG_LEVEL', 'PYTHONPATH',
     'RUN_DIR', 'RUN_ID']

`FOO` is as set in system env:

    >>> env["FOO"]
    'env-foo'

`GUILD_HOME` however is not defined by the env:

    >>> env["GUILD_HOME"] == "2"
    False

    >>> env["GUILD_HOME"] == guild_home, (env, guild_home)
    (True, ...)

## Op cmd

Let's define some operation env. This simulates what happens when an
operation defines env using the `env` attribute.

    >>> op.cmd_env = {
    ...     "FOO": "op-foo",
    ...     "BAR": "op-bar",
    ...     "GUILD_HOME": "op-guild-home",
    ...     "RUN_DIR": "op-run-dir",
    ... }

    >>> with Env({"FOO": "env-foo", "GUILD_HOME": "env-guild-home"}, replace=True):
    ...     with SetGuildHome(guild_home):
    ...         env = op_env(op, run)

The env contains the expected vars:

    >>> sorted(env)
    ['BAR', 'CMD_DIR', 'FOO', 'GUILD_HOME', 'LOG_LEVEL', 'PYTHONPATH',
     'RUN_DIR', 'RUN_ID']

As `FOO` is defined by the op, it overrides the system env:

    >>> env["FOO"]
    'op-foo'

However, `GUILD_HOME` is not defined by the op:

    >>> env["GUILD_HOME"] == "op-guild-home"
    False

    >>> env["GUILD_HOME"] == guild_home, (env, guild_home)
    (True, ...)

Neither is `RUN_DIR`:

    >>> env["RUN_DIR"] == "op-run-dir"
    False

    >>> env["RUN_DIR"] == run.dir, (env, run.dir)
    (True, ...)