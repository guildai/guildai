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
    ['intro', 'expert', 'common']

## Model defs

By definition a modelfile is a list of modeldefs ("models" in this
context):

    >>> list(mf)
    [<guild.modelfile.ModelDef 'intro'>,
     <guild.modelfile.ModelDef 'expert'>,
     <guild.modelfile.ModelDef 'common'>]

### Accessing modeldefs

We can lookup a modeld by name using dictionary semantics:

    >>> mf["intro"]
    <guild.modelfile.ModelDef 'intro'>

    >>> mf.get("intro")
    <guild.modelfile.ModelDef 'intro'>

### Default model

The first model defined in a project is considered to be the default
model:

    >>> mf.default_model
    <guild.modelfile.ModelDef 'intro'>

### Attributes

The model name is used to identify the model:

    >>> mf["expert"].name
    'expert'

    >>> mf["intro"].name
    'intro'

The description provides additional details:

    >>> mf["expert"].description
    'Sample model'

Models support visibility. By default model visibility is
"public". Models that have a visibility of "private" are not displayed
in lists. The two `mnist` models are public (default visibility):

    >>> mf["expert"].visibility
    'public'

    >>> mf["intro"].visibility
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

    >>> def flagdefs(flags):
    ...   return [
    ...     (flag.name, flag.description, flag.value)
    ...     for flag in flags]

Let's look at the flags defined for the `common` model, which is a
private modeldef that the two `mnist` models reference.

    >>> flagdefs(mf["common"].flags)
    [('batch-size', 'Number of images per batch', 100),
     ('epochs', 'Number of epochs to train', 5)]

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

The `expert` model has the following `flags` spec:

    flags: common

This is short-hand for:

    flags:
      $include: common

This indicates that the flag definitions for the `common` model should
be included in the referencing model.

Here are the flag defs for `expert`:

    >>> flagdefs(mf["expert"].flags)
    [('batch-size', 'Number of images per batch', 100),
     ('epochs', 'Number of epochs to train', 5)]

In this case the `expert` model included all of the `common`
flag definitions without redefining any.

The `intro` model also includes `common` flags but redefines the value
of one flag and adds another:

    >>> flagdefs(mf["intro"].flags)
    [('batch-size', 'Number of images per batch', 100),
     ('epochs', 'Number of epochs to train', 10),
     ('learning-rate', 'Learning rate for training', 0.001)]

Note that while the value for `epochs` is redefined, the original flag
description is not.

The third set of flags defined in the modelfile is associated with the
`evaluate` operation of the `intro` model.

    >>> eval_op = mf["intro"].get_operation("evaluate")
    >>> flagdefs(eval_op.flags)
    [('batch-size', '', 50000),
     ('epochs', '', 1)]

In this case the operation did not include flagdefs and did not
provide descriptions for its flags, so those are none.

Returning to flag values, operations inherit the values of flags
defined in their host models. We can use `all_flag_values` to retrieve
all of the flag values associated with a model or op definition.

Flag values for `intro` model:

    >>> pprint(mf["intro"].flag_values())
    {'batch-size': 100, 'epochs': 10, 'learning-rate': 0.001}

Flag values for `evaluate` op of `intro` model:

    >>> pprint(mf["intro"].get_operation("evaluate").flag_values())
    {'batch-size': 50000, 'epochs': 1, 'learning-rate': 0.001}

Flag values for `expert` model:

    >>> pprint(mf["expert"].flag_values())
    {'batch-size': 100, 'epochs': 5}

Flag values for `train` op of `expert` model:

    >>> pprint(mf["expert"].get_operation("train").flag_values())
    {'batch-size': 100, 'epochs': 5}

If we set the value of a flag defined on a model that is not defined
by the model's operation, the operation inherits that value:

    >>> mf["intro"].set_flag_value("learning-rate", 0.002)
    >>> pprint(mf["intro"].get_operation("evaluate").flag_values())
    {'batch-size': 50000, 'epochs': 1, 'learning-rate': 0.002}

However, if the operation defines a flag value, setting the value on
the operation's model doesn't modify the operation's flag value:

    >>> mf["intro"].set_flag_value("epochs", 4)
    >>> pprint(mf["intro"].get_operation("evaluate").flag_values())
    {'batch-size': 50000, 'epochs': 1, 'learning-rate': 0.002}

### Operations

Operations are ordered by name:

    >>> [op.name for op in mf["expert"].operations]
    ['evaluate', 'train']

Find an operation using a model's `get_op` method:

    >>> mf["expert"].get_operation("train")
    <guild.modelfile.OpDef 'expert:train'>

`get_op` returns None if the operation isn't defined for the model:

    >>> print(mf["expert"].get_operation("not-defined"))
    None

## Resources

Model resources are are named lists of sources that may be required by
operations. Our sample models each have the following resources:

    >>> mf["common"].resources
    [<guild.modelfile.ResourceDef 'data'>]

    >>> mf["expert"].resources
    []

    >>> mf["intro"].resources
    []

In the same way that models can include flag definitions from other
models, they can include resources. In our example, both the `intro`
and `expert` models include resources from the `common` model.

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
