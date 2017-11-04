# Evaluate MNIST intro example

Once an `mnist-intro` model is trained, we can run the `evaluate`
operation to test it against all of the test data.

    >>> cd("examples/mnist2")
    >>> run("guild run intro:evaluate -y")
    Resolving 'model' resource
    Resolving 'data' resource
    ...
    Extracting data/train-images-idx3-ubyte.gz
    ...
    Test accuracy=...
    <exit 0>
