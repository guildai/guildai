# Model files

Model files are files that contain model definitions. By convention
model files are named `MODEL` or `MODELS`.

Support for model files is provided by the `modelfile` module:

    >>> from guild import modelfile

## Loading a model file from a directory

Use `from_dir` to load a model file from a directory:

    >>> mf = modelfile.from_dir(sample("projects/mnist"))
    >>> mf.src
    '.../samples/projects/mnist/MODELS'

## Loading a modelfile from a file

Use `from_file` to load a modelfile from a file directly:

    >>> mf = modelfile.from_file(sample("projects/mnist/MODELS"))
    >>> [model.name for model in mf]
    ['mnist-intro', 'mnist-expert', 'common']

## Model defs

By definition a modelfile is a list of modeldefs ("models" in this
context):

    >>> list(mf)
    [<guild.modelfile.ModelDef 'mnist-intro'>,
     <guild.modelfile.ModelDef 'mnist-expert'>,
     <guild.modelfile.ModelDef 'common'>]

### Accessing modeldefs

We can lookup a modeld by name using dictionary semantics:

    >>> mf["mnist-intro"]
    <guild.modelfile.ModelDef 'mnist-intro'>

    >>> mf.get("mnist-intro")
    <guild.modelfile.ModelDef 'mnist-intro'>

### Default model

The first model defined in a project is considered to be the default
model:

    >>> mf.default_model
    <guild.modelfile.ModelDef 'mnist-intro'>

### Attributes

The model name is used to identify the model:

    >>> mf["mnist-expert"].name
    'mnist-expert'

    >>> mf["mnist-intro"].name
    'mnist-intro'

The description provides additional details:

    >>> mf["mnist-expert"].description
    'Sample model'

Models support visibility. By default model visibility is
"public". Models that have a visibility of "private" are not displayed
in lists. The two `mnist` models are public (default visibility):

    >>> mf["mnist-expert"].visibility
    'public'

    >>> mf["mnist-intro"].visibility
    'public'

The `common` model, which is used to define flags that are common to
both `mnist` models, is designated as private:

    >>> mf["common"].visibility
    'private'

### Flags

Flags are named values that are provided to operations during a
run. Flags can be defined at the model level and at the operation
level.

Our sample modelfile uses an advanced scheme of including flag
definitions from one model into another model. Refer to
[samples/projects/mnist/MODELS](samples/projects/mnist/MODELS) for
details on how this is structured.

We'll use a helper function to print the flagdefs:

    >>> def print_flagdefs(flags):
    ...   for flag in flags:
    ...     print("%s: %s (default %r)"
    ...           % (flag.name, flag.description, flag.value))

Let's look at the flags defined for the `common` model, which is a
private modeldef that the two `mnist` models reference.

    >>> print_flagdefs(mf["common"].flags)
    batch-size: Number of images per batch (default 100)
    epochs: Number of epochs to train (default 5)

Flag *values* are distinct from flag *definitions*. The value
associated with a flag definition is used as the initial flag
value. We can read the flag values using `get_flag_value`:

    >>> mf["common"].get_flag_value("batch-size")
    100

    >>> mf["common"].get_flag_value("epochs")
    5

These values can be modified without effecting the flag definitions.

    >>> mf["common"].set_flag_value("epochs", 3)
    >>> mf["common"].get_flag_value("epochs")
    3
    >>> mf["common"].get_flagdef("epochs").value
    5

The `mnist-expert` model has the following `flags` spec:

    flags: common

This is short-hand for:

    flags:
      $include: common

This indicates that the flag definitions for the `common` model should
be included in the referencing model.

Here are the flag defs for `mnist-expert`:

    >>> print_flagdefs(mf["mnist-expert"].flags)
    batch-size: Number of images per batch (default 100)
    epochs: Number of epochs to train (default 5)

In this case the `mnist-expert` model included all of the `common`
flag definitions without redefining any.

The `mnist-intro` model also includes `common` flags, redefines the
value of one and adds another. Here's the flags spec for that model:

    flags:
      $include: common
      epochs: 10
      learning-rate:
        value: 0.001
        description: Learning rate for training

And the corresponding flag defs:

    >>> print_flagdefs(mf["mnist-intro"].flags)
    batch-size: Number of images per batch (default 100)
    epochs: Number of epochs to train (default 10)
    learning-rate: Learning rate for training (default 0.001)

Note that while the value for `epochs` is redefined, the original flag
description is not.

The third set of flags defined in the modelfile is associated with the
`evaluate` operation of the `intro` model.

    >>> eval_op = mf["mnist-intro"].get_op("evaluate")
    >>> print_flagdefs(eval_op.flags)
    batch-size: None (default 50000)
    epochs: None (default 1)

In this case the operation did not include flagdefs and did not
provide descriptions for its flags, so those are none.

Returning to flag values, operations inherit the values of flags
defined in their host models. We can use `all_flag_values` to retrieve
all of the flag values associated with a model or op definition.

Flag values for `mnist-intro` model:

    >>> pprint(mf["mnist-intro"].flag_values())
    {'batch-size': 100, 'epochs': 10, 'learning-rate': 0.001}

Flag values for `evaluate` op of `mnist-intro` model:

    >>> pprint(mf["mnist-intro"].get_op("evaluate").flag_values())
    {'batch-size': 50000, 'epochs': 1, 'learning-rate': 0.001}

Flag values for `mnist-expert` model:

    >>> pprint(mf["mnist-expert"].flag_values())
    {'batch-size': 100, 'epochs': 5}

Flag values for `train` op of `mnist-expert` model:

    >>> pprint(mf["mnist-expert"].get_op("train").flag_values())
    {'batch-size': 100, 'epochs': 5}

If we set the value of a flag defined on a model that is not defined
by the model's operation, the operation inherits that value:

    >>> mf["mnist-intro"].set_flag_value("learning-rate", 0.002)
    >>> pprint(mf["mnist-intro"].get_op("evaluate").flag_values())
    {'batch-size': 50000, 'epochs': 1, 'learning-rate': 0.002}

However, if the operation defines a flag value, setting the value on
the operation's model doesn't modify the operation's flag value:

    >>> mf["mnist-intro"].set_flag_value("epochs", 4)
    >>> pprint(mf["mnist-intro"].get_op("evaluate").flag_values())
    {'batch-size': 50000, 'epochs': 1, 'learning-rate': 0.002}

### Operations

Operations are ordered by name:

    >>> [op.name for op in mf["mnist-expert"].operations]
    ['evaluate', 'train']

Find an operation using a model's `get_op` method:

    >>> mf["mnist-expert"].get_op("train")
    <guild.modelfile.OpDef 'mnist-expert:train'>

`get_op` returns None if the operation isn't defined for the model:

    >>> print(mf["mnist-expert"].get_op("not-defined"))
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
