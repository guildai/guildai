# Run on missing default model

Guild supports running an operation without specifying a model
provided the operation is run on a guildfile that contains at least
one more (i.e. we can reasonably infer a model).

If there is no default model, Guild prints an error message and exits.

    >>> run("guild run train")
    guild: cannot find operation train
    You may need to include a model in the form MODEL:OPERATION.
    Try 'guild operations' for a list of available operations.
    <exit 1>
