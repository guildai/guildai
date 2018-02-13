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

    >>> mf["expert"].private
    False

    >>> mf["intro"].private
    False

The `common` model, which is used to define flags that are common to
both `mnist` models, is designated as private:

    >>> mf["common"].private
    True

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
    ...     (flag.name, flag.description, flag.default)
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
    >>> mf["common"].get_flagdef("epochs").default
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

### Updating flags

Flags can be updated using flags from another flag host.

Consider this modelfile:

    >>> mf2 = modelfile.from_string("""
    ... name: sample
    ... operations:
    ...   a:
    ...     flags:
    ...       x: X1
    ...       y: Y
    ...   b:
    ...     flags:
    ...       x: x2
    ...       z: Z
    ... """)

The two opdefs:

    >>> opdef_a = mf2["sample"].get_operation("a")
    >>> opdef_b = mf2["sample"].get_operation("b")

Here are the flags and values for opdef a:

    >>> opdef_a.flags
    [<guild.modelfile.FlagDef 'x'>, <guild.modelfile.FlagDef 'y'>]

    >>> pprint(opdef_a.flag_values())
    {'x': 'X1', 'y': 'Y'}

And the flags and values for opdef b:

    >>> opdef_b.flags
    [<guild.modelfile.FlagDef 'x'>, <guild.modelfile.FlagDef 'z'>]

    >>> pprint(opdef_b.flag_values())
    {'x': 'x2', 'z': 'Z'}

We'll update opdef a flags with those from opdef b:

    >>> opdef_a.update_flags(opdef_b)

The updated flags:

    >>> opdef_a.flags
    [<guild.modelfile.FlagDef 'x'>,
     <guild.modelfile.FlagDef 'y'>,
     <guild.modelfile.FlagDef 'z'>]

and values:

    >>> pprint(opdef_a.flag_values())
    {'x': 'x2', 'y': 'Y', 'z': 'Z'}

## Operations

Operations are ordered by name:

    >>> [op.name for op in mf["expert"].operations]
    ['evaluate', 'train']

Find an operation using a model's `get_op` method:

    >>> mf["expert"].get_operation("train")
    <guild.modelfile.OpDef 'expert:train'>

`get_op` returns None if the operation isn't defined for the model:

    >>> print(mf["expert"].get_operation("not-defined"))
    None

### Plugin ops

An operation can delegate its implementation to a plugin using the
`plugin-op` attribute. Here's a sample modelfile:

    >>> mf2 = modelfile.from_string("""
    ... name: sample
    ... operations:
    ...   train:
    ...     plugin-op: foo-train
    ... """)

The opdef in this case will use `plugin_op` rather than `cmd`. Plugin
ops are provided as modelfile.PluginOp objects and have `name` and
`config` attributes:

    >>> train = mf2["sample"].get_operation("train")

    >>> train.plugin_op.name
    'foo-train'

    >>> train.plugin_op.config
    {}

Plugin ops may be configured by specifying them as objects with `name`
and additional config attributes:

    >>> mf2 = modelfile.from_string("""
    ... name: sample
    ... operations:
    ...   train:
    ...     plugin-op:
    ...       name: bar-train
    ...       config-1: bar
    ...       config-2: [1, 2, 3]
    ... """)

    >>> train = mf2["sample"].get_operation("train")

    >>> train.plugin_op.name
    'bar-train'

    >>> pprint(train.plugin_op.config)
    {'config-1': 'bar', 'config-2': [1, 2, 3]}

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

A resource source consists of a URI and other information that Guild
uses to fully resolve the source. URIs are specified indirectly using
one of three source type attributes:

- file
- url
- operation

Here's a model definition that contains various resource sources:

    >>> mf = modelfile.from_string("""
    ... name: sample
    ... resources:
    ...   sample:
    ...     sources:
    ...       - foo.txt
    ...       - file: bar.tar.gz
    ...       - url: https://files.com/bar.tar.gz
    ...       - operation: train/model.meta
    ... """)

Here are the associated resource sources:

    >>> mf["sample"].get_resource("sample").sources
    [<guild.resourcedef.ResourceSource 'file:foo.txt'>,
     <guild.resourcedef.ResourceSource 'file:bar.tar.gz'>,
     <guild.resourcedef.ResourceSource 'https://files.com/bar.tar.gz'>,
     <guild.resourcedef.ResourceSource 'operation:train/model.meta'>]

Note that when a source is specified as a string it is treated as a
file.

At least one of the three type attributes is required:

    >>> modelfile.from_string("""
    ... name: sample
    ... resources:
    ...   sample:
    ...     sources:
    ...       - foo: bar.txt
    ... """)
    Traceback (most recent call last):
    ResourceFormatError: invalid source {'foo': 'bar.txt'} in resource 'sample': missing
    required attribute (one of file, url, operation)

However, no more than one is allowed:

    >>> modelfile.from_string("""
    ... name: sample
    ... resources:
    ...   sample:
    ...     sources:
    ...       - file: foo.txt
    ...         url: http://files.com/bar.txt
    ... """)
    Traceback (most recent call last):
    ResourceFormatError: invalid source {'file': 'foo.txt', 'url': 'http://files.com/bar.txt'}
    in resource 'sample': conflicting attributes (file, url)

## References

A list of references may be included for each model. These can be used
to direct users to upstream sources and papers.

    >>> mf = modelfile.from_string("""
    ... name: sample
    ... references:
    ...   - https://arxiv.org/abs/1603.05027
    ...   - https://arxiv.org/abs/1512.03385
    ... """)
    >>> mf["sample"].references
    ['https://arxiv.org/abs/1603.05027', 'https://arxiv.org/abs/1512.03385']

## Includes

Guild model files support includes.

    >>> mf = modelfile.from_dir(sample("projects/includes"))
    >>> list(mf)
    [<guild.modelfile.ModelDef 'shared'>,
     <guild.modelfile.ModelDef 'model-a'>,
     <guild.modelfile.ModelDef 'model-b'>,
     <guild.modelfile.ModelDef 'model-c'>]

    >>> mf["model-a"].flags
    [<guild.modelfile.FlagDef 'model-a-flag-1'>,
     <guild.modelfile.FlagDef 'shared-1'>,
     <guild.modelfile.FlagDef 'shared-2'>]

    >>> mf["model-b"].flags
    [<guild.modelfile.FlagDef 'model-b-flag-1'>,
     <guild.modelfile.FlagDef 'model-b-flag-2'>,
     <guild.modelfile.FlagDef 'shared-1'>,
     <guild.modelfile.FlagDef 'shared-2'>]

    >>> mf["model-c"].flags
    [<guild.modelfile.FlagDef 'model-c-flag-1'>,
     <guild.modelfile.FlagDef 'model-c-flag-2'>]

## Model inheritance

### Data merging

Model inheritance works using a low level data merge facility
implemented by `modelfile._apply_parent_data`.

Here's a helper function to apply parent data and print the result:

    >>> def apply_parent(parent, child):
    ...     modelfile._apply_parent_data(parent, child)
    ...     pprint(child)

If a dict value doesn't exist in child, it's copied from parent:

    >>> apply_parent({"a": 1}, {})
    {'a': 1}

    >>> apply_parent({"a": 1, "b": 2}, {})
    {'a': 1, 'b': 2}

    >>> apply_parent({"a": 1, "b": [1, 2, 3]}, {})
    {'a': 1, 'b': [1, 2, 3]}

If a simple dict value exists (i.e. is not a dict or list), the value
is preserved:

    >>> apply_parent({}, {"a": 1})
    {'a': 1}

    >>> apply_parent({"a": 1}, {"a": 2})
    {'a': 2}

If a dict value exists, it is extended with the corresponding value in
child using the same rules:

    >>> apply_parent({"a": {"b": 1}}, {"a": {}})
    {'a': {'b': 1}}

    >>> apply_parent({"a": {"b": 2}}, {"a": {"b": 1}})
    {'a': {'b': 1}}

    >>> apply_parent({"a": {"b": 2, "c": 3}}, {"a": {"b": 1}})
    {'a': {'b': 1, 'c': 3}}

Lists not extended:

    >>> apply_parent([1, 2, 3], [])
    []

Empty cases:

    >>> apply_parent({}, {})
    {}
    >>> apply_parent([], [])
    []

Simple values:

    >>> apply_parent(1, 2)
    2
    >>> apply_parent([], 1)
    1
    >>> apply_parent({}, 1)
    1

The following is a complex example that illustrates a likely model
extension scenario.

    >>> parent = {
    ...   'name': 'base',
    ...   'description': 'Base model definition',
    ...   'operations': {
    ...     'evaluate': {
    ...       'cmd': 'eval',
    ...       'description': 'Evaluate a trained model',
    ...       'requires': ['model', 'data']
    ...     },
    ...     'train': {
    ...       'cmd': 'train',
    ...       'description': 'Train a model',
    ...       'flags': {
    ...         'batch-size': {
    ...           'default': 100,
    ...           'description': 'Batch size'
    ...         },
    ...         'epochs': {
    ...           'default': 10,
    ...           'description': 'Number of epochs to train'
    ...         }
    ...       },
    ...       'requires': 'data'
    ...     }
    ...   },
    ...   'resources': {
    ...     'model': {
    ...       'description': 'Exported intro model',
    ...       'sources': [{'operation': 'train', 'select': 'model'}]
    ...     }
    ...   }
    ... }

    >>> child = {
    ...   'name': 'model',
    ...   'description': 'My model',
    ...   'operations': {
    ...     'train': {
    ...       'flags': {
    ...         'batch-size': {
    ...           'default': 101
    ...         }
    ...       }
    ...     },
    ...     'evaluate': {
    ...       'cmd': 'train --test',
    ...     },
    ...     'prepare': {
    ...       'cmd': 'prepare'
    ...     }
    ...   }
    ... }

We'll extend the child in-place so we can test specific attributes
after it's extended.

    >>> modelfile._apply_parent_data(parent, child)

Name and description are both preserved:

    >>> child["name"]
    'model'

    >>> child["description"]
    'My model'

The `train` and `evaluate` operations of the base are now extended

    >>> sorted(child["operations"])
    ['evaluate', 'prepare', 'train']

    >>> pprint(child["operations"]["train"])
    {'cmd': 'train',
     'description': 'Train a model',
     'flags': {'batch-size': {'default': 101, 'description': 'Batch size'},
               'epochs': {'default': 10,
                          'description': 'Number of epochs to train'}},
     'requires': 'data'}

    >>> pprint(child["operations"]["evaluate"])
    {'cmd': 'train --test',
     'description': 'Evaluate a trained model',
     'requires': ['model', 'data']}

    >>> pprint(child["resources"])
    {'model': {'description': 'Exported intro model',
               'sources': [{'operation': 'train', 'select': 'model'}]}}

### Extending model defs

This facility is used to implement model inheritance. Models inherit
the attributes of parent models by listing parent models in an
`extends` attributes.

Here's a model file that defines a model that extends another:

    >>> mf = modelfile.from_string("""
    ... - name: trainable
    ...   description: A trainable model
    ...   private: yes
    ...   operations:
    ...     train:
    ...       cmd: train
    ...       flags:
    ...         batch-size: 32
    ...
    ... - name: model-1
    ...   extends: trainable
    ... """)

`model-1` inherits the operations of its parent `trainable`:

    >>> m1 = mf["model-1"]
    >>> m1.operations
    [<guild.modelfile.OpDef 'model-1:train'>]

It also inherits the description:

    >>> m1.description
    'A trainable model'

Models do not inherit name or private:

    >>> m1.name
    'model-1'

    >>> m1.private
    False

Here's a more complex example with two parent models and two child
models.

    >>> mf = modelfile.from_string("""
    ... - name: trainable
    ...   description: A trainable model
    ...   private: yes
    ...   operations:
    ...     train:
    ...       cmd: train
    ...       flags:
    ...         batch-size: 32
    ...
    ... - name: evaluatable
    ...   description: An evaluatable model
    ...   private: yes
    ...   operations:
    ...     evaluate:
    ...       cmd: train --test
    ...
    ... - name: model-1
    ...   description: A trainable, evaluatable model
    ...   extends: [trainable, evaluatable]
    ...
    ... - name: model-2
    ...   extends: trainable
    ...   operations:
    ...     train:
    ...       flags:
    ...         batch-size: 16
    ... """)

In this example, `model-1` extends two models and so inherits
attributes from both.

    >>> m1 = mf["model-1"]
    >>> m1.operations
    [<guild.modelfile.OpDef 'model-1:evaluate'>,
     <guild.modelfile.OpDef 'model-1:train'>]


It's other attributes:

    >>> m1.name
    'model-1'

    >>> m1.private
    False

    >>> m1.description
    'A trainable, evaluatable model'

As a point of comparison to `model-2` below, `model-1` inherits the
default for the `batch-size` attribute:

    >>> m1.get_operation("train").get_flagdef("batch-size").default
    32

`model-2` only extends one parent, but it modifies a flag default.

    >>> m2 = mf["model-2"]

    >>> m2.operations
    [<guild.modelfile.OpDef 'model-2:train'>]

    >>> m2.get_operation("train").get_flagdef("batch-size").default
    16

In this example, a model extends a model that in turn extends another
model:

    >>> mf = modelfile.from_string("""
    ... - name: a
    ...   operations:
    ...     train:
    ...       cmd: train
    ...       flags:
    ...         f1:
    ...           description: f1 in a
    ...           default: 1
    ...         f2:
    ...           description: f2 in a
    ...           default: 2
    ...         f3:
    ...           description: f3 in a
    ...           default: 3
    ... - name: b
    ...   extends: a
    ...   operations:
    ...     train:
    ...       flags:
    ...         f2:
    ...           description: f2 in b
    ...           default: 22
    ...     eval:
    ...       cmd: eval
    ... - name: c
    ...   extends: b
    ...   operations:
    ...     train:
    ...       flags:
    ...         f3:
    ...           description: f3 in c
    ...           default: 33
    ...     predict:
    ...       cmd: predict
    ... """)


Model `a`:

    >>> a = mf["a"]

    >>> a.operations
    [<guild.modelfile.OpDef 'a:train'>]

    >>> [(f.name, f.description, f.default)
    ...   for f in a.get_operation("train").flags]
    [('f1', 'f1 in a', 1), ('f2', 'f2 in a', 2), ('f3', 'f3 in a', 3)]

Model `b`:

    >>> b = mf["b"]

    >>> b.operations
    [<guild.modelfile.OpDef 'b:eval'>,
     <guild.modelfile.OpDef 'b:train'>]

    >>> [(f.name, f.description, f.default)
    ...   for f in b.get_operation("train").flags]
    [('f1', 'f1 in a', 1), ('f2', 'f2 in b', 22), ('f3', 'f3 in a', 3)]

Model `c`:

    >>> c = mf["c"]

    >>> c.operations
    [<guild.modelfile.OpDef 'c:eval'>,
     <guild.modelfile.OpDef 'c:predict'>,
     <guild.modelfile.OpDef 'c:train'>]

    >>> [(f.name, f.description, f.default)
    ...   for f in c.get_operation("train").flags]
    [('f1', 'f1 in a', 1), ('f2', 'f2 in b', 22), ('f3', 'f3 in c', 33)]

### Inheritance cycles

Below are some inheritance cycles:

    >>> modelfile.from_string("""
    ... - name: a
    ...   extends: a
    ... """)
    Traceback (most recent call last):
    ModelfileReferenceError: cycle in model extends: ['a']

    >>> modelfile.from_string("""
    ... - name: a
    ...   extends: b
    ... - name: b
    ...   extends: a
    ... """)
    Traceback (most recent call last):
    ModelfileReferenceError: cycle in model extends: ['b', 'a']

### Params

Params may be used in model parents to define place-holder for child
models. Here's s simple example:

    >>> mf = modelfile.from_string("""
    ... - name: base
    ...   description: A {{type}} classifier
    ...
    ... - name: softmax
    ...   extends: base
    ...   params:
    ...     type: softmax
    ...
    ... - name: cnn
    ...   extends: base
    ...   params:
    ...     type: CNN
    ... """)

Here are the description of each model:

    >>> mf["base"].description
    'A {{type}} classifier'

    >>> mf["softmax"].description
    'A softmax classifier'

    >>> mf["cnn"].description
    'A CNN classifier'

Here's an example of a parent that provides default param values.

    >>> mf = modelfile.from_string("""
    ... - name: base
    ...   description: A v{{version}} {{type}} classifier
    ...   params:
    ...     version: 1
    ...
    ... - name: softmax
    ...   extends: base
    ...   params:
    ...     type: softmax
    ...
    ... - name: cnn
    ...   extends: base
    ...   params:
    ...     type: CNN
    ...     version: 2
    ... """)

    >>> mf["base"].description
    'A v1 {{type}} classifier'

    >>> mf["softmax"].description
    'A v1 softmax classifier'

    >>> mf["cnn"].description
    'A v2 CNN classifier'

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
