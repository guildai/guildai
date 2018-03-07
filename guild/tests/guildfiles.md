# Guildfiles

Guildfiles are files that contain model definitions. By convention
guild files are named `guild.yml`.

Support for guild files is provided by the `guildfile` module:

    >>> from guild import guildfile

## Loading a guild file from a directory

Use `from_dir` to load a guild file from a directory:

    >>> gf = guildfile.from_dir(sample("projects/mnist"))
    >>> gf.src
    '.../samples/projects/mnist/guild.yml'

## Loading a guildfile from a file

Use `from_file` to load a guildfile from a file directly:

    >>> gf = guildfile.from_file(sample("projects/mnist/guild.yml"))

Models are access using the `models` attribute:

    >>> sorted(gf.models.items())
    [('expert', <guild.guildfile.ModelDef 'expert'>),
     ('intro', <guild.guildfile.ModelDef 'intro'>)]

### Accessing modeldefs

We can lookup a models using dictionary semantics:

    >>> gf.models["intro"]
    <guild.guildfile.ModelDef 'intro'>

    >>> gf.models.get("intro")
    <guild.guildfile.ModelDef 'intro'>

    >>> print(gf.models.get("undefined"))
    None

### Default model

The first model defined in a project is considered to be the default
model:

    >>> gf.default_model
    <guild.guildfile.ModelDef 'intro'>

### Attributes

The model name is used to identify the model:

    >>> gf.models["expert"].name
    'expert'

    >>> gf.models["intro"].name
    'intro'

The description provides additional details:

    >>> gf.models["expert"].description
    'Sample model'

### Flags

Flags are named values that are provided to operations during a
run. Flags can be defined at the model level and at the operation
level.

Our sample guildfile uses an advanced scheme of including flag
definitions from a shared config into two models. Refer to
[samples/projects/mnist/guild.yml](samples/projects/mnist/guild.yml)
for details on how this is structured.

We'll use a helper function to print the flagdefs:

    >>> def flagdefs(flags):
    ...   return [
    ...     (flag.name, flag.description, flag.default)
    ...     for flag in flags]

Let's look at the flags defined for the `intro` model:

    >>> flagdefs(gf.models["intro"].flags)
    [('batch-size', 'Number of images per batch', 100),
     ('epochs', 'Number of epochs to train', 10),
     ('learning-rate', 'Learning rate for training', 0.001)]

Note that while the value for `epochs` is redefined, the original flag
description is not.

Flag *values* are distinct from flag *definitions*. The default value
associated with a flag definition is used as the initial flag
value. We can read the flag values using `get_flag_value`:

    >>> gf.models["intro"].get_flag_value("batch-size")
    100

    >>> gf.models["intro"].get_flag_value("epochs")
    10

These values can be modified without effecting the flag definitions.

    >>> gf.models["intro"].set_flag_value("epochs", 3)

    >>> gf.models["intro"].get_flag_value("epochs")
    3

    >>> gf.models["intro"].get_flagdef("epochs").default
    10

Here are the flag defs for `expert`:

    >>> flagdefs(gf.models["expert"].flags)
    [('batch-size', 'Number of images per batch', 100),
     ('epochs', 'Number of epochs to train', 5)]

In this case the `expert` model included all of the `common`
flag definitions without redefining any.

The third set of flags defined in the guildfile is associated with the
`evaluate` operation of the `intro` model.

    >>> eval_op = gf.models["intro"].get_operation("evaluate")
    >>> flagdefs(eval_op.flags)
    [('batch-size', '', 50000),
     ('epochs', '', 1)]

In this case the operation did not include flagdefs and did not
provide descriptions for its flags.

Operations inherit the values of flags defined in their host
models. We can use `all_flag_values` to retrieve all of the flag
values associated with a model or op definition.

Flag values for `intro` model:

    >>> pprint(gf.models["intro"].flag_values())
    {'batch-size': 100, 'epochs': 3, 'learning-rate': 0.001}

Flag values for `evaluate` op of `intro` model:

    >>> pprint(gf.models["intro"].get_operation("evaluate").flag_values())
    {'batch-size': 50000, 'epochs': 1, 'learning-rate': 0.001}

Flag values for `expert` model:

    >>> pprint(gf.models["expert"].flag_values())
    {'batch-size': 100, 'epochs': 5}

Flag values for `train` op of `expert` model:

    >>> pprint(gf.models["expert"].get_operation("train").flag_values())
    {'batch-size': 100, 'epochs': 5}

If we set the value of a flag defined on a model that is not defined
by the model's operation, the operation inherits that value:

    >>> gf.models["intro"].set_flag_value("learning-rate", 0.002)
    >>> pprint(gf.models["intro"].get_operation("evaluate").flag_values())
    {'batch-size': 50000, 'epochs': 1, 'learning-rate': 0.002}

However, if the operation defines a flag value, setting the value on
the operation's model doesn't modify the operation's flag value:

    >>> gf.models["intro"].set_flag_value("epochs", 4)
    >>> pprint(gf.models["intro"].get_operation("evaluate").flag_values())
    {'batch-size': 50000, 'epochs': 1, 'learning-rate': 0.002}

### Updating flags

Flags can be updated using flags from another flag host.

Consider this guildfile:

    >>> gf2 = guildfile.from_string("""
    ... model: sample
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

    >>> opdef_a = gf2.models["sample"].get_operation("a")
    >>> opdef_b = gf2.models["sample"].get_operation("b")

Here are the flags and values for opdef a:

    >>> opdef_a.flags
    [<guild.guildfile.FlagDef 'x'>, <guild.guildfile.FlagDef 'y'>]

    >>> pprint(opdef_a.flag_values())
    {'x': 'X1', 'y': 'Y'}

And the flags and values for opdef b:

    >>> opdef_b.flags
    [<guild.guildfile.FlagDef 'x'>, <guild.guildfile.FlagDef 'z'>]

    >>> pprint(opdef_b.flag_values())
    {'x': 'x2', 'z': 'Z'}

We'll update opdef a flags with those from opdef b:

    >>> opdef_a.update_flags(opdef_b)

The updated flags:

    >>> opdef_a.flags
    [<guild.guildfile.FlagDef 'x'>,
     <guild.guildfile.FlagDef 'y'>,
     <guild.guildfile.FlagDef 'z'>]

and values:

    >>> pprint(opdef_a.flag_values())
    {'x': 'x2', 'y': 'Y', 'z': 'Z'}

## Operations

Operations are ordered by name:

    >>> [op.name for op in gf.models["expert"].operations]
    ['evaluate', 'train']

Find an operation using a model's `get_op` method:

    >>> gf.models["expert"].get_operation("train")
    <guild.guildfile.OpDef 'expert:train'>

`get_op` returns None if the operation isn't defined for the model:

    >>> print(gf.models["expert"].get_operation("not-defined"))
    None

### Plugin ops

An operation can delegate its implementation to a plugin using the
`plugin-op` attribute. Here's a sample guildfile:

    >>> gf2 = guildfile.from_string("""
    ... model: sample
    ... operations:
    ...   train:
    ...     plugin-op: foo-train
    ... """)

The opdef in this case will use `plugin_op` rather than `cmd`. Plugin
ops are provided as guildfile.PluginOp objects and have `name` and
`config` attributes:

    >>> train = gf2.models["sample"].get_operation("train")

    >>> train.plugin_op
    'foo-train'

## Resources

Model resources are are named lists of sources that may be required by
operations. Our sample models each have the following resources:

    >>> gf.models["expert"].resources
    [<guild.guildfile.ResourceDef 'data'>]

    >>> gf.models["intro"].resources
    []

In the same way that models can include flag definitions, they can
include resources. In our example, the `expert` model includes
resources from `common` config.

A resource source consists of a URI and other information that Guild
uses to fully resolve the source. URIs are specified indirectly using
one of three source type attributes:

- file
- url
- operation

Here's a model definition that contains various resource sources:

    >>> gf = guildfile.from_string("""
    ... model: sample
    ... resources:
    ...   sample:
    ...     sources:
    ...       - foo.txt
    ...       - file: bar.tar.gz
    ...       - url: https://files.com/bar.tar.gz
    ...       - operation: train/model.meta
    ... """)

Here are the associated resource sources:

    >>> gf.models["sample"].get_resource("sample").sources
    [<guild.resourcedef.ResourceSource 'file:foo.txt'>,
     <guild.resourcedef.ResourceSource 'file:bar.tar.gz'>,
     <guild.resourcedef.ResourceSource 'https://files.com/bar.tar.gz'>,
     <guild.resourcedef.ResourceSource 'operation:train/model.meta'>]

Note that when a source is specified as a string it is treated as a
file.

At least one of the three type attributes is required:

    >>> guildfile.from_string("""
    ... model: sample
    ... resources:
    ...   sample:
    ...     sources:
    ...       - foo: bar.txt
    ... """)
    Traceback (most recent call last):
    ResourceFormatError: invalid source {'foo': 'bar.txt'} in resource 'sample': missing
    required attribute (one of file, url, module, operation)

However, no more than one is allowed:

    >>> guildfile.from_string("""
    ... model: sample
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

    >>> gf = guildfile.from_string("""
    ... model: sample
    ... references:
    ...   - https://arxiv.org/abs/1603.05027
    ...   - https://arxiv.org/abs/1512.03385
    ... """)
    >>> gf.models["sample"].references
    ['https://arxiv.org/abs/1603.05027', 'https://arxiv.org/abs/1512.03385']

## Includes

See [includes.md](includes.md) for guildfile include tests.

## Model inheritance

### Data merging

Model inheritance works using a low level data merge facility
implemented by `guildfile._apply_parent_data`.

Here's a helper function to apply parent data and print the result:

    >>> def apply_parent(parent, child):
    ...     guildfile._apply_parent_data(parent, child)
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

    >>> guildfile._apply_parent_data(parent, child)

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

Here's a guild file that defines a model that extends another:

    >>> gf = guildfile.from_string("""
    ... - model: trainable
    ...   description: A trainable model
    ...   operations:
    ...     train:
    ...       cmd: train
    ...       flags:
    ...         batch-size: 32
    ...
    ... - model: model-1
    ...   extends: trainable
    ... """)

`model-1` inherits the operations of its parent `trainable`:

    >>> m1 = gf.models["model-1"]
    >>> m1.operations
    [<guild.guildfile.OpDef 'model-1:train'>]

It also inherits the description:

    >>> m1.description
    'A trainable model'

Models do not inherit name:

    >>> m1.name
    'model-1'

Here's a more complex example with two parent models and two child
models.

    >>> gf = guildfile.from_string("""
    ... - model: trainable
    ...   description: A trainable model
    ...   operations:
    ...     train:
    ...       cmd: train
    ...       flags:
    ...         batch-size: 32
    ...
    ... - model: evaluatable
    ...   description: An evaluatable model
    ...   operations:
    ...     evaluate:
    ...       cmd: train --test
    ...
    ... - model: model-1
    ...   description: A trainable, evaluatable model
    ...   extends: [trainable, evaluatable]
    ...
    ... - model: model-2
    ...   extends: trainable
    ...   operations:
    ...     train:
    ...       flags:
    ...         batch-size: 16
    ... """)

In this example, `model-1` extends two models and so inherits
attributes from both.

    >>> m1 = gf.models["model-1"]
    >>> m1.operations
    [<guild.guildfile.OpDef 'model-1:evaluate'>,
     <guild.guildfile.OpDef 'model-1:train'>]


It's other attributes:

    >>> m1.name
    'model-1'

    >>> m1.description
    'A trainable, evaluatable model'

As a point of comparison to `model-2` below, `model-1` inherits the
default for the `batch-size` attribute:

    >>> m1.get_operation("train").get_flagdef("batch-size").default
    32

`model-2` only extends one parent, but it modifies a flag default.

    >>> m2 = gf.models["model-2"]

    >>> m2.operations
    [<guild.guildfile.OpDef 'model-2:train'>]

    >>> m2.get_operation("train").get_flagdef("batch-size").default
    16

In this example, a model extends a model that in turn extends another
model:

    >>> gf = guildfile.from_string("""
    ... - model: a
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
    ... - model: b
    ...   extends: a
    ...   operations:
    ...     train:
    ...       flags:
    ...         f2:
    ...           description: f2 in b
    ...           default: 22
    ...     eval:
    ...       cmd: eval
    ... - model: c
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

    >>> a = gf.models["a"]

    >>> a.operations
    [<guild.guildfile.OpDef 'a:train'>]

    >>> [(f.name, f.description, f.default)
    ...   for f in a.get_operation("train").flags]
    [('f1', 'f1 in a', 1), ('f2', 'f2 in a', 2), ('f3', 'f3 in a', 3)]

Model `b`:

    >>> b = gf.models["b"]

    >>> b.operations
    [<guild.guildfile.OpDef 'b:eval'>,
     <guild.guildfile.OpDef 'b:train'>]

    >>> [(f.name, f.description, f.default)
    ...   for f in b.get_operation("train").flags]
    [('f1', 'f1 in a', 1), ('f2', 'f2 in b', 22), ('f3', 'f3 in a', 3)]

Model `c`:

    >>> c = gf.models["c"]

    >>> c.operations
    [<guild.guildfile.OpDef 'c:eval'>,
     <guild.guildfile.OpDef 'c:predict'>,
     <guild.guildfile.OpDef 'c:train'>]

    >>> [(f.name, f.description, f.default)
    ...   for f in c.get_operation("train").flags]
    [('f1', 'f1 in a', 1), ('f2', 'f2 in b', 22), ('f3', 'f3 in c', 33)]

### Inheritance cycles

Below are some inheritance cycles:

    >>> guildfile.from_string("""
    ... - model: a
    ...   extends: a
    ... """)
    Traceback (most recent call last):
    GuildfileCycleError: error in <string>: cycle in 'extends' (a -> a)

    >>> guildfile.from_string("""
    ... - model: a
    ...   extends: b
    ... - model: b
    ...   extends: a
    ... """)
    Traceback (most recent call last):
    GuildfileCycleError: error in <string>: cycle in 'extends' (b -> a -> b)

### Params

Params may be used in model parents to define place-holder for child
models. Here's s simple example:

    >>> gf = guildfile.from_string("""
    ... - model: base
    ...   description: A {{type}} classifier
    ...
    ... - model: softmax
    ...   extends: base
    ...   params:
    ...     type: softmax
    ...
    ... - model: cnn
    ...   extends: base
    ...   params:
    ...     type: CNN
    ... """)

Here are the description of each model:

    >>> gf.models["base"].description
    'A {{type}} classifier'

    >>> gf.models["softmax"].description
    'A softmax classifier'

    >>> gf.models["cnn"].description
    'A CNN classifier'

Here's an example of a parent that provides default param values.

    >>> gf = guildfile.from_string("""
    ... - model: base
    ...   description: A v{{version}} {{type}} classifier
    ...   params:
    ...     version: 1
    ...
    ... - model: softmax
    ...   extends: base
    ...   params:
    ...     type: softmax
    ...
    ... - model: cnn
    ...   extends: base
    ...   params:
    ...     type: CNN
    ...     version: 2
    ... """)

    >>> gf.models["base"].description
    'A v1 {{type}} classifier'

    >>> gf.models["softmax"].description
    'A v1 softmax classifier'

    >>> gf.models["cnn"].description
    'A v2 CNN classifier'

## Projects

In addition to containing resources, Guildfiles may contain at most
one package definition.

We'll use
[samples/projects/package/guild.yml](samples/projects/package/guild.yml)
to illustrate.

    >>> gf = guildfile.from_dir(sample("projects/package"))

The sample doesn't contain any models:

    >>> gf.models
    {}

It does contain a package:

    >>> gf.package
    <guild.guildfile.PackageDef 'hello'>

## Errors

### Invalid format

    >>> guildfile.from_dir(sample("projects/invalid-format"))
    Traceback (most recent call last):
    GuildfileError: error in .../samples/projects/invalid-format/guild.yml:
    invalid guildfile data: 'This is invalid YAML!'

### No models (missing guild file)

    >>> guildfile.from_dir(sample("projects/missing-sources"))
    Traceback (most recent call last):
    NoModels: ...

A file not found error is Python version specific (FileNotFoundError
in Python 3 and IOError in Python 2) so we'll assert using exception
content.

    >>> try:
    ...   guildfile.from_file(sample("projects/missing-sources/guild.yml"))
    ... except IOError as e:
    ...   print(str(e))
    [Errno 2] No such file or directory: '.../projects/missing-sources/guild.yml'
