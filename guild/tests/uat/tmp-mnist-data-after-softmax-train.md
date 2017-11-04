# Tmp MNIST data after softmax train

The `mnist-softmax` model uses a software library that downloads the
MNIST dataset to `/tmp/MNIST_data` by default. As the `mnist` package
is configured to use the IDX dataset resource provided by the
`mnist-dataset` package, we want to confirm that nothing was
downloaded to the default location.

    >>> run("find $TEMP/MNIST_data")
    find: ‘/.../MNIST_data’: No such file or directory
    <exit 1>
