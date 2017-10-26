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

    >>> guild.model.path()
    [...]

By default, this path is identical to the Python path
(i.e. `sys.path`). We can modify the model path in two ways:

- Adding a modelfile path
- Setting the entire path explicitly

Let's modify the model path by adding a sample model path:

    >>> guild.model.add_model_path(sample("projects/mnist"))

This has the effect of inserting the project location at the beginning
of the model path:

    >>> guild.model.path()
    ['.../samples/projects/mnist', ...]

We can alternatively set the entire model path using `set_path`. We'll
include both our sample MNIST project as well as the sample models
defined in `model-packages`.

    >>> guild.model.set_path([
    ...   sample("projects/mnist"),
    ...   sample("model-packages")])

Here's our new path:

    >>> guild.model.path()
    ['.../samples/projects/mnist',
     '.../samples/model-packages']

## Iterating models

We can iterate through all available models using `iter_models`:

    >>> sorted(guild.model.iter_models(), key=lambda m: m.name)
    [<guild.model.Model 'expert'>,
     <guild.model.Model 'intro'>,
     <guild.model.Model 'mnist-cnn'>,
     <guild.model.Model 'mnist-softmax'>]

## Models by name

We can lookup models matching a name:

    >>> list(guild.model.for_name("mnist-cnn"))
    [<guild.model.Model 'mnist-cnn'>]

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

- Modelfile distributions, which are based on modelfiles

The `mnist-cnn` model is defined in a standard Python distribution:

    >>> cnn = next(guild.model.for_name("mnist-cnn"))

    >>> cnn.dist.__class__
    <class 'pkg_resources.DistInfoDistribution'>

Here we see that the project name is `gpkg.dist` and the distribution
is located in the sample `model-packages` directory. Standard
distributions have versions as they were explicitly packaged using
`setuptools` (e.g. by way of the `guild package` command).

The `mnist-intro` model is defined in a modelfile:

    >>> intro = next(guild.model.for_name("intro"))

    >>> intro.dist.__class__
    <class 'guild.model.ModelfileDistribution'>

Modelfile distributions are not versioned and trying to read the
version will generate an error:

    >>> intro.dist.version
    Traceback (most recent call last):
    ValueError: ("Missing 'Version:' header and/or PKG-INFO file"...

Modelfile distribution project names start with '.modelfile.' to
distinguish them from standard distributions:

    >>> intro.dist.project_name[:11]
    '.modelfile.'

The part of the project name that follows the '.modelfile.' prefix is
an escaped relative directory that contains the model's
modelfile. This value can be unescaped using
`model._unescape_project_name`.

    >>> intro_pkg_path = guild.model._unescape_project_name(
    ...                    intro.dist.project_name[11:])
    >>> intro_pkg_path
    '.../samples/projects/mnist'

Modelfile distribution package paths always start with '.':

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

    >>> intro.fullname
    '.../samples/projects/mnist/intro'

Models from local modelfiles (i.e. not installed from standard Python
packages) are named with a starting '.' and a path leading to the
model name. Paths in these names are always relative to the current
working directory.

    >>> cnn.fullname
    'mnist/mnist-cnn'

Models from installed packages are named with their Guild package
names (i.e. after namespaces are applied) and do not start with a '.'.

## Model references

Models provide a `reference` that can be used to identify the
model. This is used by operation runs to tie a run back to its model.

References are in the form:

    PACKAGE_REF VERSION MODEL_NAME

Here's the reference for the `intro` model:

    >>> intro.reference
    'file:/.../samples/projects/mnist/MODELS ... intro'

Note that the package reference in this case is an absolute path to
the modelfile. The version is a hash (md5) of the modelfile. This
information can be used to locate the model definition and optionally
verify that it has not been modified since the reference was
generated.

Here's the reference for the `cnn` model:

    >>> cnn.reference
    'dist:gpkg.mnist 0.1.0 mnist-cnn'

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

Model definitions in turn are associated with the modelfiles they're
defined in.

    >>> cnn_def.modelfile.src
    '.../samples/model-packages/gpkg/mnist/MODELS'

    >>> intro_def.modelfile.src
    '.../samples/projects/mnist/MODELS'
