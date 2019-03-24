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
    ...                   "fashion_mnist_mlp.py", script_path)

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

    >>> opdef.compare
    ['=batch_size',
     '=dropout',
     '=epochs',
     '=lr',
     '=lr_decay',
     'loss step as step',
     'loss',
     'acc',
     'val_loss',
     'val_acc']

    >>> pprint(opdef.output_scalars)
    {'acc': 'acc: ([0-9\\.]+) - val_loss',
     'loss': 'step - loss: ([0-9\\.]+)',
     'step': 'Epoch ([0-9]+)/[0-9]+',
     'val_acc': 'val_acc: ([0-9\\.]+)',
     'val_loss': 'val_loss: ([0-9\\.]+)'}

## Keras model from Guild file

The Guild file in `project` reference `fashion_mnist_fashion.py` as
`main` for the `train` operation.

    >>> from guild import guildfile

    >>> gf = guildfile.from_dir(project)

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

    >>> opdef2.compare
    ['=batch_size',
     '=dropout',
     '=epochs',
     '=lr',
     '=lr_decay',
     'loss step as step',
     'loss',
     'acc',
     'val_loss',
     'val_acc']

    >>> opdef.compare == opdef2.compare
    True

Output scalars:

    >>> pprint(opdef2.output_scalars)
    {'acc': 'acc: ([0-9\\.]+) - val_loss',
     'loss': 'step - loss: ([0-9\\.]+)',
     'step': 'Epoch ([0-9]+)/[0-9]+',
     'val_acc': 'val_acc: ([0-9\\.]+)',
     'val_loss': 'val_loss: ([0-9\\.]+)'}

    >>> opdef.output_scalars == opdef2.output_scalars
    True
