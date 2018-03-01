# Run on missing default model

Guild supports running an operation without specifying a model
provided the operation is run on a guildfile that contains at least
one more (i.e. we can reasonably infer a model).

If there is no default model, Guild prints an error message and exits.

    >>> run("guild train")
    guild: a model is required for this operation
    Try 'guild operations' for a list of model-qualified operations
    <exit 1>

    >>> run("guild run train")
    guild: a model is required for this operation
    Try 'guild operations' for a list of model-qualified operations
    <exit 1>
