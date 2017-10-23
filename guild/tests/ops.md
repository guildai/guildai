# Operations

Operation support is implemented by the `op` module:

    >>> import guild.op

For our tests, we'll use a helper function that returns an instance of
guild.project.Operation:

    >>> import guild.modelfile

    >>> def ProjectOp(cmd, name="op"):
    ...     data = [
    ...       {
    ...         "name": "model",
    ...         "operations": {
    ...           name: {
    ...             "cmd": cmd
    ...           }
    ...         }
    ...       }
    ...     ]
    ...     models = guild.modelfile.Modelfile(data, "./MODEL")
    ...     return models["model"].get_op(name)

We'll also create a helper function that returns and instance of
guild.op.Operation given arguments to ProjectOp:

    >>> def Operation(*args, **kw):
    ...     return guild.op.from_opdef(ProjectOp(*args, **kw), "test")

Note that the `"test"` argument is an operation reference, which is
not used in our tests.

## Command specs

Command specs are used to generate Python commands. The first part of
the spec is used as the Python script or module. It can be a module
name with or without a py extension.

Here's an operation with a simple "train" cmd:

    >>> op = Operation(cmd="train")
    >>> op.cmd_args
    ['python', '-um', 'guild.op_main', 'train']

Command specs may contain additional arguments, which will be included
in the Python command.

    >>> op = Operation(cmd="train epoch=10 tags='tag1 tag2'")
    >>> op.cmd_args
    ['python', '-um', 'guild.op_main', 'train', 'epoch=10', 'tags=tag1 tag2']

Command specs cannot be empty:

    >>> Operation(cmd="")
    Traceback (most recent call last):
    InvalidCmd

## Flag args

Flags are defined in MODEL files and provided as command line
arguments to the run command. `flag_args` returns a list of command
line arg for a map of flag values.

Empty flags:

    >>> guild.op._flag_args({})
    []

Single flag:

    >>> guild.op._flag_args({"epochs": 100})
    ['--epochs', '100']

Multiple flags are returned in sorted order:

    >>> guild.op._flag_args({"epochs": 100, "data": "my-data"})
    ['--data', 'my-data', '--epochs', '100']

Flag options (i.e. options with implicit values) may be specified with
None values:

    >>> guild.op._flag_args({"test": None, "batch-size": 50})
    ['--batch-size', '50', '--test']

## Operation flags

Operation flags may be defined in two places:

- Within the operation itself
- Within the operation model

Flags defined in the operation override flags defined in the model.

For our tests we'll use the train operation:

    >>> project_op = ProjectOp("train")

We can get the flags defined for this op using the `all_flag_values`
method:

    >>> project_op.all_flag_values()
    {}

Our sample operations aren't initialized with any flags, so we expect
this list to be empty.

Let's add some flags, starting with the operation model. We'll use the
`set_flag_value` method:

    >>> project_op.modeldef.set_flag_value("epochs", 100)

And now enumerate flag values for the operation:

    >>> project_op.all_flag_values()
    {'epochs': 100}

Let's define the same flag at the operation level:

    >>> project_op.set_flag_value("epochs", 200)
    >>> project_op.all_flag_values()
    {'epochs': 200}

Here are a couple additional flags, one defined in the model and the
other in the operations:

    >>> project_op.set_flag_value("batch-size", 50)
    >>> project_op.modeldef.set_flag_value("learning-rate", 0.1)
    >>> pprint(project_op.all_flag_values())
    {'batch-size': 50,
     'epochs': 200,
     'learning-rate': 0.1}
