# Keras support

The plugin module:

    >>> from guild.plugins import keras

We'll use the `keras` project to illustrate Keras support.

    >>> project = sample("projects/keras")

## Keras model proxy

Keras support includes a model proxy, which is generated from a Keras
script.

    >>> script_path = os.path.join(project, "fashion_mnist_mlp.py")
    >>> model_proxy = keras.KerasScriptModelProxy(
    ...                   script_path, "fashion_mnist_mlp.py")

Model name:

    >>> model_proxy.modeldef.name
    ''

Operations:

    >>> model_proxy.modeldef.operations
    [<guild.guildfile.OpDef 'fashion_mnist_mlp.py'>]

Operation details:

    >>> opdef = model_proxy.modeldef.operations[0]

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

    # NOTE: As of 0.6.2 compare is None so that defaults are
    # applied at runtime.
    >>> print(opdef.compare)
    None

    >>> pprint(opdef.output_scalars) # doctest: -NORMALIZE_PATHS
    ['Epoch (?P<step>[0-9]+)',
     ' - ([a-z_]+): (\\value)',
     'Test loss: (?P<test_loss>\\value)',
     'Test accuracy: (?P<test_accuracy>\\value)']

## Keras model from Guild file

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

Compare colspecs:

    >>> print(opdef2.compare)
    None

    >>> opdef.compare == opdef2.compare
    True

Output scalars:

    >>> pprint(opdef2.output_scalars) # doctest: -NORMALIZE_PATHS
    ['Epoch (?P<step>[0-9]+)',
     ' - ([a-z_]+): (\\value)',
     'Test loss: (?P<test_loss>\\value)',
     'Test accuracy: (?P<test_accuracy>\\value)']

    >>> opdef.output_scalars == opdef2.output_scalars
    True
