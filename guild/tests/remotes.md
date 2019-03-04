# Remotes

These tests demonstrate Guild's remote functionality as implemented by
`guild.remote`:

    >>> import guild.remote

Guild supports a remote interface as defined by the class
`guild.remote.Remote`.

Remotes are instantiated using `guild.remote.for_name` by proving the
name of a remote defined in user config.

By default, user config is defined in `~/.guild/config.yml`. We can
provide an explicit config in a call to `for_name`.

Here's a sample user config with a `ssh` remote definition:

    >>> user_config = {
    ...   "remotes": {
    ...     "ssh": {
    ...       "type": "ssh",
    ...       "host": "localhost",
    ...     }
    ...   }
    ... }

Let's create a remote for `ssh` using the config:

    >>> with UserConfig(user_config):
    ...     remote = guild.remote.for_name("ssh")

    >>> remote.name
    'ssh'

    >>> remote
    <guild.remotes.ssh.SSHRemote object ...>

The various methods of `remote` are used to implement Guild commands
on the remote target.

Here are the commands that support the `remote` param:

    >>> from guild.commands import main
    >>> for _, cmd in sorted(main.main.commands.items()):
    ...     for param in cmd.params:
    ...         if param.name == "remote":
    ...             print(cmd.name)
    ...             break
    check
    label
    pull
    push
    run
    runs
    stop
    watch
