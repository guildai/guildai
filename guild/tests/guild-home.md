# Guild Home

Guild home is a location where Guild stores runs and cached resources.

Guild home is created as needed when certain operations are run.

## Setting Guild Home

Guild home may be set in two ways:

- `GUILD_HOME` environment variable
- Specifying `-H` for the `guild` command

We'll illustrate the use of the `GUILD_HOME` environment variable.

Here's a sample Guild home directory:

    >>> guild_home_1 = mkdtemp()
    >>> find(guild_home_1)
    <empty>

Let's simulate a command using the main command interface.

    >>> from guild.commands import main

    >>> def run(args):
    ...     try:
    ...         main.main(args)
    ...     except SystemExit as e:
    ...         assert not e.code, e.code

Let's list runs in our Guild home under using the `GUILD_HOME`
environment variable:

    >>> with Env({"GUILD_HOME": guild_home_1}):
    ...     run(["runs"])

Here's the contents of our Guild home:

    >>> find(guild_home_1)
    .guild-nocopy

Let's run the same test but using the `-H` option.

First a new Guild home:

    >>> guild_home_2 = mkdtemp()
    >>> find(guild_home_2)
    <empty>

And list runs with the `-H` option:

    >>> run(["-H", guild_home_2, "runs"])

And the contents of Guild home:

    >>> find(guild_home_2)
    .guild-nocopy

## Default Guild Home

If Guild Home is not otherwise specified (see above) Guild uses the
following scheme to locate Guild home relative to the current
directory:

- Use `.guild` directory in the current directory, if it exists
- Otherwise look in the current directory parent for `.guild` and use
  it, if it exists
- Otherwise continue looking in subsequent parent directories for
  `.guild` stopping at the user home directory or the volume root
  directory

Let's demonstrate using a sample nested hiearchy.

    >>> tmp = mkdtemp()
    >>> mkdir(path(tmp, "a"))
    >>> mkdir(path(tmp, "a", ".guild"))
    >>> mkdir(path(tmp, "a", "b"))
    >>> mkdir(path(tmp, "a", "b", "c"))
    >>> mkdir(path(tmp, "a", "b", "c", ".guild"))

    >>> find(tmp, includedirs=True)
    a
    a/.guild
    a/b
    a/b/c
    a/b/c/.guild

References to these directories:

    >>> a_dir = path(tmp, "a")
    >>> ab_dir = path(tmp, "a", "b")
    >>> abc_dir = path(tmp, "a", "b", "c")

Helper to get Guild home using `guild.config.default_guild_home()`,
which bypasses any explicitly set value in the VM.

    >>> from guild.config import default_guild_home

    >>> def guild_home_for_dir(dir, config=None, extra_env=None):
    ...     env = {"GUILD_HOME": ""}
    ...     if extra_env:
    ...         env.update(extra_env)
    ...     with SetUserConfig(config or {}):
    ...         with SetCwd(dir):
    ...             with Env(env):
    ...                 return default_guild_home()

Guild home for `a/b/c` is `a/b/c/.guild`.

    >>> gh = guild_home_for_dir(abc_dir)
    >>> gh == path(abc_dir, ".guild"), (gh, abc_dir)
    (True, ...)

Guild home for `a/b` is `a/.guild` (note that `a/b/.guild` does not
exist).

    >>> gh = guild_home_for_dir(ab_dir)
    >>> gh == path(a_dir, ".guild"), (gh, a_dir)
    (True, ...)

Guild home for `a` is `a/.guild`.

    >>> gh = guild_home_for_dir(a_dir)
    >>> gh == path(a_dir, ".guild"), (gh, a_dir)
    (True, ...)

### Using pre-0.9 behavior

A user may set the `legacy.guild-home` user config to 'pre-0.9' to use
the pre-0.9 behavior when determining Guild home. This behavior always
uses `~/.guild` as Guild home when it's not otherwise specified by
`GUILD_HOME` or the `-H` command option.

Config indicating pre-0.9 Guild home scheme:

    >>> pre0_9_config = {"legacy": {"guild-home": "pre-0.9"}}

User home:

    >>> user_home = os.path.expanduser("~")

We need to remove `VIRTUAL_ENV` and `CONDA_PREFIX` to ensure these
aren't used, if set.

    >>> disable_venv = {"VIRTUAL_ENV": "", "CONDA_PREFIX": ""}

Guild home for `a/b/c`:

    >>> gh = guild_home_for_dir(abc_dir, pre0_9_config, disable_venv)
    >>> gh == path(user_home, ".guild"), (gh, abc_dir, user_home)
    (True, ...)

Guild home for `a/b` is `a/.guild` (note that `a/b/.guild` does not
exist).

    >>> gh = guild_home_for_dir(ab_dir, pre0_9_config, disable_venv)
    >>> gh == path(user_home, ".guild"), (gh, ab_dir, user_home)
    (True, ...)

Guild home for `a` is `a/.guild`.

    >>> gh = guild_home_for_dir(a_dir, pre0_9_config, disable_venv)
    >>> gh == path(user_home, ".guild"), (gh, a_dir, user_home)
    (True, ...)

When `GUILD_HOME` is set, it is used regardless of the scheme or
environment.

    >>> guild_home_for_dir("/foo", None, {"GUILD_HOME": "/foo"})
    '/foo'

    >>> guild_home_for_dir("/foo", pre0_9_config, {"GUILD_HOME": "/foo"})
    '/foo'

### Invalid legacy config

Guild logs a warning message if the config is not recognized/supported.

Specify `guild-home` that isn't supported.

    >>> invalid_config = {"legacy": {"guild-home": "not-valid"}}

    >>> with LogCapture() as logs:
    ...     _ = guild_home_for_dir(".", invalid_config, None)

    >>> logs.print_all()
    WARNING: unsupported legacy scheme for 'guild-home': 'not-valid' -
    using default scheme
