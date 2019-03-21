# Train Keras example with missing dependency

When models are installed using Guild packages, their dependencies are
also installed (assuming the Guild package correctly specifies
them). In general though, users are responsible for resolving library
dependencies.

We can illustrate this with any of the Keras examples, which assume
the availability of Keras but can't otherwise satisfy the dependency.

Let's confirm that Keras is not installed.

    >>> run("python -c 'import keras'")
    Traceback (most recent call last):
    ...: No module named ...keras...
    <exit 1>

Let's next attempt to train a Keras example.

    >>> cd("examples/keras")
    >>> run("guild run -y mnist_irnn.py", timeout=10, ignore="Refreshing")
    Traceback (most recent call last):
    ...: No module named ...keras...
    <exit 1>
