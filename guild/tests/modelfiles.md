# Model files

Model files are files that contain model definitions. By convention
model files are named `MODEL` or `MODELS`.

Support for model files is provided by the `modelfile` module:

    >>> from guild import modelfile

## Loading a model file from a directory

Use `from_dir` to load a model file from a directory:

    >>> models = modelfile.from_dir(sample("projects/mnist"))
    >>> models.src
    '.../samples/projects/mnist/MODELS'

## Loading projects from a file

Use `from_file` to load a project from a file directly:

    >>> project = modelfile.from_file(sample("projects/mnist/MODELS"))
    >>> [model.name for model in project]
    ['mnist-intro', 'mnist-expert']

## Project models

By definition projects are lists of models:

    >>> list(project)
    [<guild.modelfile.Model 'mnist-intro'>,
     <guild.modelfile.Model 'mnist-expert'>]

    >>> [m.name for m in project]
    ['mnist-intro', 'mnist-expert']

We can lookup a model by name using dictionary semantics:

    >>> project["mnist-intro"]
    <guild.modelfile.Model 'mnist-intro'>

    >>> project.get("mnist-intro")
    <guild.modelfile.Model 'mnist-intro'>

The first model defined in a project is considered to be the *default
model*:

    >>> project.default_model()
    <guild.modelfile.Model 'mnist-intro'>

## Model attributes

We'll use the 'expert' model for these examples:

    >>> model = project["mnist-expert"]

    >>> model.name
    'mnist-expert'

    >>> model.version
    '0.1.0'

    >>> model.description
    'Sample model'

    >>> model.modelfile == project
    True

## Model operations

We'll use the 'intro' model for these examples:

    >>> model = project["mnist-intro"]

Operations are ordered by name:

    >>> [op.name for op in model.operations]
    ['evaluate', 'train']

Find an operation using a model's `get_op` method:

    >>> model.get_op("train")
    <guild.modelfile.Operation 'mnist-intro:train'>

`get_op` returns None if the operation isn't defined for the model:

    >>> print(model.get_op("not-defined"))
    None

## Errors

### Invalid format

    >>> modelfile.from_dir(sample("projects/invalid-format"))
    Traceback (most recent call last):
    ModelfileFormatError: ...

### No models (i.e. MODEL or MODELS)

    >>> modelfile.from_dir(sample("projects/missing-sources"))
    Traceback (most recent call last):
    NoModels: ...

A file not found error is Python version specific (FileNotFoundError
in Python 3 and IOError in Python 2) so we'll assert using exception
content.

    >>> try:
    ...   modelfile.from_file(sample("projects/missing-sources/MODEL"))
    ... except IOError as e:
    ...   print(str(e))
    [Errno 2] No such file or directory: '.../projects/missing-sources/MODEL'
