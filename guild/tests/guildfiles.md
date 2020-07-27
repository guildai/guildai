# Guild files

Guild files are files that contain model definitions. By convention
guild files are named `guild.yml`.

Support for Guild files is provided by the `guildfile` module:

    >>> from guild import guildfile

## Loading a Guild file from a directory

Use `for_dir` to load a guild file from a directory:

    >>> project = sample("projects/mnist-pkg")
    >>> gf = guildfile.for_dir(project)
    >>> gf.src
    '.../samples/projects/mnist-pkg/guild.yml'

## Loading a Guild file from a file

Use `for_file` to load a guildfile from a file directly:

    >>> gf = guildfile.for_file(sample("projects/mnist-pkg/guild.yml"))

Models are access using the `models` attribute:

    >>> pprint(gf.models)
    {'expert': <guild.guildfile.ModelDef 'expert'>,
     'intro': <guild.guildfile.ModelDef 'intro'>}

## Accessing modeldefs

We can lookup a models using dictionary semantics:

    >>> gf.models["intro"]
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

    >>> gf_default_model_test = guildfile.for_string("""
    ... - model: foo
    ... """)
    >>> gf_default_model_test.default_model
    <guild.guildfile.ModelDef 'foo'>

If the file contains more than one model, a model must explicitly be
designated as default.

In this case, foo is default:

    >>> gf_default_model_test = guildfile.for_string("""
    ... - model: foo
    ...   default: yes
    ... - model: bar
    ... """)
    >>> gf_default_model_test.default_model
    <guild.guildfile.ModelDef 'foo'>

In this case, bar is default:

    >>> gf_default_model_test = guildfile.for_string("""
    ... - model: foo
    ... - model: bar
    ...   default: yes
    ... """)
    >>> gf_default_model_test.default_model
    <guild.guildfile.ModelDef 'bar'>

In this case, neither are default:

    >>> gf_default_model_test = guildfile.for_string("""
    ... - model: foo
    ... - model: bar
    ... """)
    >>> gf_default_model_test.default_model is None
    True

Of course, if a Guild file contains no models, there's no default.

    >>> guildfile.for_string("- config: foo").default_model is None
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

    >>> gf.models["expert"]["train"]
    <guild.guildfile.OpDef 'expert:train'>

`get_operation` returns None if the operation isn't defined for the
model:

    >>> print(gf.models["expert"].get_operation("not-defined"))
    None

### Default operation

If an operation is designated as `default` it can be accessed using
the `default_operation` attribute of the model def:

    >>> expert_model = gf.models["expert"]
    >>> train_op = expert_model["train"]
    >>> train_op.default
    True

    >>> expert_model.default_operation
    <guild.guildfile.OpDef 'expert:train'>

    >>> expert_model.default_operation is train_op
    True

The intro model doesn't have a default operation:

    >>> intro_model = gf.models["intro"]
    >>> train_op = intro_model["train"]
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

    >>> gf_op_coerce = guildfile.for_string("""
    ... - model: foo
    ...   operations:
    ...     test: test
    ... """)

    >>> gf_op_coerce.models["foo"]["test"].main
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

    >>> intro_train = gf.models["intro"]["train"]
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

    >>> expert_train = gf.models["expert"]["train"]
    >>> flagdefs(expert_train.flags)
    [('batch-size', 'Number of images per train batch', 100),
     ('clones', 'Number of clones to deploy to', None),
     ('epochs', 'Number of epochs to train', 5),
     ('learning-rate', 'Learning rate for training', 0.001)]

In this case the `expert:train` operation included all of the `common`
flag definitions without redefining any.

Here are the flags for `intro:evaluate`:

    >>> intro_evaluate = gf.models["intro"]["evaluate"]
    >>> flagdefs(intro_evaluate.flags)
    [('batch-size', 'Number of images per eval batch', 50000),
     ('epochs', 'Epochs to evaluate', 2)]

In this case the operation redefined the value for `epochs` (to 2 from
1) but did not change `batch-size`.

### Merging flags

From from one opdef can be merged into another opdef.

Consider this guildfile:

    >>> gf_flag_update = guildfile.for_string("""
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

    >>> opdef_a = gf_flag_update.default_model["a"]
    >>> opdef_b = gf_flag_update.default_model["b"]

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

    >>> op = guildfile.for_string("""
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

    >>> op = guildfile.for_string("""
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

    >>> guildfile.for_string("""
    ... test:
    ...   optimizer: {}
    ... """)
    Traceback (most recent call last):
    GuildfileError: error in <string>: missing required 'algorithm'
    attribute in {}

When specified as a dict, additional attributes - with the exception
of `default` - are considered optimizer flags:

    >>> op = guildfile.for_string("""
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

    >>> op = guildfile.for_string("""
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
designation, the first optimizers is selected using lexicographical
order.

    >>> print(op.default_optimizer)
    <guild.guildfile.OptimizerDef 'gp-1'>

When multiple optimizers are specified, the algorithm may be omitted
when specifying dict values, in which case the dict name is used as
the algorithm:

    >>> op = guildfile.for_string("""
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

    >>> op = guildfile.for_string("""
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

    >>> guildfile.for_string("""
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

    >>> pprint(gf.models["expert"]["train"].as_data())
    {'default': True,
     'flags': {'$include': 'default-train-flags'},
     'main': 'expert'}

    >>> pprint(gf.models["expert"]["evaluate"].as_data())
    {'flags': {'$include': 'default-eval-flags'}, 'main': 'expert --test'}

### Including operations

Guild support `$includes` for operations.

    >>> gf_op_incl = guildfile.for_string("""
    ... - config: shared-ops
    ...   operations:
    ...     foo:
    ...       main: guild.pass
    ...       flags:
    ...         i: 1
    ...         f: 2.2
    ...     bar: guild.pass
    ... - model: m
    ...   operations:
    ...     $include: shared-ops
    ...     baz:
    ...       main: guild.pass
    ...       flags:
    ...         b: yes
    ... """)

    >>> gf_op_incl.models
    {'m': <guild.guildfile.ModelDef 'm'>}

    >>> m = gf_op_incl.models["m"]
    >>> m.operations
    [<guild.guildfile.OpDef 'm:bar'>,
     <guild.guildfile.OpDef 'm:baz'>,
     <guild.guildfile.OpDef 'm:foo'>]

    >>> m.get_operation("bar").flags
    []

    >>> m.get_operation("baz").flags
    [<guild.guildfile.FlagDef 'b'>]

    >>> m.get_operation("foo").flags
    [<guild.guildfile.FlagDef 'f'>, <guild.guildfile.FlagDef 'i'>]

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

    >>> gf = guildfile.for_string("""
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

    >>> guildfile.for_string("""
    ... - model: sample
    ...   resources:
    ...     sample:
    ...       sources:
    ...         - foo: bar.txt
    ... """)
    Traceback (most recent call last):
    GuildfileError: error in <string>: invalid source {'foo': 'bar.txt'}
    in resource 'sample:sample': missing required attribute (one of config,
    file, module, url, operation)

However, no more than one is allowed:

    >>> guildfile.for_string("""
    ... - model: sample
    ...   resources:
    ...     sample:
    ...       sources:
    ...         - file: foo.txt
    ...           url: http://files.com/bar.txt
    ... """)
    Traceback (most recent call last):
    GuildfileError: error in <string>: invalid source {'file': 'foo.txt',
    'url': 'http://files.com/bar.txt'} in resource 'sample:sample':
    conflicting attributes (file, url)

### Target Path

In 0.7, Guild renamed the `path` attr to `target-path` to help clarify
how the value is used.

The `path` value is supported forevermore without deprecation warning.

    >>> gf = guildfile.for_string("""
    ... op:
    ...   requires:
    ...    - file: foo.txt
    ...      path: data
    ... """)

    >>> res = gf.default_model.get_operation("op").dependencies[0].inline_resource
    >>> res.sources
    [<guild.resourcedef.ResourceSource 'file:foo.txt'>]

    >>> res.sources[0].target_path
    'data'

The `path` attribute is no longer supported in the API:

    >>> res.sources[0].path
    Traceback (most recent call last):
    AttributeError: 'ResourceSource' object has no attribute 'path'

The same holds for resources.

    >>> gf = guildfile.for_string("""
    ... - model: ''
    ...   resources:
    ...     foo:
    ...       path: data
    ... """)

    >>> gf.default_model.resources[0].target_path
    'data'

    >>> gf.default_model.resources[0].path
    Traceback (most recent call last):
    AttributeError: 'ResourceDef' object has no attribute 'path'

The preferred spelling is to use `target-path`:

    >>> gf = guildfile.for_string("""
    ... op:
    ...   requires:
    ...    - file: foo.txt
    ...      target-path: data
    ... """)

    >>> res = gf.default_model.get_operation("op").dependencies[0].inline_resource
    >>> res.sources[0].target_path
    'data'

    >>> gf = guildfile.for_string("""
    ... - model: ''
    ...   resources:
    ...     foo:
    ...       target-path: data
    ... """)

    >>> gf.default_model.resources[0].target_path
    'data'

If both attritubtes are specified, Guild logs a warning.

    >>> with LogCapture() as log:
    ...     _ = guildfile.for_string("""
    ... op:
    ...   requires:
    ...    - file: foo.txt
    ...      path: data1
    ...      target-path: data2
    ... """)

    >>> log.print_all()
    WARNING: target-path and path both specified for source file:foo.txt
    - using target-path

    >>> with LogCapture() as log:
    ...     _ = guildfile.for_string("""
    ... - model: ''
    ...   resources:
    ...     foo:
    ...       path: data1
    ...       target-path: data2
    ... """)

    >>> log.print_all()
    WARNING: target-path and path both specified for resource :foo
    - using target-path

### Unrecognized Source Attrs

    >>> with LogCapture() as log:
    ...     _ = guildfile.for_string("""
    ... - model: ''
    ...   resources:
    ...     foo:
    ...       - file: f
    ...         target-path: p
    ...         foo: 123
    ...         foo-bar: 456
    ... """)

    >>> log.print_all()
    WARNING: unexpected source attribute 'foo' in resource 'file:f'
    WARNING: unexpected source attribute 'foo-bar' in resource 'file:f'

## References

A list of references may be included for each model. These can be used
to direct users to upstream sources and papers.

    >>> gf = guildfile.for_string("""
    ... - model: sample
    ...   references:
    ...     - https://arxiv.org/abs/1603.05027
    ...     - https://arxiv.org/abs/1512.03385
    ... """)
    >>> gf.models["sample"].references
    ['https://arxiv.org/abs/1603.05027', 'https://arxiv.org/abs/1512.03385']

## Includes

See also [includes.md](includes.md) for guildfile include tests.

Some Guild file mappings support use of a special attribute
`$include`, which includes attributes defined in other Guild file
objects.

Here's an example of including flags defined in a `config` object.

    >>> gf = guildfile.for_string("""
    ... - config: shared-flags
    ...   flags:
    ...     foo: 123
    ...     bar: 456
    ...
    ... - operations:
    ...     op:
    ...       flags:
    ...         $include: shared-flags
    ... """)

    >>> gf.default_model.get_operation("op").flags
    [<guild.guildfile.FlagDef 'bar'>, <guild.guildfile.FlagDef 'foo'>]

Operations may be similarly included.

    >>> gf = guildfile.for_string("""
    ... - config: shared-ops
    ...   operations:
    ...     op1: guild.pass
    ...     op2: guild.pass
    ...
    ... - operations:
    ...     $include: shared-ops
    ... """)

    >>> gf.default_model.operations
    [<guild.guildfile.OpDef 'op1'>, <guild.guildfile.OpDef 'op2'>]

Resources:

    >>> gf = guildfile.for_string("""
    ... - config: shared-resources
    ...   resources:
    ...     r1:
    ...       - file: a.txt
    ...     r2:
    ...       - url: http://my.co/b.txt
    ...
    ... - model: ''
    ...   resources:
    ...     $include: shared-resources
    ... """)

    >>> gf.default_model.resources
    [<guild.guildfile.ResourceDef 'r1'>, <guild.guildfile.ResourceDef 'r2'>]

Flag values defined for steps can also be included.

In the following example, we define a `steps` operation that runs an
`op` operation as a single step. The steo includes flag values defined
in config `shared-flag-vals`.

    >>> gf = guildfile.for_string("""
    ... - config: shared-flag-vals
    ...   flags:
    ...     foo: 123
    ...     bar: 345
    ...
    ... - operations:
    ...     op:
    ...       main: guild.pass
    ...       flags:
    ...         foo: null
    ...         bar: null
    ...     steps:
    ...       steps:
    ...        - run: op
    ...          flags:
    ...            $include: shared-flag-vals
    ...            bar: 456
    ... """)

The values for an operation `steps` attribute is the config data,
which is used downstream by `guild.steps_main`. `guildfile` provides
special support for includes to resolve included flag values in the
config.

    >>> pprint(gf.default_model.get_operation("steps").steps)
    [{'flags': {'bar': 456, 'foo': 123}, 'run': 'op'}]

Here's another approach, where `steps` includes flags defined for
`op`.

    >>> gf = guildfile.for_string("""
    ... op:
    ...   main: guild.pass
    ...   flags:
    ...     foo: 123
    ...     bar: 456
    ... steps:
    ...   steps:
    ...    - run: op
    ...      flags:
    ...        $include: :op
    ...        bar: 789
    ... """)

    >>> pprint(gf.default_model.get_operation("steps").steps)
    [{'flags': {'bar': 789, 'foo': 123}, 'run': 'op'}]

And another case where steps includes a subset of flags.

    >>> gf = guildfile.for_string("""
    ... op:
    ...   main: guild.pass
    ...   flags:
    ...     foo: 123
    ...     bar: 456
    ...     baz: 789
    ... steps:
    ...   steps:
    ...    - run: op
    ...      flags:
    ...        $include: :op#bar,baz
    ...        bar: 789
    ... """)

    >>> pprint(gf.default_model.get_operation("steps").steps)
    [{'flags': {'bar': 789, 'baz': 789}, 'run': 'op'}]

### Include targets

Include targets are strings that contain model (top-level object),
operation, and attr specs. They're processed by the private function
`guildfile._split_include_ref`.

    >>> def split(ref):
    ...     return guildfile._split_include_ref(ref, "<string>")

Some examples:

    >>> split("")
    Traceback (most recent call last):
    GuildfileReferenceError: error in <string>: invalid include reference '':
    operation references must be specified as CONFIG[#ATTRS] or MODEL:OPERATION[#ATTRS]

    >>> split("shared-flags")
    ('shared-flags', None, None)

    >>> split("shared-flags#")
    ('shared-flags', None, None)

    >>> split("shared-flags#flag1")
    ('shared-flags', None, 'flag1')

    >>> split("shared-flags#flag1,flag2")
    ('shared-flags', None, 'flag1,flag2')

    >>> split(":some-op")
    ('', 'some-op', None)

    >>> split(":some-op#")
    ('', 'some-op', None)

    >>> split(":some-op#flag1")
    ('', 'some-op', 'flag1')

    >>> split(":some-op#flag1,flag2")
    ('', 'some-op', 'flag1,flag2')

    >>> split("some-model:some-op")
    ('some-model', 'some-op', None)

    >>> split("some-model:some-op#")
    ('some-model', 'some-op', None)

    >>> split("some-model:some-op#flag1")
    ('some-model', 'some-op', 'flag1')

    >>> split("some-model:some-op#flag1,flag2")
    ('some-model', 'some-op', 'flag1,flag2')

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

    >>> gf = guildfile.for_string("""
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

    >>> gf = guildfile.for_string("""
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

    >>> m1["train"].get_flagdef("batch-size").default
    32

`model-2` only extends one parent, but it modifies a flag default.

    >>> m2 = gf.models["model-2"]

    >>> m2.operations
    [<guild.guildfile.OpDef 'model-2:train'>]

    >>> m2["train"].get_flagdef("batch-size").default
    16

In this example, a model extends a model that in turn extends another
model:

    >>> gf = guildfile.for_string("""
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
    ...   for f in a["train"].flags]
    [('f1', 'f1 in a', 1), ('f2', 'f2 in a', 2), ('f3', 'f3 in a', 3)]

Model `b`:

    >>> b = gf.models["b"]

    >>> b.operations
    [<guild.guildfile.OpDef 'b:eval'>,
     <guild.guildfile.OpDef 'b:train'>]

    >>> [(f.name, f.description, f.default)
    ...   for f in b["train"].flags]
    [('f1', 'f1 in a', 1), ('f2', 'f2 in b', 22), ('f3', 'f3 in a', 3)]

Model `c`:

    >>> c = gf.models["c"]

    >>> c.operations
    [<guild.guildfile.OpDef 'c:eval'>,
     <guild.guildfile.OpDef 'c:predict'>,
     <guild.guildfile.OpDef 'c:train'>]

    >>> [(f.name, f.description, f.default)
    ...   for f in c["train"].flags]
    [('f1', 'f1 in a', 1), ('f2', 'f2 in b', 22), ('f3', 'f3 in c', 33)]

In this example, one model extends two configs, each of which extends
one config:

    >>> gf = guildfile.for_string("""
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

    >>> gf = guildfile.for_string("""
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
    ...  for f in gf.models["a"]["test"].flags]
    [('f1', 'Flag f1', 1), ('f2', 'Flag f2', 2)]

    >>> [(f.name, f.description, f.default)
    ...  for f in gf.models["b"]["test"].flags]
    [('f1', 'Flag f1', 3), ('f2', 'Flag f2', 4)]

### Parameters

Parameters are defined in config or models. They can be used as values
in other config using the syntax `{{NAME}}` where `NAME` is the
parameter name.

    >>> gf = guildfile.for_string("""
    ... - model: m
    ...   params:
    ...     n: 10
    ...   description: Value of n is {{n}}
    ... """)

    >>> gf.default_model.description
    'Value of n is 10'

Param values are passed through when they can be:

Here's a case with a flag value:

    >>> gf = guildfile.for_string("""
    ... - model: m
    ...   params:
    ...     n: 10.0
    ...   operations:
    ...     o:
    ...       flags:
    ...         n: '{{n}}'
    ...         n_str: n is {{n}}
    ... """)

    >>> op = gf.default_model["o"]
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

    >>> gf = guildfile.for_string(base_config + """
    ... - model: m
    ...   extends: [a, b]
    ...   description: foo is {{foo}}
    ... """)
    >>> gf.models["m"].description
    'foo is 1'

In the second case, the order of parents is `b` first and then `a`:

    >>> gf = guildfile.for_string(base_config + """
    ... - model: m
    ...   extends: [b, a]
    ...   description: foo is {{foo}}
    ... """)
    >>> gf.models["m"].description
    'foo is 2'

Finally, `m` defines `foo` itself:

    >>> gf = guildfile.for_string(base_config + """
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

    >>> gf = guildfile.for_dir(extend_pkg_dir)
    Traceback (most recent call last):
    GuildfileReferenceError: error in .../projects/extend-pkg/guild.yml:
    cannot find Guild file for package 'pkg'

Let's try again with 'extend-pkg' included in the system path:

    >>> with SysPath(prepend=[extend_pkg_dir]):
    ...     gf = guildfile.for_dir(extend_pkg_dir)

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

    >>> guildfile.for_string("""
    ... - model: a
    ...   extends: a
    ... """)
    Traceback (most recent call last):
    GuildfileCycleError: error in <string>: cycle in 'extends' (a -> a)

    >>> guildfile.for_string("""
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
    ...     gf = guildfile.for_dir(project_dir)

Models:

    >>> sorted(gf.models)
    ['m', 'm2', 'm3']

Operations:

    >>> gf.models["m"].operations
    [<guild.guildfile.OpDef 'm:op-a'>,
     <guild.guildfile.OpDef 'm:op-b'>]

The flags defined for `op-a` are included via `a-flags` config that's
defined in the project Guild file.

    >>> gf.models["m"]["op-a"].flags
    [<guild.guildfile.FlagDef 'a-1'>,
     <guild.guildfile.FlagDef 'a-2'>]

    >>> pprint(gf.models["m"]["op-a"].flag_values())
    {'a-1': 1, 'a-2': 2}

    >>> gf.models["m"]["op-b"].flags
    [<guild.guildfile.FlagDef 'b-1'>,
     <guild.guildfile.FlagDef 'b-2'>,
     <guild.guildfile.FlagDef 'b-3'>,
     <guild.guildfile.FlagDef 'b-4'>]

    >>> pprint(gf.models["m"]["op-b"].flag_values())
    {'b-1': 11, 'b-2': 22, 'b-3': 3, 'b-4': 4}

Model `m3` uses a variety of flag includes for its sample operation:

    >>> m3_op = gf.models["m3"]["op"]

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

    >>> gf = guildfile.for_string("""
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

    >>> gf = guildfile.for_string("""
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

    >>> gf = guildfile.for_string("""
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

    >>> gf = guildfile.for_string("""
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

    >>> gf = guildfile.for_string("""
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

    >>> gf = guildfile.for_string("""
    ... - operations:
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

    >>> gf = guildfile.for_string("""
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

    >>> foo = gf.default_model["foo"]
    >>> foo.description
    ''
    >>> foo.main
    'foo'
    >>> print(foo.exec_)
    None

bar:

    >>> bar = gf.default_model["bar"]
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

    >>> gf = guildfile.for_dir(sample("projects/package"))

The sample contains one model:

    >>> gf.models
    {'model-1': <guild.guildfile.ModelDef 'model-1'>}

It does contain a package:

    >>> gf.package
    <guild.guildfile.PackageDef 'gpkg.hello'>

## Loading from a run

If a run references a Guild file (in its `opref` attribute), the
references Guild file can be loaded using `for_run`.

Let's create a run in a temporary location:

    >>> from guild import run as runlib
    >>> run = runlib.for_dir(mkdtemp())
    >>> run.init_skel()

Next, configure the run's opref to reference a valid Guild file:

    >>> from guild import opref
    >>> gf_path = sample("projects", "mnist-pkg", "guild.yml")
    >>> run.write_opref(opref.OpRef("guildfile", gf_path, "", "", ""))

Now we can load the referenced Guild file using `for_run`:

    >>> gf = guildfile.for_run(run)
    >>> gf.src == gf_path
    True

If we try to load a Guild file from a run that references a missing
file, we get an error:

    >>> bad_path = path(mkdtemp(), "guild.yml")
    >>> run.write_opref(opref.OpRef("guildfile", bad_path, "", "", ""))

    >>> exists(bad_path)
    False

    >>> guildfile.for_run(run)
    Traceback (most recent call last):
    GuildfileMissing: .../guild.yml

## Operation Defaults

A model may provide defaults for operations using `operation-defaults`.

    >>> gf = guildfile.for_string("""
    ... - model: m
    ...   operation-defaults:
    ...     flags-dest: args
    ...     flags-import: no
    ...     sourcecode: no
    ...     flags:
    ...       f1: 1
    ...       f2: 2
    ...   operations:
    ...     op1: guild.pass
    ...     op2:
    ...       main: guild.pass
    ...       flags-import: all
    ...       sourcecode: ['*.py']
    ...       flags: {}
    ... """)

    >>> gf.default_model.operations
    [<guild.guildfile.OpDef 'm:op1'>, <guild.guildfile.OpDef 'm:op2'>]

`op1` takes all of its attrs from the defaults:

    >>> op1 = gf.default_model.get_operation("op1")
    >>> op1.flags_dest
    'args'

    >>> op1.flags_import
    []

    >>> op1.sourcecode.specs
    []

    >>> [(f.name, f.default) for f in op1.flags]
    [('f1', 1), ('f2', 2)]

`op2` redefines `flags-import` and `sourcecode`:

    >>> op2 = gf.default_model.get_operation("op2")
    >>> op2.flags_dest
    'args'

    >>> op2.flags_import
    True

    >>> op2.sourcecode.specs
    [<guild.guildfile.FileSelectSpec exclude *>,
     <guild.guildfile.FileSelectSpec include *.py>]

    >>> [(f.name, f.default) for f in op2.flags]
    []

Operation defaults can be inherited:

    >>> gf = guildfile.for_string("""
    ... - config: base
    ...   operation-defaults:
    ...     flags:
    ...       f1: 1
    ...       f2: 2
    ... - model: m
    ...   extends: base
    ...   operations:
    ...     op1: guild.pass
    ... """)

    >>> gf.default_model.operations
    [<guild.guildfile.OpDef 'm:op1'>]

    >>> op1 = gf.default_model.get_operation("op1")

    >>> [(f.name, f.default) for f in op1.flags]
    [('f1', 1), ('f2', 2)]

## Errors

### Invalid format

    >>> guildfile.for_dir(sample("projects/invalid-format"))
    Traceback (most recent call last):
    GuildfileError: error in .../samples/projects/invalid-format/guild.yml:
    invalid guildfile data 'This is invalid YAML!': expected a mapping

### No models (missing guild file)

    >>> guildfile.for_dir(sample("projects/missing-sources"))
    Traceback (most recent call last):
    NoModels: ...

A file not found error is Python version specific (FileNotFoundError
in Python 3 and IOError in Python 2) so we'll assert using exception
content.

    >>> try:
    ...   guildfile.for_file(sample("projects/missing-sources/guild.yml"))
    ... except IOError as e:
    ...   print(str(e))
    [Errno 2] No such file or directory: '.../projects/missing-sources/guild.yml'

### Missing required type attr

    >>> guildfile.for_string("""
    ... - foo: bar
    ... """)
    Traceback (most recent call last):
    GuildfileError: error in <string>: missing required type (one of: config,
    include, model, package) in {'foo': 'bar'}

### Implicit anonymous model

If a top-level item defines `operations` but does not provide a
required type attribute of `model` or `config`, Guild coerces the
object to an anomyous model - i.e. a model named with the empty
string.

    >>> gf = guildfile.for_string("""
    ... - operations:
    ...     test: guild.pass
    ... """)

    >>> gf.models
    {'': <guild.guildfile.ModelDef ''>}

    >>> gf.models[''].operations
    [<guild.guildfile.OpDef 'test'>]

    >>> gf.default_operation
    <guild.guildfile.OpDef 'test'>

### flags-import

    >>> guildfile.for_string("""
    ... op:
    ...   flags-import: hello
    ... """)
    Traceback (most recent call last):
    GuildfileError: error in <string>: invalid flags-import value 'hello':
    expected yes/all, no, or a list of flag names

### sourcecode

    >>> guildfile.for_string("""
    ... op:
    ...   sourcecode: 123
    ... """)
    Traceback (most recent call last):
    GuildfileError: error in <string>: invalid select files spec 123:
    expected a string, list, or mapping

### choices

    >>> guildfile.for_string("""
    ... op:
    ...   flags:
    ...     foo:
    ...       choices:
    ...         a: 1
    ... """)
    Traceback (most recent call last):
    GuildfileError: error in <string>: invalid flag choice data {'a': 1}:
    expected a list of values or mappings

NOTE: Using a single flag above to avoid inconsistencies in dict key
ordering across platforms.
