# Invalid `chdir`

Users may specify a directory to act as the current directory for a
command using the `-C` option.

If the specified value doesn't exist:

    >>> run("guild -C foobar models")
    guild: directory 'foobar' does not exist
    <exit 1>

If the specified value isn't a directory:

    >>> run("guild -C examples/mnist/guild.yml models")
    guild: 'examples/mnist/guild.yml' is not a directory
    <exit 1>
