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

We can iterate through all available models using `iter_models1`:

    >>> sorted(guild.model.iter_models())
    [('mnist', <guild.model.Model object ...>),
     ('mnist-expert', <guild.model.Model object ...>),
     ('mnist-intro', <guild.model.Model object ...>)]
