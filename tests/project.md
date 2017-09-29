# Projects

Support for Guild projects is provided by the `project` module:

    >>> import guild.project

## Loading projects from a directory

Use `from_dir` to load a project from a directory:

    >>> project = guild.project.from_dir(sample("projects/mnist"))
    >>> project.src
    '.../samples/projects/mnist/MODELS'

## Loading projects from a file

Use `from_file` to load a project from a file directly:

    >>> project = guild.project.from_file(sample("projects/mnist/MODELS"))
    >>> [model.name for model in project]
    ['mnist-intro', 'mnist-expert']

## Project models

By definition projects are lists of models:

    >>> list(project)
    [<guild.project.Model 'mnist-intro'>,
     <guild.project.Model 'mnist-expert'>]

    >>> [m.name for m in project]
    ['mnist-intro', 'mnist-expert']

We can lookup a model by name using dictionary semantics:

    >>> project["mnist-intro"]
    <guild.project.Model 'mnist-intro'>

    >>> project.get("mnist-intro")
    <guild.project.Model 'mnist-intro'>

The first model defined in a project is considered to be the *default
model*:

    >>> project.default_model()
    <guild.project.Model 'mnist-intro'>

## Model attributes

We'll use the 'expert' model for these examples:

    >>> model = project["mnist-expert"]

    >>> model.name
    'mnist-expert'

    >>> model.version
    '0.1.0'

    >>> model.description
    'Sample model'

    >>> model.project == project
    True

## Model operations

We'll use the 'intro' model for these examples:

    >>> model = project["mnist-intro"]

Operations are ordered by name:

    >>> [op.name for op in model.operations]
    ['evaluate', 'train']

Find an operation using a model's `get_op` method:

    >>> model.get_op("train")
    <guild.project.Operation 'mnist-intro:train'>

`get_op` returns None if the operation isn't defined for the model:

    >>> print(model.get_op("not-defined"))
    None

## Errors

### Invalid format

    >>> guild.project.from_dir(sample("projects/invalid-format"))
    Traceback (most recent call last):
    ProjectFormatError: ...

### No sources (i.e. MODEL or MODELS)

    >>> guild.project.from_dir(sample("projects/missing-sources"))
    Traceback (most recent call last):
    MissingSourceError: ...

    >>> guild.project.from_file(sample("projects/missing-sources/MODEL"))
    Traceback (most recent call last):
    IOError: ...
