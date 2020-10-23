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
    cat
    check
    comment
    diff
    label
    ls
    pull
    push
    run
    runs
    stop
    tag
    watch

## ssh configuration

The ssh remote supports a number of configuration attributes. These
tests highlight some of the important nuances.

Helper function to return a remote for ssh config:

    >>> def ssh_remote(attrs, include_host=True):
    ...     ssh_config = {
    ...         "type": "ssh"
    ...     }
    ...     ssh_config.update(attrs)
    ...     if include_host and "host" not in attrs:
    ...         ssh_config["host"] = "a_host"
    ...     config = {
    ...         "remotes": {
    ...             "ssh": ssh_config
    ...         }
    ...     }
    ...     with UserConfig(config):
    ...         return guild.remote.for_name("ssh")

### Required ssh attrs

Host is required:

    >>> ssh_remote({}, include_host=False)
    Traceback (most recent call last):
    MissingRequiredConfig: host

    >>> ssh = ssh_remote({"host": "foo"})
    >>> ssh.host
    'foo'

### venv path

A virtual environment may be specified using either `venv-path` or
`guild-env`, which are synonymous.

    >>> ssh = ssh_remote({
    ...     "venv-path": "foo"
    ... })

    >>> ssh.venv_path
    'foo'

    >>> ssh = ssh_remote({
    ...     "guild-env": "foo"
    ... })

    >>> ssh.venv_path
    'foo'

### conda env

A Conda env may be specified as a path or as a name.

If specified as a path, it is used as specified.

    >>> ssh = ssh_remote({
    ...     "conda-env": "foo/bar"
    ... })

    >>> ssh.conda_env
    'foo/bar'

If specified as a name, then `guild-path` must also be specified.

    >>> ssh = ssh_remote({
    ...     "conda-env": "foo"
    ... })
    Traceback (most recent call last):
    ConfigError: cannot determine Guild home from conda-env 'foo' - specify
    a path for conda-env or specify guild-home

    >>> ssh = ssh_remote({
    ...     "conda-env": "foo",
    ...     "guild-home": "bar"
    ... })

    >>> ssh.conda_env
    'foo'

### Guild home

Guild home is `.guild` by default.

    >>> ssh = ssh_remote({})

    >>> ssh.guild_home
    '.guild'

Guild home may be specified using `guild-home`.

    >>> ssh = ssh_remote({
    ...     "guild-home": "foo"
    ... })

    >>> ssh.guild_home
    'foo'

If `venv-path` or `guild-env` is specified, and `guild-home` is not
specified, Guild home is derrived from the venv path.

    >>> ssh = ssh_remote({
    ...     "venv-path": "foo"
    ... })

    >>> ssh.guild_home
    'foo/.guild'

    >>> ssh = ssh_remote({
    ...     "guild-env": "foo"
    ... })

    >>> ssh.guild_home
    'foo/.guild'

    >>> ssh = ssh_remote({
    ...     "guild-env": "foo",
    ...     "guild-home": "bar"
    ... })

    >>> ssh.guild_home
    'bar'

If `conda-env` is specified and `guild-home` is not specified, Guild
home is derrived from `conda-env`.

    >>> ssh = ssh_remote({
    ...     "conda-env": "foo/bar"
    ... })

    >>> ssh.guild_home
    'foo/bar/.guild'

Note, as shown above, an error is raised if `conda-env` is not a path
with `guild-home` is not specified.

    >>> ssh_remote({
    ...     "conda-env": "bar"
    ... })
    Traceback (most recent call last):
    ConfigError: cannot determine Guild home from conda-env 'bar' - specify
    a path for conda-env or specify guild-home

    >>> ssh = ssh_remote({
    ...     "conda-env": "bar",
    ...     "guild-home": "foo"
    ... })

    >>> ssh.guild_home
    'foo'

## Misc

    >>> from guild.remotes.ssh import _quote_arg as quote
    >>> from guild.remotes.ssh import _noquote as noquote

    >>> quote(None)
    "''"

    >>> quote("")
    "''"

    >>> quote("a b")
    "'a b'"

    >>> quote("~/a/b")
    "'~/a/b'"

    >>> quote(noquote(""))
    ''

    >>> quote(noquote("a b"))
    'a b'

    >>> quote(noquote("~/a/b"))
    '~/a/b'

    >>> quote(noquote(None)) is None
    True

    >>> quote(noquote(123))
    123

    >>> bool(noquote(""))
    False

    >>> bool(noquote(None))
    False

    >>> bool(noquote("a b"))
    True
