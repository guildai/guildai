# Models

Models play a central role in Guild commands. Models define the
operations that are performed by the `run` command. They are a
resource that can be discovered.

Models are managed using the `guild.model` module:

    >>> import guild.model

Models are dicovered along a model path, which is identical in concept
to the Python path. Models are advertised within the path using Python
distribution entry points under the "guild.models"
group. Additionally, model source directories may be placed on the
path to make models in that directory discoverable.

We can view the current model path using the `path` function:

    >>> guild.model.get_path()
    [...]

By default, this path is identical to the Python path
(i.e. `sys.path`). We can modify the model path in two ways:

- Adding a guildfile path
- Setting the entire path explicitly

Let's modify the model path by adding a sample model path:

    >>> guild.model.insert_path(sample("projects/mnist-pkg"))

This has the effect of inserting the project location at the beginning
of the model path:

    >>> guild.model.get_path()
    ['.../samples/projects/mnist-pkg', ...]

We can alternatively set the entire model path using `set_path`. We'll
include both our sample MNIST project as well as the sample models
defined in `packages`.

    >>> guild.model.set_path([
    ...   sample("projects/mnist-pkg"),
    ...   sample("packages")])

Here's our new path:

    >>> guild.model.get_path()
    ['.../samples/projects/mnist-pkg',
     '.../samples/packages']

## Iterating models

We can iterate through all available models using `iter_models`:

    >>> sorted(guild.model.iter_models(), key=lambda m: m.name)
    [<guild.model.GuildfileModel 'expert'>,
     <guild.model.GuildfileModel 'intro'>,
     <guild.model.PackageModel 'mnist-cnn'>,
     <guild.model.PackageModel 'mnist-softmax'>]

Note that models derived from guildfiles are distinguished from models
derived from packages.

## Models by name

We can lookup models matching a name:

    >>> list(guild.model.for_name("mnist-cnn"))
    [<guild.model.PackageModel 'mnist-cnn'>]

If there are no models matching `name` we get an error:

    >>> list(guild.model.for_name("other"))
    Traceback (most recent call last):
    LookupError: other

## Model distributions

Models are associated with the distributions in which they're
defined. Guild supports two types of distributions:

- Standard Python distributions as outlined in
  [Packaging and Distributing Projects]
  (https://packaging.python.org/tutorials/distributing-packages/)

- Guildfile distributions, which are based on guildfiles

The `mnist-cnn` model is defined in a standard Python distribution:

    >>> cnn = next(guild.model.for_name("mnist-cnn"))

    >>> cnn.dist.__class__
    <class 'pkg_resources.DistInfoDistribution'>

Here we see that the project name is `gpkg.dist` and the distribution
is located in the sample `packages` directory. Standard
distributions have versions as they were explicitly packaged using
`setuptools` (e.g. by way of the `guild package` command).

The `mnist-intro` model is defined in a guildfile:

    >>> intro = next(guild.model.for_name("intro"))

    >>> intro.dist.__class__
    <class 'guild.model.GuildfileDistribution'>

Guildfile distributions are not versioned and trying to read the
version will generate an error:

    >>> intro.dist.version
    Traceback (most recent call last):
    ValueError: ("Missing 'Version:' header and/or PKG-INFO file"...

Guildfile distribution project names start with '.guildfile.' to
distinguish them from standard distributions:

    >>> intro.dist.project_name[:11]
    '.guildfile.'

The part of the project name that follows the '.guildfile.' prefix is
an escaped relative directory that contains the model's
guildfile. This value can be unescaped using
`model._unescape_project_name`.

    >>> intro_pkg_path = guild.model.unescape_project_name(
    ...                    intro.dist.project_name[11:])
    >>> intro_pkg_path
    '.../samples/projects/mnist-pkg'

Guildfile distribution package paths always start with '.':

    >>> intro_pkg_path[0]
    '.'

## Model names

Models have names, which must correspond to the names in their
associated model definition.

    >>> intro.name == intro.modeldef.name == "intro"
    True

    >>> cnn.name == cnn.modeldef.name == "mnist-cnn"
    True

Models also provide a `fullname` attribute that applies namespaces to
the model distribution project name:

Models from local guildfiles (i.e. not installed from standard Python
packages) are named with a starting '.' and a path leading to the
model name. Paths in these names are always relative to the current
working directory.

    >>> intro.fullname[0]
    '.'

    >>> intro.fullname
    '.../tests/samples/projects/mnist-pkg/intro'

Models from installed packages are named with their Guild package
names (i.e. after namespaces are applied) and do not start with a '.'.

    >>> cnn.fullname
    'gpkg.mnist/mnist-cnn'

## Model references

Models provide a `reference` that can be used to identify the
model. This is used by operation runs to tie a run back to its model.

References are in the form:

    PACKAGE_REF VERSION MODEL_NAME

Here's the reference for the `intro` model:

    >>> intro.reference
    ModelRef(dist_type='guildfile',
             dist_name='.../samples/projects/mnist-pkg/guild.yml',
             dist_version='...',
             model_name='intro')

Note that the package reference in this case is an absolute path to
the guildfile. The version is a hash (md5) of the guildfile. This
information can be used to locate the model definition and optionally
verify that it has not been modified since the reference was
generated.

Here's the reference for the `cnn` model:

    >>> cnn.reference
    ModelRef(dist_type='package',
             dist_name='gpkg.mnist',
             dist_version='0.1.0',
             model_name='mnist-cnn')

This is a model reference for a PyPI packaged model.

## Model definitions

Models are associated with modeldefs that provide the details
associated with a model, including their operations. Modeldefs
implemented as YAML files that are on the model path

The `mnist-cnn` modeldef looks like this:

    >>> cnn_def = cnn.modeldef

    >>> cnn_def.name
    'mnist-cnn'

    >>> cnn_def.description
    'CNN classifier for MNIST'

    >>> [(op.name, op.description) for op in cnn_def.operations]
    [('train', 'Train the CNN')]

Here's the `intro` def:

    >>> intro_def = intro.modeldef

    >>> intro_def.name
    'intro'

    >>> intro_def.description
    ''

    >>> [(op.name, op.description) for op in intro_def.operations]
    [('evaluate', ''), ('train', '')]

Model definitions in turn are associated with the guildfiles they're
defined in.

    >>> cnn_def.guildfile.src
    '.../samples/packages/gpkg/mnist/guild.yml'

    >>> intro_def.guildfile.src
    '.../samples/projects/mnist-pkg/guild.yml'
