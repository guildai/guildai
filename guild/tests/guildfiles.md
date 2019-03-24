# Guildfiles

Guildfiles are files that contain model definitions. By convention
guild files are named `guild.yml`.

Support for guild files is provided by the `guildfile` module:

    >>> from guild import guildfile

## Loading a guild file from a directory

Use `from_dir` to load a guild file from a directory:

    >>> project = sample("projects/mnist-pkg")
    >>> gf = guildfile.from_dir(project)
    >>> gf.src
    '.../samples/projects/mnist-pkg/guild.yml'

## Loading a guildfile from a file

Use `from_file` to load a guildfile from a file directly:

    >>> gf = guildfile.from_file(sample("projects/mnist-pkg/guild.yml"))

Models are access using the `models` attribute:

    >>> pprint(gf.models)
    {'expert': <guild.guildfile.ModelDef 'expert'>,
     'intro': <guild.guildfile.ModelDef 'intro'>}

## Accessing modeldefs

We can lookup a models using dictionary semantics:

    >> gf.models["intro"]
    <guild.guildfile.ModelDef 'intro'>

    >>> gf.models.get("intro")
    <guild.guildfile.ModelDef 'intro'>

    >>> print(gf.models.get("undefined"))
    None

## Default model

Guild files may have a default model, which is implicitly used in
cases where a model is not specified explicitly.

If a Guild file contains only one model, that model is always the
default.

    >>> gf_default_model_test = guildfile.from_string("""
    ... - model: foo
    ... """)
    >>> gf_default_model_test.default_model
    <guild.guildfile.ModelDef 'foo'>

If the file contains more than one model, a model must explicitly be
designated as default.

In this case, foo is default:

    >>> gf_default_model_test = guildfile.from_string("""
    ... - model: foo
    ...   default: yes
    ... - model: bar
    ... """)
    >>> gf_default_model_test.default_model
    <guild.guildfile.ModelDef 'foo'>

In this case, bar is default:

    >>> gf_default_model_test = guildfile.from_string("""
    ... - model: foo
    ... - model: bar
    ...   default: yes
    ... """)
    >>> gf_default_model_test.default_model
    <guild.guildfile.ModelDef 'bar'>

In this case, neither are default:

    >>> gf_default_model_test = guildfile.from_string("""
    ... - model: foo
    ... - model: bar
    ... """)
    >>> gf_default_model_test.default_model is None
    True

Of course, if a Guild file contains no models, there's no default.

    >>> guildfile.from_string("- config: foo").default_model is None
    True

In the case of our sample mnist project, there are two models, none of
which are designated as default. The default model is therefore None.

    >>> gf.default_model is None
    True

## Model attributes

The model name is used to identify the model:

    >>> gf.models["expert"].name
    'expert'

    >>> gf.models["intro"].name
    'intro'

The description provides additional details:

    >>> gf.models["expert"].description
    'Expert model'

## Operations

Operations are ordered by name:

    >>> [op.name for op in gf.models["expert"].operations]
    ['evaluate', 'train']

Find an operation using a model's `get_op` method:

    >>> gf.models["expert"].get_operation("train")
    <guild.guildfile.OpDef 'expert:train'>

`get_operation` returns None if the operation isn't defined for the
model:

    >>> print(gf.models["expert"].get_operation("not-defined"))
    None

### Default operation

If an operation is designated as `default` it can be accessed using
the `default_operation` attribute of the model def:

    >>> expert_model = gf.models["expert"]
    >>> train_op = expert_model.get_operation("train")
    >>> train_op.default
    True

    >>> expert_model.default_operation
    <guild.guildfile.OpDef 'expert:train'>

    >>> expert_model.default_operation is train_op
    True

The intro model doesn't have a default operation:

    >>> intro_model = gf.models["intro"]
    >>> train_op = intro_model.get_operation("train")
    >>> train_op.default
    False

    >>> print(intro_model.default_operation)
    None

`get_operation` fails if op_name is None:

    >>> expert_model.get_operation(None)
    Traceback (most recent call last):
    ValueError: name cannot be None

### Op coercion

If an operation is specified as a string, the string value is assumed
to be the `main` attribute.

    >>> gf_op_coerce = guildfile.from_string("""
    ... - model: foo
    ...   operations:
    ...     test: test
    ... """)

    >>> gf_op_coerce.models["foo"].get_operation("test").main
    'test'

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

Let's look at the flags defined for `intro:train`:

    >>> intro_train = gf.models["intro"].get_operation("train")
    >>> flagdefs(intro_train.flags)
    [('batch-size', 'Number of images per train batch', 100),
     ('clones', 'Number of clones to deploy to', None),
     ('epochs', 'Number of epochs to train', 10),
     ('learning-rate', 'Learning rate for training', 0.001)]

Note that while the value for `epochs` is redefined (to 10 from 5),
the flag description is not.

Flag *values* are distinct from flag *definitions*. The default value
associated with a flag definition is used as the initial flag
value. We can read the flag values using `get_flag_value`:

    >>> intro_train.get_flag_value("batch-size")
    100

    >>> intro_train.get_flag_value("epochs")
    10

These values can be modified without effecting the flag definitions.

    >>> intro_train.set_flag_value("epochs", 3)
    >>> intro_train.get_flag_value("epochs")
    3
    >>> intro_train.get_flagdef("epochs").default
    10

Here are the flag defs for `expert:train`:

    >>> expert_train = gf.models["expert"].get_operation("train")
    >>> flagdefs(expert_train.flags)
    [('batch-size', 'Number of images per train batch', 100),
     ('clones', 'Number of clones to deploy to', None),
     ('epochs', 'Number of epochs to train', 5),
     ('learning-rate', 'Learning rate for training', 0.001)]

In this case the `expert:train` operation included all of the `common`
flag definitions without redefining any.

Here are the flags for `intro:evaluate`:

    >>> intro_evaluate = gf.models["intro"].get_operation("evaluate")
    >>> flagdefs(intro_evaluate.flags)
    [('batch-size', 'Number of images per eval batch', 50000),
     ('epochs', 'Epochs to evaluate', 2)]

In this case the operation redefined the value for `epochs` (to 2 from
1) but did not change `batch-size`.

### Merging flags

From from one opdef can be merged into another opdef.

Consider this guildfile:

    >>> gf_flag_update = guildfile.from_string("""
    ... a:
    ...   exec: a
    ...   flags:
    ...     x: X1
    ...     y: Y
    ... b:
    ...   exec: b
    ...   flags:
    ...     x: X2
    ...     z: Z
    ... """)

The two opdefs:

    >>> opdef_a = gf_flag_update.default_model.get_operation("a")
    >>> opdef_b = gf_flag_update.default_model.get_operation("b")

Here are the flags and values for opdef a:

    >>> opdef_a.flags
    [<guild.guildfile.FlagDef 'x'>, <guild.guildfile.FlagDef 'y'>]

    >>> pprint(opdef_a.flag_values())
    {'x': 'X1', 'y': 'Y'}

And the flags and values for opdef b:

    >>> opdef_b.flags
    [<guild.guildfile.FlagDef 'x'>, <guild.guildfile.FlagDef 'z'>]

    >>> pprint(opdef_b.flag_values())
    {'x': 'X2', 'z': 'Z'}

Let's merge the values from b into a:

    >>> opdef_a.merge_flags(opdef_b)

The merged flags:

    >>> opdef_a.flags
    [<guild.guildfile.FlagDef 'x'>,
     <guild.guildfile.FlagDef 'y'>,
     <guild.guildfile.FlagDef 'z'>]

and values:

    >>> pprint(opdef_a.flag_values())
    {'x': 'X1', 'y': 'Y', 'z': 'Z'}

Note that values for a take precedence over values from b in a merge.

### Optimizer defs

Operations may define one or more optimizers. Optimizers may be
specified for an operation in two ways:

- As a string, which is the optimizer algorithm
- As a dict containing the optimizer algorithm and flag vals

An optimizer has a name, opspec, default status, and flags:

    >>> def print_optimizer(opt):
    ...     print("name:", opt.name)
    ...     print("opspec:", opt.opspec)
    ...     print("default:", opt.default)
    ...     print("flags: ", end="")
    ...     pprint(opt.flags)

A single optimizer may be defined using the `optimizer` attribute.

    >>> op = guildfile.from_string("""
    ... test:
    ...   optimizer: gp
    ... """).default_model.default_operation

    >>> op.optimizers
    [<guild.guildfile.OptimizerDef 'gp'>]

Optimizers can be read by name:

    >>> op.get_optimizer("gp")
    <guild.guildfile.OptimizerDef 'gp'>

When specified as a string, the optimizer opspec is the same as the
string and the optimizer has no flags:

    >>> print_optimizer(op.get_optimizer("gp"))
    name: gp
    opspec: gp
    default: False
    flags: {}

A single optimizer is always the default regardless of its default
status:

    >>> op.default_optimizer is op.get_optimizer("gp")
    True

A single optimizer may alternatively be specified as a dict, in which
case it must contain an `algorithm` attribute:

    >>> op = guildfile.from_string("""
    ... test:
    ...   optimizer:
    ...     algorithm: gp
    ... """).default_model.default_operation

    >>> print_optimizer(op.default_optimizer)
    name: gp
    opspec: gp
    default: False
    flags: {}

If it doesn't specify an algorithm, an error is generated:

    >>> guildfile.from_string("""
    ... test:
    ...   optimizer: {}
    ... """)
    Traceback (most recent call last):
    GuildfileError: error in <string>: missing required 'algorithm'
    attribute in {}

When specified as a dict, additional attributes - with the exception
of `default` - are considered optimizer flags:

    >>> op = guildfile.from_string("""
    ... test:
    ...   optimizer:
    ...     algorithm: gp
    ...     default: yes
    ...     random-starts: 3
    ...     kappa: 1.8
    ...     noise: 0.1
    ... """).default_model.default_operation

    >>> print_optimizer(op.default_optimizer)
    name: gp
    opspec: gp
    default: True
    flags: {'kappa': 1.8, 'noise': 0.1, 'random-starts': 3}

Multiple optimizers may be defined using the `optimizers` attribute.

    >>> op = guildfile.from_string("""
    ... test:
    ...   optimizers:
    ...     gp-1:
    ...       algorithm: gp
    ...       kappa: 1.6
    ...     gp-2:
    ...       algorithm: gp
    ...       kappa: 1.8
    ... """).default_model.default_operation

    >>> op.optimizers
    [<guild.guildfile.OptimizerDef 'gp-1'>,
     <guild.guildfile.OptimizerDef 'gp-2'>]

    >>> print_optimizer(op.get_optimizer("gp-1"))
    name: gp-1
    opspec: gp
    default: False
    flags: {'kappa': 1.6}

    >>> print_optimizer(op.get_optimizer("gp-2"))
    name: gp-2
    opspec: gp
    default: False
    flags: {'kappa': 1.8}

When multiple optimizers are specified and none have a default
designation, there is no default optimizer:

    >>> print(op.default_optimizer)
    None

When multiple optimizers are specified, the algorithm may be omitted
when specifying dict values, in which case the dict name is used as
the algorithm:

    >>> op = guildfile.from_string("""
    ... test:
    ...   optimizers:
    ...     gp:
    ...       kappa: 1.6
    ...       noise: 0.1
    ...     forest:
    ...       default: yes
    ...       kappa: 1.8
    ... """).default_model.default_operation

    >>> op.optimizers
    [<guild.guildfile.OptimizerDef 'forest'>,
     <guild.guildfile.OptimizerDef 'gp'>]

    >>> print_optimizer(op.get_optimizer("forest"))
    name: forest
    opspec: forest
    default: True
    flags: {'kappa': 1.8}

    >>> print_optimizer(op.get_optimizer("gp"))
    name: gp
    opspec: gp
    default: False
    flags: {'kappa': 1.6, 'noise': 0.1}

Note also in this example that we have a default optimizer:

    >>> op.default_optimizer
    <guild.guildfile.OptimizerDef 'forest'>

When specifying multiple optimizers, string values are coerced in the
same way they with a single optimizer. This is effectively a way of
renaming optimizer algorithms:

    >>> op = guildfile.from_string("""
    ... test:
    ...   optimizers:
    ...     bayesian: skopt:gp
    ...     experimental: tune
    ... """).default_model.default_operation

    >>> op.optimizers
    [<guild.guildfile.OptimizerDef 'bayesian'>,
     <guild.guildfile.OptimizerDef 'experimental'>]

    >>> print_optimizer(op.get_optimizer("bayesian"))
    name: bayesian
    opspec: skopt:gp
    default: False
    flags: {}

    >>> print_optimizer(op.get_optimizer("experimental"))
    name: experimental
    opspec: tune
    default: False
    flags: {}

An operation may not contain both `optimizer` and `optimizers`.

    >>> guildfile.from_string("""
    ... test:
    ...   optimizer: gp
    ...   optimizers:
    ...     gp-2: gp
    ... """)
    Traceback (most recent call last):
    GuildfileError: error in <string>: conflicting optimizer configuration
    in operation 'test' - cannot define both 'optimizer' and 'optimizers'

### Representing operation defs as data

An operation def can be represented as data by calling `as_data()`.

    >>> pprint(opdef_a.as_data())
    {'exec': 'a', 'flags': {'x': {'default': 'X1'}, 'y': {'default': 'Y'}}}

    >>> pprint(opdef_b.as_data())
    {'exec': 'b', 'flags': {'x': {'default': 'X2'}, 'z': {'default': 'Z'}}}

    >>> pprint(gf.models["expert"].get_operation("train").as_data())
    {'default': True,
     'flags': {'$include': 'default-train-flags'},
     'main': 'expert'}

    >>> pprint(gf.models["expert"].get_operation("evaluate").as_data())
    {'flags': {'$include': 'default-eval-flags'}, 'main': 'expert --test'}

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
    ... - model: sample
    ...   resources:
    ...     sample:
    ...       sources:
    ...         - foo.txt
    ...         - file: bar.tar.gz
    ...         - url: https://files.com/bar.tar.gz
    ...         - operation: train/model.meta
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
    ... - model: sample
    ...   resources:
    ...     sample:
    ...       sources:
    ...         - foo: bar.txt
    ... """)
    Traceback (most recent call last):
    ResourceFormatError: invalid source {'foo': 'bar.txt'} in resource 'sample:sample':
    missing required attribute (one of file, url, module, operation)

However, no more than one is allowed:

    >>> guildfile.from_string("""
    ... - model: sample
    ...   resources:
    ...     sample:
    ...       sources:
    ...         - file: foo.txt
    ...           url: http://files.com/bar.txt
    ... """)
    Traceback (most recent call last):
    ResourceFormatError: invalid source {'file': 'foo.txt', 'url': 'http://files.com/bar.txt'}
    in resource 'sample:sample': conflicting attributes (file, url)

## References

A list of references may be included for each model. These can be used
to direct users to upstream sources and papers.

    >>> gf = guildfile.from_string("""
    ... - model: sample
    ...   references:
    ...     - https://arxiv.org/abs/1603.05027
    ...     - https://arxiv.org/abs/1512.03385
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
    ...       'main': 'eval',
    ...       'description': 'Evaluate a trained model',
    ...       'requires': ['model', 'data']
    ...     },
    ...     'train': {
    ...       'main': 'train',
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
    ...       'main': 'train --test',
    ...     },
    ...     'prepare': {
    ...       'main': 'prepare'
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
    {'description': 'Train a model',
     'flags': {'batch-size': {'default': 101, 'description': 'Batch size'},
               'epochs': {'default': 10,
                          'description': 'Number of epochs to train'}},
     'main': 'train',
     'requires': 'data'}

    >>> pprint(child["operations"]["evaluate"])
    {'description': 'Evaluate a trained model',
     'main': 'train --test',
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
    ...       exec: train
    ...       flags:
    ...         batch-size: 32
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
    ...       exec: train
    ...       flags:
    ...         batch-size: 32
    ...
    ... - model: evaluatable
    ...   description: An evaluatable model
    ...   operations:
    ...     evaluate:
    ...       exec: train --test
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
    ...       exec: train
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
    ...       exec: eval
    ... - model: c
    ...   extends: b
    ...   operations:
    ...     train:
    ...       flags:
    ...         f3:
    ...           description: f3 in c
    ...           default: 33
    ...     predict:
    ...       main: predict
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

In this example, one model extends two configs, each of which extends
one config:

    >>> gf = guildfile.from_string("""
    ... - config: a
    ...   operations:
    ...     a_op: {}
    ... - config: b
    ...   operations:
    ...     b_op: {}
    ...   extends: a
    ... - config: c
    ...   operations:
    ...     c_op: {}
    ...   extends: a
    ... - model: m
    ...   extends: [b, c]
    ... """)

    >>> gf.models["m"].operations
    [<guild.guildfile.OpDef 'm:a_op'>,
     <guild.guildfile.OpDef 'm:b_op'>,
     <guild.guildfile.OpDef 'm:c_op'>]

### Defining default flag values

It's common to inherit from a model definition and modify default flag
values.

Here's an example where model `b` extends `a` and redefines two flag
defaults for an operation. Note that `b` simply redefines the values.

    >>> gf = guildfile.from_string("""
    ... - model: a
    ...   operations:
    ...     test:
    ...       flags:
    ...         f1:
    ...           description: Flag f1
    ...           default: 1
    ...         f2:
    ...           description: Flag f2
    ...           default: 2
    ...
    ... - model: b
    ...   extends: a
    ...   operations:
    ...     test:
    ...       flags:
    ...         f1: 3
    ...         f2: 4
    ... """)

    >>> [(f.name, f.description, f.default)
    ...  for f in gf.models["a"].get_operation("test").flags]
    [('f1', 'Flag f1', 1), ('f2', 'Flag f2', 2)]

    >>> [(f.name, f.description, f.default)
    ...  for f in gf.models["b"].get_operation("test").flags]
    [('f1', 'Flag f1', 3), ('f2', 'Flag f2', 4)]


### Parameters

Parameters are defined in config or models. They can be used as values
in other config using the syntax `{{NAME}}` where `NAME` is the
parameter name.

    >>> gf = guildfile.from_string("""
    ... - model: m
    ...   params:
    ...     n: 10
    ...   description: Value of n is {{n}}
    ... """)

    >>> gf.default_model.description
    'Value of n is 10'

Param values are passed through when they can be:

Here's a case with a flag value:

    >>> gf = guildfile.from_string("""
    ... - model: m
    ...   params:
    ...     n: 10.0
    ...   operations:
    ...     o:
    ...       flags:
    ...         n: '{{n}}'
    ...         n_str: n is {{n}}
    ... """)

    >>> op = gf.default_model.get_operation("o")
    >>> pprint(op.flag_values())
    {'n': 10.0, 'n_str': 'n is 10.0'}

### Multiple inheritance

The order in which parents are listed in an extends list determines
how parent values are applied. This rule is followed: as a parent is
applied to a child, the child takes on the values of the parent _as if
it defined those values itself_. Parents cannot redefine an attribute
that was defined by a perviously applied parent.

Here's an example that uses two configs, `a` and `b`:

    >>> base_config = """
    ... - config: a
    ...   params:
    ...     foo: 1
    ... - config: b
    ...   params:
    ...     foo: 2
    ... """

In the first case, a model `m` extends `a` first and then `b`:

    >>> gf = guildfile.from_string(base_config + """
    ... - model: m
    ...   extends: [a, b]
    ...   description: foo is {{foo}}
    ... """)
    >>> gf.models["m"].description
    'foo is 1'

In the second case, the order of parents is `b` first and then `a`:

    >>> gf = guildfile.from_string(base_config + """
    ... - model: m
    ...   extends: [b, a]
    ...   description: foo is {{foo}}
    ... """)
    >>> gf.models["m"].description
    'foo is 2'

Finally, `m` defines `foo` itself:

    >>> gf = guildfile.from_string(base_config + """
    ... - model: m
    ...   extends: [b, a]
    ...   params:
    ...     foo: 3
    ...   description: foo is {{foo}}
    ... """)
    >>> gf.models["m"].description
    'foo is 3'

This will surprise a user who assumes that the last parent overrides
previous parents. But this convention is used in Python's multiple
inheritance scheme.

Here's the same structure, applied in Python:

    >>> class A(object):
    ...   foo = 1

    >>> class B(object):
    ...   foo = 2

In case 1, `M` extends `A` and then `B`.

    >>> class M(A, B):
    ...   pass
    >>> M().foo
    1

In case 2, `M` extends `B` and then `A`:

    >>> class M(B, A):
    ...   pass
    >>> M().foo
    2

Finally, `M` defines `foo` itself:

    >>> class M(B, A):
    ...   foo = 3
    >>> M().foo
    3

### Extending packages

Guildfiles may extend models and config defined in packages.

When extending a package, the package must be defined on the system
path (sys.path). If it's not, an error will occur.

We'll use the 'extend-pkg' project to illustrate. This project extends
both config and a model defined in package 'pkg' (defined in
'extend-pkg/pkg').

    >>> extend_pkg_dir = sample("projects/extend-pkg")

First we'll try to load the project without including 'pkg' in the
system path.

    >>> import sys
    >>> extend_pkg_dir in sys.path
    False

    >>> gf = guildfile.from_dir(extend_pkg_dir)
    Traceback (most recent call last):
    GuildfileReferenceError: error in .../projects/extend-pkg/guild.yml:
    cannot find Guild file for package 'pkg'

Let's try again with 'extend-pkg' included in the system path:

    >>> with SysPath(prepend=[extend_pkg_dir]):
    ...     gf = guildfile.from_dir(extend_pkg_dir)

The Guildfile contains the two models, which both contain properties
inherited from the package.

    >>> pprint(gf.models)
    {'a': <guild.guildfile.ModelDef 'a'>,
     'b': <guild.guildfile.ModelDef 'b'>}

    >>> gf.models["a"].operations
    [<guild.guildfile.OpDef 'a:test'>]

    >>> gf.models["b"].operations
    [<guild.guildfile.OpDef 'b:test'>, <guild.guildfile.OpDef 'b:train'>]

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

### Using $includes and inheritance

This test uses a sample project:

    >>> project_dir = sample("projects/inherit-and-include")

We need to modify the system path to find a package referenced in the
project:

    >>> with SysPath(prepend=[project_dir]):
    ...     gf = guildfile.from_dir(project_dir)

Models:

    >>> sorted(gf.models)
    ['m', 'm2', 'm3']

Operations:

    >>> gf.models["m"].operations
    [<guild.guildfile.OpDef 'm:op-a'>,
     <guild.guildfile.OpDef 'm:op-b'>]

The flags defined for `op-a` are included via `a-flags` config that's
defined in the project Guild file.

    >>> gf.models["m"].get_operation("op-a").flags
    [<guild.guildfile.FlagDef 'a-1'>,
     <guild.guildfile.FlagDef 'a-2'>]

    >>> pprint(gf.models["m"].get_operation("op-a").flag_values())
    {'a-1': 1, 'a-2': 2}

    >>> gf.models["m"].get_operation("op-b").flags
    [<guild.guildfile.FlagDef 'b-1'>,
     <guild.guildfile.FlagDef 'b-2'>,
     <guild.guildfile.FlagDef 'b-3'>,
     <guild.guildfile.FlagDef 'b-4'>]

    >>> pprint(gf.models["m"].get_operation("op-b").flag_values())
    {'b-1': 11, 'b-2': 22, 'b-3': 3, 'b-4': 4}

Model `m3` uses a variety of flag includes for its sample operation:

    >>> m3_op = gf.models["m3"].get_operation("op")

And its flags:

    >>> m3_op_flags = [(f.name, f.default) for f in m3_op.flags]

We expect this:

    >>> expected = [
    ...   # Include: a-flags#a-1
    ...   ('a-1', 1),
    ...   # Include: b-flags-1#b-1
    ...   ('b-1', 11),
    ...   # Include: c-flags
    ...   ('c-1', 111),
    ...   ('c-2', 222),
    ...   # Include: m2:op#m-1,m-3
    ...   ('m-1', 1111),
    ...   ('m-3', 3333)]

    >>> m3_op_flags == expected, m3_op_flags
    (True, ...)

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

Parameters can include references to other parameters.

    >>> gf = guildfile.from_string("""
    ... - config: c1
    ...   params:
    ...     p1: 1
    ... - config: c2
    ...   extends: c1
    ...   params:
    ...     p2: '{{p1}} 2'
    ... - model: m
    ...   extends: c2
    ...   params:
    ...     p3: '{{p2}} 3'
    ...   description: Model {{p3}}
    ... """)

    >>> gf.models["m"].description
    'Model 1 2 3'

Here's a param ref cycle:

    >>> gf = guildfile.from_string("""
    ... - config: c1
    ...   params:
    ...     p1: '{{p2}}'
    ... - config: c2
    ...   extends: c1
    ...   params:
    ...     p2: '{{p1}}'
    ... - model: m
    ...   extends: c2
    ...   description: Model {{p2}}
    ... """)

    >>> gf.models["m"].description
    'Model {{p1}}'

Param values may be numbers:

    >>> gf = guildfile.from_string("""
    ... - model: m
    ...   params:
    ...     foo: 123
    ...   description: Model {{foo}}
    ... """)

    >>> gf.models["m"].description
    'Model 123'

## Anonymous models

A model named with the empty string is considered an *anonymous*
model:

    >>> gf = guildfile.from_string("""
    ... - model: ''
    ...   operations:
    ...     foo: foo
    ...     bar: bar
    ... """)

    >>> gf.models
    {'': <guild.guildfile.ModelDef ''>}

    >>> gf.models[""] == gf.default_model
    True

    >>> gf.default_model.operations
    [<guild.guildfile.OpDef 'bar'>,
     <guild.guildfile.OpDef 'foo'>]

Anonymous models may be defined using a top-level map of operations:

    >>> gf = guildfile.from_string("""
    ... foo: foo
    ... bar:
    ...   description: Bar
    ...   exec: hello
    ... """)

The model:

    >>> gf.models
    {'': <guild.guildfile.ModelDef ''>}

    >>> gf.models[""] == gf.default_model
    True

Its operations:

    >>> gf.default_model.operations
    [<guild.guildfile.OpDef 'bar'>, <guild.guildfile.OpDef 'foo'>]

foo:

    >>> foo = gf.default_model.get_operation("foo")
    >>> foo.description
    ''
    >>> foo.main
    'foo'
    >>> print(foo.exec_)
    None

bar:

    >>> bar = gf.default_model.get_operation("bar")
    >>> bar.description
    'Bar'
    >>> print(bar.main)
    None
    >>> bar.exec_
    'hello'

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
    <guild.guildfile.PackageDef 'gpkg.hello'>

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
