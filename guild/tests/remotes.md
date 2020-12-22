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

## Remotes from Specs

### S3

    >>> remote = guild.remote.for_spec("s3:foo/bar")
    >>> remote
    <guild.remotes.s3.S3Remote object at ...>

    >>> remote.name
    's3:foo/bar'

    >>> remote.bucket
    'foo'

    >>> remote.root
    '/bar'

    >>> print(remote.region)
    None

    >>> remote.local_env
    {}

    >>> remote.local_sync_dir
    '.../remotes/s3-foo-bar/meta/1ce28f3340b3334b1b181b3a874486c6'

### SSH

    >>> def ssh_remote(spec):
    ...     remote = guild.remote.for_spec(spec)
    ...     pprint({
    ...         "name": remote.name,
    ...         "host": remote.host,
    ...         "user": remote.user,
    ...         "port": remote.port,
    ...         "venv_path": remote.venv_path,
    ...     }, width=60)

    >>> ssh_remote("ssh:foo")
    {'host': 'foo',
     'name': 'foo',
     'port': None,
     'user': None,
     'venv_path': None}

    >>> ssh_remote("ssh:me@foo")
    {'host': 'foo',
     'name': 'me@foo',
     'port': None,
     'user': 'me',
     'venv_path': None}

    >>> ssh_remote("ssh:me@foo:2222")
    {'host': 'foo',
     'name': 'me@foo:2222',
     'port': 2222,
     'user': 'me',
     'venv_path': None}

    >>> ssh_remote("ssh:me@foo:2222:~/env/guild-123")
    {'host': 'foo',
     'name': 'me@foo:2222:~/env/guild-123',
     'port': 2222,
     'user': 'me',
     'venv_path': '~/env/guild-123'}

    >>> ssh_remote("ssh:me@foo:~/env/guild-123")
    {'host': 'foo',
     'name': 'me@foo:~/env/guild-123',
     'port': None,
     'user': 'me',
     'venv_path': '~/env/guild-123'}

    >>> ssh_remote("ssh:foo:~/env/guild-123")
    {'host': 'foo',
     'name': 'foo:~/env/guild-123',
     'port': None,
     'user': None,
     'venv_path': '~/env/guild-123'}

### Non-existing spec

    >>> print(guild.remote.for_spec("foo"))
    None

### Errors

    >>> guild.remote.for_spec("foo:")
    Traceback (most recent call last):
    UnsupportedRemoteType: foo

Unless the env var `GIST_USER` is defined, a gist spec must specify a
user along with a gist name.

    >>> with Env({}, replace=True):
    ...     guild.remote.for_spec("gist:foo")
    Traceback (most recent call last):
    MissingRequiredEnv: gist remotes must be specified as USER/GIST_NAME
    if GIST_USER environment variable is not defined

### Remote types that don't support specs

    >>> guild.remote.for_spec("ec2:xxx")
    Traceback (most recent call last):
    RemoteForSpecNotImplemented: ('ec2', 'xxx')

    >>> guild.remote.for_spec("azure-blob:yyy")
    Traceback (most recent call last):
    RemoteForSpecNotImplemented: ('azure-blob', 'yyy')

## Misc

### Quoting ssh args

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

### Local meta dirs

    >>> from guild.remotes.meta_sync import local_meta_dir

    >>> def _meta_dir(remote_name, key):
    ...     with Env({"GUILD_CONFIG": "/HOME/guild.yml"}):
    ...         return local_meta_dir(remote_name, key)

    >>> _meta_dir("foo", "bar")
    '/HOME/remotes/foo/meta/37b51d194a7513e45b56f6524f2d51f2'

    >>> _meta_dir("foo", "bar2")
    '/HOME/remotes/foo/meta/224e2539f52203eb33728acd228b4432'

    >>> _meta_dir("s3:guild-uat/default", "guild-uat/default")
    '/HOME/remotes/s3-guild-uat-default/meta/6b5ef651b8a674a8c47a7ee4436792c0'


### Safe filenames for remote names

    >>> from guild.remotes.meta_sync import _safe_filename

    >>> _safe_filename("")
    ''

    >>> _safe_filename("a")
    'a'

    >>> _safe_filename("a-b")
    'a-b'

    >>> _safe_filename("a/b")
    'a-b'

    >>> _safe_filename("//a///b//")
    'a-b'

    >>> _safe_filename(":/^%$#@!")
    '-'
