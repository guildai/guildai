# Guild init

Guild environments are initialized using the `init` command. The
implementation is currently in `guild.commands.init_impl`. This test
illustrates how init works by viewing the init command preview prompt.

    >>> from guild.commands import init_impl

For this test we'll use the `init-env` project.

    >>> project_dir = sample("projects/init-env")

We'll work with the internals of `init_impl` to generate the prompt
parameters for the init command.

Here's a helper function to generate a Config object.

    >>> def config(**kw):
    ...   from guild import config as configlib
    ...   from guild import click_util
    ...   arg_kw = dict(
    ...     dir=join_path(project_dir, "venv"),
    ...     name=None,
    ...     python=None,
    ...     guild=None,
    ...     guild_home=None,
    ...     system_site_packages=False,
    ...     no_isolate=False,
    ...     no_reqs=False,
    ...     path=(),
    ...     requirement=(),
    ...     tensorflow=None,
    ...     skip_tensorflow=False,
    ...     isolate_resources=False,
    ...     no_progress=False)
    ...   arg_kw.update(kw)
    ...   args = click_util.Args(**arg_kw)
    ...   with configlib.SetCwd(project_dir):
    ...     return init_impl.Config(args)

Here's the default prompt, assuming we're creating the environment
within the project directory:

    >>> pprint(config().prompt_params)
    [('Location', '.../samples/projects/init-env/venv'),
     ('Name', 'init-env'),
     ('Python interpreter', 'default'),
     ('Use system site packages', 'no'),
     ('Guild', '...'),
     ('Guild package requirements',
      ('Pillow',
       'pkg-a',
       'pkg-b',
       'tensorflow...')),
     ('Resource cache', 'shared')]

## Requires Guild packages

Guild init attempts to install package requirements. It will traverse
required Guild packages to find non Guild packages to install provided
the user provides package locations using `-p, --path` options.

In the case above, we didn't provide the location of the `pkg-a` and
`pkg-b`, so the prompt shows that these will be installed.

If we specify the location of these packages, init will read any Guild
files in those packages and install those. The rationale for this
behavior is that if the package can be found on one of the paths
specified by `--path` it should not be installed as it will be
available on the Python path configured for the environment.

Here's the preview when we specify the location of `pkg-a` and `pkg-b`
using a `--path` option.

    >>> pprint(config(path=(project_dir,)).prompt_params)
    [('Location', '.../samples/projects/init-env/venv'),
     ('Name', 'init-env'),
     ('Python interpreter', 'default'),
     ('Use system site packages', 'no'),
     ('Guild', '...'),
     ('Guild package requirements',
      ('Pillow',
       'lxml',
       'matplotlib',
       'numpy',
       'tensorflow...')),
     ('Additional paths', ('.../samples/projects/init-env',)),
     ('Resource cache', 'shared')]

Note that there are cycles in the Guild package requirements in the
sample project: `pkg-a` requires `pkg-b` and vise-versa. Guild init
stop traversing package requirements if it's already processed a Guild
file.

## Guild home

The `--guild-home` can be used to explicitly set the location of Guild
home.

    >>> pprint(config(guild_home="foo").prompt_params)
    [('Location', '...'),
     ('Name', 'init-env'),
     ('Python interpreter', 'default'),
     ('Use system site packages', 'no'),
     ('Guild', '...'),
     ('Guild home', 'foo'),
     ('Guild package requirements',
      ('Pillow', 'pkg-a', 'pkg-b', 'tensorflow-any')),
     ('Resource cache', 'shared')]

If `--no-isolate` is specified, the current Guild home path is used.

    >>> from guild import config as configlib
    >>> gh = configlib.guild_home()

    >>> params = config(no_isolate=True).prompt_params
    >>> dict(params).get("Guild home") == gh, (params, gh)
    (True, ...)

However, `guild_home` if specified overrides this value.

    >>> params = config(no_isolate=True, guild_home="bar").prompt_params
    >>> dict(params).get("Guild home")
    'bar'

## Using init

The module `guild.init` is used to perform initialization.

    >>> from guild import init

### Init Guild env

Use `init_env` to initialize a Guild environment.

Our target directory:

    >>> env_dir = mkdtemp()

Initialize an env:

    >>> init.init_env(env_dir)

The generated files:

    >>> find(env_dir, includedirs=True)
    .guild
    .guild/.guild-nocopy
    .guild/cache
    .guild/cache/resources
    .guild/cache/runs
    .guild/runs
    .guild/trash

If we specify `guild_home`, we get a link to that directory instead.

Build a sample directory to link to:

    >>> guild_home = mkdtemp()
    >>> touch(path(guild_home, "foo"))
    >>> touch(path(guild_home, "bar"))
    >>> mkdir(path(guild_home, "baz"))
    >>> touch(path(guild_home, "baz", "bam"))

Target env directory:

    >>> env_dir = mkdtemp()

Initialize the environment specifying the target Guild home.

    >>> init.init_env(env_dir, guild_home=guild_home)

The directory structure is simply a link to the target Guild home.

    >>> find(env_dir)
    .guild

    >>> real_guild_dir = realpath(path(env_dir, ".guild"))
    >>> real_guild_dir == guild_home, (real_guild_dir, guild_home)
    (True, ...)

Follow the link to the target:

    >>> find(env_dir, includedirs=True, followlinks=True)
    .guild
    .guild/bar
    .guild/baz
    .guild/baz/bam
    .guild/foo

### Write permission

    >>> env_path = mkdtemp()

Set path to read only.

    >>> import stat
    >>> os.chmod(env_path, stat.S_IREAD)

Attempt to initialize the read only location (skip on Windows as the
above does not prevent writes to the directory).

    >>> init.init_env(env_path)  # doctest: -WINDOWS
    Traceback (most recent call last):
    PermissionError: .../.guild
