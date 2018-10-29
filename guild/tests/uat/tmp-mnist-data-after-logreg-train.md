# Tmp MNIST data after logreg train

The `logreg` model uses a software library that downloads the
MNIST dataset to `/tmp/MNIST_data` by default. As the `mnist` package
is configured to use the its `dataset` resource, we want to confirm
that nothing was downloaded to the default location.

    >>> run("find $TEMP/MNIST_data")
    find: .../MNIST_data...: No such file or directory
    <exit 1>
