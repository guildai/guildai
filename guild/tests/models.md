# Models

Models play a central role in Guild commands. Models define the
operations that are performed by the `run` command. They are a
resource that can be discovered.

Models are managed using the `guild.model` module:

    >>> import guild.model

Models are discovered by looking for entry points in the
"guild.models" group. They can be discovered in the project directory
(either the current working directory or a location specified by the
user) or in Python distributions (i.e. installed packages).

To ensure our tests are consistent, we need to hack the `model`
module:

    >>> guild.model._models.limit_to_paths([
    ...   sample("projects/mnist"),
    ...   sample("models")])

We use `iter_models` to list all available models:

    >>> list(guild.model.iter_models())
    [('mnist', <guild.model.Model object ...>)]
