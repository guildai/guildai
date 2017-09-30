# Operations

Operation support is implemented by the `op` module:

    >>> import guild.op

For our tests, we'll use a helper function that returns an instance of
guild.project.Operation:

    >>> import guild.project

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
    ...     project = guild.project.Project(data, "./MODEL")
    ...     return project["model"].get_op(name)

We'll also create a helper function that returns and instance of
guild.op.Operation given arguments to ProjectOp:

    >>> def Operation(*args, **kw):
    ...     return guild.op.from_project_op(ProjectOp(*args, **kw))

## Command specs

Command specs are used to generate Python commands. The first part of
the spec is used as the Python script or module. It can be a module
name with or without a py extension.

Here's an operation with a simple "train" cmd:

    >>> op = Operation(cmd="train")
    >>> op._cmd_args
    ['python', '-u', './train']

Command specs may contain additional arguments, which will be included
in the Python command.

    >>> op = Operation(cmd="train epoch=10 tags='tag1 tag2'")
    >>> op._cmd_args
    ['python', '-u', './train', 'epoch=10', 'tags=tag1 tag2']

Command specs cannot be empty:

    >>> Operation(cmd="")
    Traceback (most recent call last):
    InvalidCmdSpec
