# Models

Models play a central role in Guild commands. Models define the
operations that are performed by the `run` command. They are a
resource that can be discovered.

Models are managed using the `guild.model` module:

    >>> import guild.model

Models are dicovered along a model path, which is identical in concept
to the Python path. Models are advertised within the path using Python
distribution entry points under the "guild.models"
group. Additionally, model source files may be placed directly on the
path to make those models discoverable.

We can view the current model path using the `path` function:

    >>> guild.model.path()
    [...]

By default, this path is identical to the Python path
(i.e. `sys.path`). We can modify the model path in two ways:

- Adding a project source
- Setting the entire path explicitly

Let's modify the model path by adding a sample model source:

    >>> guild.model.add_model_source(sample("projects/mnist/MODELS"))

This has the effect of inserting the project location at the beginning
of the model path:

    >>> guild.model.path()
    ['.../samples/projects/mnist/MODELS', ...]

We can alternatively set the entire model path explicitly using
`set_path`. We'll include both our sample MNIST project as well as the
sample models defined in `model-packages`.

    >>> guild.model.set_path([
    ...   sample("projects/mnist/MODELS"),
    ...   sample("model-packages")])

Here's our new path:

    >>> guild.model.path()
    ['.../samples/projects/mnist/MODELS',
     '.../samples/model-packages']

## Iterating models

We can iterate through all available models using `iter_models`:

    >>> sorted(guild.model.iter_models(), key=lambda m: m.name)
    [<guild.model.Model 'mnist-cnn'>,
     <guild.model.Model 'mnist-expert'>,
     <guild.model.Model 'mnist-intro'>,
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

    >>> cnn.dist
    gpkg.mnist 0.1.0 (.../samples/model-packages)

    >>> cnn.dist.__class__
    <class 'pkg_resources.DistInfoDistribution'>

Here we see that the project name is `gpkg.dist` and the distribution
is located in the sample `model-packages` directory. Standard
distributions have versions as they were explicitly packaged using
`setuptools` (e.g. by way of the `guild package` command).

The `mnist-intro` model is defined in a modelfile:

    >>> intro = next(guild.model.for_name("mnist-intro"))

    >>> intro.dist
    <guild.model.ModelfileDistribution '.../samples/projects/mnist/MODELS'>

Modelfile distributions are not versioned and trying to read the
version will generate an error:

    >>> intro.dist.version
    Traceback (most recent call last):
    ValueError: ("Missing 'Version:' header and/or PKG-INFO file"...

Modelfile distribution project names are always 'Unknown':

    >>> intro.dist.project_name
    'Unknown'

## Model defs

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

Here's the `mnist-intro` def:

    >>> intro_def = intro.modeldef

    >>> intro_def.name
    'mnist-intro'

    >>> print(intro_def.description)
    None

    >>> [(op.name, op.description) for op in intro_def.operations]
    [('evaluate', None), ('train', None)]
