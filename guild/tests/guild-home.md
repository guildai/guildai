# Guild Home

Guild home is a location where Guild stores runs and cached resources.

Guild home is created as needed when certain operations are run.

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
