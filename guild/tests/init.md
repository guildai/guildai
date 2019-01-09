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
    ...     dir=join_path(project_dir, "env"),
    ...     name=None,
    ...     python=None,
    ...     guild=None,
    ...     no_reqs=False,
    ...     path=(),
    ...     requirement=(),
    ...     tensorflow=None,
    ...     local_resource_cache=False,
    ...     no_progress=False)
    ...   arg_kw.update(kw)
    ...   args = click_util.Args(**arg_kw)
    ...   with configlib.SetCwd(project_dir):
    ...     return init_impl.Config(args)

Here's the default prompt, assuming we're creating the environment
within the project directory:

    >>> config().prompt_params
    [('Location', '.../samples/projects/init-env/env'),
     ('Name', 'init-env'),
     ('Python interpreter', 'default'),
     ('Guild version', '...'),
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

    >>> config(path=(project_dir,)).prompt_params
    [('Location', '.../samples/projects/init-env/env'),
     ('Name', 'init-env'),
     ('Python interpreter', 'default'),
     ('Guild version', '...'),
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

## Specifying TensorFlow package

Note the sample project lists `tensorflow-any` as a requirement. This
is a special package name that Guild translates to either `tensorflow`
or `tensorflow-gpu` during init based on system GPU support. However,
the user may use the `--tensorflow` option to specify the requirement
to use for `tensorflow-any`.

Here's helper function that returns the TensorFlow requirements entry:

    >>> def tf_req(**kw):
    ...   params = config(**kw).prompt_params
    ...   assert len(params) == 7, params
    ...   assert params[4][0] == "Guild package requirements", params
    ...   assert len(params[4][1]) == 5, params
    ...   assert params[4][1][4].startswith("tensorflow"), params
    ...   return params[4][1][4]

Here's the default, without a user-defined paramter:

    >>> tf = tf_req(path=(project_dir,))
    >>> tf in ("tensorflow", "tensorflow-gpu"), tf
    (True, ...)

If we specify the `tensorflow` option:

    >>> tf_req(path=(project_dir,), tensorflow="tensorflow-gpu>=1.20")
    'tensorflow-gpu>=1.20'
