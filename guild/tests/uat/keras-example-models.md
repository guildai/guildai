# Keras example models

Guild plugins can enumerate models when there is no modefile.

We can illustrate this using the Keras `mnist` example.

    >>> cd("examples/keras/mnist")

This example doesn't have a modelfile:

    >>> run("ls MODEL*")
    ls: cannot access 'MODEL*': No such file or directory
    <exit 2>

However, we can still list locally defined models:

    >>> run("guild models")
    Limiting models to the current directory (use --all to include all)
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

    >>> run("guild operations")
    Limiting models to the current directory (use --all to include all)
    ./mnist_irnn:train  Train the model
    ./mnist_mlp:train   Train the model
    <exit 0>

Plugin defined models do not support resources, but we can still list
them.

    >>> run("guild resources")
    Limiting resources to the current directory (use --all to include all)
    <exit 0>

As with other locally defined models, we can extend our lists using
the `-a` flag.

    >>> run("guild models -a")
    ./mnist_irnn
    ./mnist_mlp
    hello/...
    <exit 0>

    >>> run("guild operations -a")
    ./mnist_irnn:train            Train the model
    ./mnist_mlp:train             Train the model
    hello/...
    <exit 0>

    >>> run("guild resources -a")
    hello/...
    <exit 0>
