# Guild config

The module `guild.config` handles user config.

    >>> from guild import config

## User config paths

User config is specified using one of three methods, listed in order
of precedence:

- In a path specified by the `GUILD_CONFIG` environment variable
- `guild-config.yml` in the current working directory
- `$GUILD_HOME/config.yml`
- `~/.guild/config.yml`

Define user config in three locations.

An arbitrary directory (will be specified using environment variable
`GUILD_CONFIG`):

    >>> other_dir = mkdtemp()
    >>> other_guild_config = path(other_dir, "guild-config.yml")
    >>> write(other_guild_config, """remotes:
    ...   foo:
    ...     description: Remote defined in arbitrary location
    ... """)

Create a sample project, which includes two project-based user config
files.

First config, `guild-config.yml`:

    >>> project_dir = mkdtemp()
    >>> write(path(project_dir, "guild-config.yml"), """remotes:
    ...   foo:
    ...     description: Remote defined in project user config
    ... """)

Second config, `.guild/config.yml`:

    >>> mkdir(path(project_dir, ".guild"))
    >>> write(path(project_dir, ".guild", "config.yml"), """remotes:
    ...   bar:
    ...     description: Remote defined in project user config v2
    ... """)

Project layout:

    >>> find(project_dir)
    .guild/config.yml
    guild-config.yml

Create a directory simulating user home (will be used by hacking the
HOME env var).

    >>> fake_home = mkdtemp()
    >>> mkdir(path(fake_home, ".guild"))
    >>> write(path(fake_home, ".guild", "config.yml"), """remotes:
    ...   foo:
    ...     description: Remote defined in default location
    ... """)

For each of the tests below, we override any explicitly set Guild home
(e.g. via `config.set_guild_home()`) and use the project `.guild`
directory. This ensuree that Guild doesn't use any activated virtual
environments for Guild home by default.

    >>> project_gh = path(project_dir, ".guild")

`GUILD_CONFIG` is always used if specified.

    >>> with SetCwd(project_dir):
    ...     with Env({
    ...         "GUILD_CONFIG": other_guild_config,
    ...         "HOME": fake_home
    ...     }):
    ...         with SetGuildHome(project_gh):
    ...             pprint(config.user_config())
    {'remotes': {'foo': {'description': 'Remote defined in arbitrary location'}}}

Otherwise, the project config is used if it exists.

Guild first checks for `guild-config.yml`.

    >>> with SetCwd(project_dir):
    ...     with Env({"HOME": fake_home}):
    ...         with SetGuildHome(project_gh):
    ...             pprint(config.user_config())
    {'remotes': {'foo': {'description': 'Remote defined in project user config'}}}

If `guild-config.yml` doesn't exst, Guild looks for
`$GUILD_HOME/config.yml`. As of 0.9 and beyond, Guild uses the
project-local `.guild` subdirectory as `GUILD_HOME` by default.

Delete `guild-config.yml` - Guild uses `.guild/config.yml`.

    >>> rm(path(project_dir, "guild-config.yml"))

    >>> find(project_dir)
    .guild/config.yml

Check user config when `guild-config.yml` is missing.

    >>> with SetCwd(project_dir):
    ...     with Env({"HOME": fake_home}):
    ...         with SetGuildHome(project_gh):
    ...             pprint(config.user_config())
    {'remotes': {'bar': {'description': 'Remote defined in project user config '
                                        'v2'}}}

When `config.yml` doesn't exist under `GUILD_HOME`, Guild uses
`~/.guild/config.yml`. Here we redefine `HOME` to use the test config
created above.

    >>> empty_dir = mkdtemp()
    >>> with SetCwd(empty_dir):  # doctest: -WINDOWS
    ...     with Env({"HOME": fake_home}):
    ...         with SetGuildHome(empty_dir):
    ...             pprint(config.user_config())
    {'remotes': {'foo': {'description': 'Remote defined in default location'}}}

## User config inheritance

User config can use the `extends` construct to extend other config
sections.

The function `_apply_config_inherits` can be used with parsed user
config as a dict. We'll create a helper function to print the resolved
structure.

    >>> def apply(data):
    ...    config._apply_config_inherits(data, "test")
    ...    pprint(data)

NOTE: For the test below, we'll use the naming convention `sN` for
sections, `iN` for section items, and `aN` for item attributes.

A section item may extend other items in the same section.

    >>> apply({
    ...   "s1": {"i1": {"a1": 1, "a2": 2},
    ...          "i2": {"extends": "i1", "a2": 3}}
    ... })
    {'s1': {'i1': {'a1': 1, 'a2': 2},
            'i2': {'a1': 1, 'a2': 3}}}

It may also extend items under the `config` section.

    >>> apply({
    ...   "config": {"i1": {"a1": 1, "a2": 2}},
    ...   "s1": {"i2": {"extends": "i1", "a2": 3}}
    ... })
    {'s1': {'i2': {'a1': 1, 'a2': 3}}}

If the name occurs in both the current section and the `config`
section, the item under the current section is selected.

    >>> apply({
    ...   "config": {"i1": {"a1": 1, "a2": 2}},
    ...   "s1": {"i1": {"a1": 3, "a2": 4},
    ...          "i2": {"extends": "i1", "a2": 5}}
    ... })
    {'s1': {'i1': {'a1': 3, 'a2': 4},
            'i2': {'a1': 3, 'a2': 5}}}

Cycles are silently ignored by dropping the last leg of the cycle.

    >>> apply({
    ...   "s1": {"i1": {"extends": "i1"}}
    ... })
    {'s1': {'i1': {}}}

    >>> apply({
    ...   "s1": {"i1": {"extends": "i2", "a1": 1, "a2": 2},
    ...          "i2": {"extends": "i1", "a2": 3, "a3": 4}}
    ... })
    {'s1': {'i1': {'a1': 1, 'a2': 2, 'a3': 4},
            'i2': {'a1': 1, 'a2': 3, 'a3': 4}}}

    >>> apply({
    ...   "config": {"i1": {"extends": "i2", "a1": 1, "a2": 2},
    ...              "i2": {"extends": "i3", "a1": 3, "a3": 4},
    ...              "i3": {"extends": "i1", "a1": 5}},
    ...   "s1": {"i4": {"extends": "i1", "a1": 6, "a4": 7},
    ...          "i5": {"extends": "i2", "a2": 8, "a5": 9}}
    ... })
    {'s1': {'i4': {'a1': 6, 'a2': 2, 'a3': 4, 'a4': 7},
            'i5': {'a1': 3, 'a2': 8, 'a3': 4, 'a5': 9}}}

If a parent can't be found, `config.ConfigError` is raised.

    >>> apply({
    ...   "s1": {"i1": {"extends": "i2"}}
    ... })
    Traceback (most recent call last):
    ConfigError: cannot find 'i2' in test

## _Config objects

The class `config._Config` can be used to read config data.

    >>> cfg = config._Config(sample("config/remotes.yml"))
    >>> pprint(cfg.read())
    {'remotes': {'v100': {'ami': 'ami-4f62582a',
                          'description': 'V100 GPU running on EC2',
                          'init': 'echo hello',
                          'instance-type': 'p3.2xlarge',
                          'region': 'us-east-2',
                          'type': 'ec2'},
                 'v100x8': {'ami': 'ami-4f62582a',
                            'description': 'V100 x8 running on EC2',
                            'init': 'echo hello there',
                            'instance-type': 'p3.16xlarge',
                            'region': 'us-east-2',
                            'type': 'ec2'}}}

## Python Executable

When running a Python program on behalf of a user (as opposed to
running a Python program to implement an internal Guild task, usually
to provide process isolation), the Python interpreter is provide by
`config.python_exe()`.

The logic used to select the appropriate Python interpreter is as
follows:

- Use `GUILD_PYTHON_EXE` env var if defined
- If the current process is run in an activate virtual environment use
  `which python` (i.e. `python` available on the path)
- Use `sys.executable`

We use `which python` only when a virtual environment is activated
because that's a signal of user intent, which is to run Python
programs in that environment. We assume - we do not verify - that the
path is configured to run the environment-specific Python VM.

If a virtual environment is not activated, we do not assume `which
python`, which could yield an undesireable system Python VM. Rather,
we assume the VM used to run Guild itself.

To summarize, we use any explicitly defined VM (via
`GUILD_PYTHON_EXE`) because that's what the user wants by
definition. Otherwise we look to for a signal that the user has
deliberately configured `PATH` to include the desired Python VM. For
this we use the heuristic of an activated Python environment. If we
have no indicator that `PATH` is explicitly configured with a Python
VM, we fall back on the current Python VM - i.e. `sys.executabe`.

Without any environment the Python exe is the same as
`sys.exectuable`.

    >>> with Env({}, replace=True):
    ...     exe = config.python_exe()

    >>> exe == sys.executable, (exe, sys.executable)
    (True, ...)

We infer an activated virtual environment when either `VIRTUAL_ENV` or
`CONDA_PREFIX` is defined and points to a Python VM. This is done by
checking for `$PREFIX/bin/python`. In this case we use `which python`,
which is determined by `PATH` and an available Python executable.

Note that `which python` may not yield the Python VM installed for the
virtual environment. This is intentional. We assume simply that `PATH`
is intentionally configured by the user in this case and use the VM
provided by `which python` without further checks.

A non-empty `VIRTUAL_ENV` or `CONDA_PREFIX` env var does not imply an
activated virtual environment. These variables must also point to a
Python executable.

Provide a `python` executable under a temp directory. This will serve
as our Python executable via `which python`.

    >>> python_bindir = mkdtemp()
    >>> touch(path(python_bindir, "python"))
    >>> make_executable(path(python_bindir, "python"))

Create a new path that includes `python_bindir`.

    >>> python_bindir_path = (
    ...     python_bindir +
    ...     os.path.pathsep +
    ...     os.getenv("PATH")
    ... )

Create directories for the two virtual env types supported.

    >>> virtual_env_prefix = mkdtemp()
    >>> conda_prefix = mkdtemp()

Note that neither of these directories contain `bin/python` files and
there will NOT imply activated environments when provided as env
values.

Check `VIRTUAL_ENV`:

    >>> with Env({"VIRTUAL_ENV": virtual_env_prefix,
    ...           "PATH": python_bindir_path},
    ...          replace=True):
    ...     exe = config.python_exe()

    >>> exe == sys.executable, (exe, sys.executable)
    (True, ...)

Check `CONDA_PREFIX`:

    >>> with Env({"CONDA_PREFIX": conda_prefix,
    ...           "PATH": python_bindir_path},
    ...          replace=True):
    ...     exe = config.python_exe()

    >>> exe == sys.executable, (exe, sys.executable)
    (True, ...)

Create `bin/python` for the two virtual env prefix dirs.

For `VIRTUAL_ENV`:

    >>> mkdir(path(virtual_env_prefix, "bin"))
    >>> touch(path(virtual_env_prefix, "bin", "python"))

For `CONDA_PREFIX`:

    >>> mkdir(path(conda_prefix, "bin"))
    >>> touch(path(conda_prefix, "bin", "python"))

Confirm that `which python` with the appropriately configured `PATH`
var yields what we expect.

    >>> with Env({"PATH": python_bindir_path}, replace=True):
    ...     exe = which("python")

    >>> exe == path(python_bindir, "python"), (exe, python_bindir)
    (True, ...)

Check `config.python_exe()` with virtual env prefixes set.

    >>> with Env({"VIRTUAL_ENV": virtual_env_prefix,
    ...           "PATH": python_bindir_path}, replace=True):
    ...     exe = config.python_exe()

    >>> exe == path(python_bindir, "python"), (exe, python_bindir)
    (True, ...)

    >>> with Env({"CONDA_PREFIX": virtual_env_prefix,
    ...           "PATH": python_bindir_path}, replace=True):
    ...     exe = config.python_exe()

    >>> exe == path(python_bindir, "python"), (exe, python_bindir)
    (True, ...)

If `GUILD_PYTHON_EXE` is defined, it is always used regardless of
other environment variables.

    >>> guild_python_exe = path(mkdtemp(), "guild-exe")

    >>> with Env({"GUILD_PYTHON_EXE": guild_python_exe,
    ...           "CONDA_PREFIX": conda_prefix,
    ...           "VIRTUAL_ENV": virtual_env_prefix,
    ...           "PATH": python_bindir_path}, replace=True):
    ...     exe = config.python_exe()

    >>> exe == guild_python_exe, (exe, guild_python_exe)
    (True, ...)
