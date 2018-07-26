# Keras example models

Guild plugins can enumerate models when there is no modefile.

We can illustrate this using the Keras `mnist` example.

    >>> cd("examples/keras/mnist")

This example doesn't have a guildfile:

    >>> run("ls guild.yml")
    ls: ...guild.yml...: No such file or directory
    <exit ...>

However, we can still list locally defined models:

    >>> run("guild models .")
    ./mnist_irnn
    ./mnist_mlp
    <exit 0>

This list is derived from scripts in the working directory that the
keras plugin detects as valid Keras training scripts.

    >>> run("ls *.py | sort")
    mnist_irnn.py
    mnist_mlp.py
    <exit 0>

We can similarly list the supported operations for each model:

    >>> run("guild operations .")
    ./mnist_irnn:train  Train the model
    ./mnist_mlp:train   Train the model
    <exit 0>

Plugin defined models do not support resources, but we can still list
them.

    >>> run("guild resources .")
    <exit 0>

Without a guildfile directory filter, all models, operations, and
resources are listed:

    >>> run("guild models")
    ./mnist_irnn
    ./mnist_mlp
    hello/...
    <exit 0>

    >>> run("guild operations")
    ./mnist_irnn:train            Train the model
    ./mnist_mlp:train             Train the model
    hello/...
    <exit 0>

    >>> run("guild resources")
    hello/...
    <exit 0>
