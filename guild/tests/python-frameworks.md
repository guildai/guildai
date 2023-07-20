# Python Frameworks

The `python_frameworks` module provides support for various Python
frameworks.

    >>> from guild.plugins import python_frameworks

## Keras

We'll use the `keras` project to illustrate Keras support.

    >>> project = sample("projects/keras")

### Keras model proxy

The frameworks plugin detects Keras training or prediction scripts.

    >>> script_path = os.path.join(project, "fashion_mnist_mlp.py")
    >>> model = python_frameworks.model_for_script(script_path)

Model name:

    >>> model.modeldef.name
    ''

Operations:

    >>> model.modeldef.operations
    [<guild.guildfile.OpDef 'fashion_mnist_mlp.py'>]

Operation details:

    >>> opdef = model.modeldef.operations[0]

    >>> opdef.flags
    [<guild.guildfile.FlagDef 'batch_size'>,
     <guild.guildfile.FlagDef 'dropout'>,
     <guild.guildfile.FlagDef 'epochs'>,
     <guild.guildfile.FlagDef 'lr'>,
     <guild.guildfile.FlagDef 'lr_decay'>]

    >>> pprint(opdef.flag_values())
    {'batch_size': 128,
     'dropout': 0.2,
     'epochs': 5,
     'lr': 0.001,
     'lr_decay': 0.0}

The primary function of the Keras support is to apply output scalar
patterns that match Keras output. In addition, Keras supports default
output scalar patterns so the user can log custom metrics.

    >>> pprint(opdef.output_scalars) # doctest: -NORMALIZE_PATHS
    ['Epoch (?P<step>[0-9]+)',
     ' - ([a-z_]+): (\\value)',
     'Test loss: (?P<test_loss>\\value)',
     'Test accuracy: (?P<test_accuracy>\\value)',
     '^\\key:\\s+\\value\\s+\\((?:step\\s+)?(?P<step>\\step)\\)$',
     '^(\\key):\\s+(\\value)(?:\\s+\\(.*\\))?$']

### Keras model from Guild file

The Guild file in `project` reference `fashion_mnist_fashion.py` as
`main` for the `train` operation.

    >>> from guild import guildfile

    >>> gf = guildfile.for_dir(project)

    >>> gf.models
    {'fashion': <guild.guildfile.ModelDef 'fashion'>}

    >>> model = gf.models["fashion"]
    >>> model.operations
    [<guild.guildfile.OpDef 'fashion:train'>]

    >>> opdef2 = model.operations[0]
    >>> opdef2.name
    'train'
    >>> opdef2.main
    'fashion_mnist_mlp'

While the file itself does define any flags, compare, or output scalar
defs, each of these are imported from the module - each mirrors the
values provided by the Keras script model proxy above.

Flag defs:

    >>> opdef2.flags
    [<guild.guildfile.FlagDef 'batch_size'>,
     <guild.guildfile.FlagDef 'dropout'>,
     <guild.guildfile.FlagDef 'epochs'>,
     <guild.guildfile.FlagDef 'lr'>,
     <guild.guildfile.FlagDef 'lr_decay'>]

Flag vals:

    >>> pprint(opdef2.flag_values())
    {'batch_size': 128,
     'dropout': 0.2,
     'epochs': 5,
     'lr': 0.001,
     'lr_decay': 0.0}

    >>> opdef.flag_values() == opdef2.flag_values()
    True

As in the case of the Python script, Keras support detects the use of
Keras in a main module and applies the applicable output scalars to
the op def.

    >>> pprint(opdef2.output_scalars) # doctest: -NORMALIZE_PATHS
    ['Epoch (?P<step>[0-9]+)',
     ' - ([a-z_]+): (\\value)',
     'Test loss: (?P<test_loss>\\value)',
     'Test accuracy: (?P<test_accuracy>\\value)',
     '^\\key:\\s+\\value\\s+\\((?:step\\s+)?(?P<step>\\step)\\)$',
     '^(\\key):\\s+(\\value)(?:\\s+\\(.*\\))?$']

    >>> opdef.output_scalars == opdef2.output_scalars
    True
