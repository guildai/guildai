# guild-env

## activate guild-env

Try to activate a non-existing environment.

    >>> tmp = mkdtemp()

Activate from cwd:

    >>> cd(tmp)
    >>> run("bash -c 'source guild-env'")
    guild-env: cannot find a Guild environment in the current directory
    Try 'source guild-env PATH'.
    <exit 1>

Activate an explicit directory:

    >>> run("bash -c 'source guild-env %s'" % tmp)
    guild-env: cannot find a Guild environment in ...
    <exit 1>

Looking for `venv` and `env`.

    >>> quiet("mkdir -p env/bin")
    >>> quiet("echo 'echo from_env' > env/bin/activate")

    >>> quiet("mkdir -p venv/bin")
    >>> quiet("echo 'echo from_venv' > venv/bin/activate")

`venv` takes precedence over `env`:

    >>> run("bash -c 'source guild-env'")
    from_venv
    ... is active.
    <BLANKLINE>
    To deactivate the environment, run:
    <BLANKLINE>
      deactivate
    <BLANKLINE>
    Common commands:
    <BLANKLINE>
      guild check   Check the environment
      guild ops     List available operations
      guild runs    List runs
      guild run     Run an operation
      guild --help  Show Guild help
    <exit 0>

Remove `venv` and activate again.

    >>> quiet("rm -rf venv")
    >>> run("bash -c 'source guild-env'")
    from_env
    ... is active.
    ...
    <exit 0>
