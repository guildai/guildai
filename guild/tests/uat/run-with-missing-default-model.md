# Run on missing default model

Guild supports running an operation without specifying a model
provided the operation is run on a modelfile that contains at least
one more (i.e. we can reasonably infer a model).

If there is no default model, Guild prints an error message and exits.

    >>> run("guild train")
    guild: there are no models in the current directory
    Try a different directory or 'guild operations' for available operations.
    <exit 1>

    >>> run("guild run train")
    guild: there are no models in the current directory
    Try a different directory or 'guild operations' for available operations.
    <exit 1>
