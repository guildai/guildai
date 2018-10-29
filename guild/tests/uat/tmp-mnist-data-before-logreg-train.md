# Tmp MNIST data before logreg train

The `logreg` model uses a software library that downloads the
MNIST dataset to `/tmp/MNIST_data` by default. As we'll be confirming
later that these files have not been downloaded to the temp location,
we need to check now and fail if they do.

    >>> run("find $TEMP/MNIST_data")
    find: .../MNIST_data...: No such file or directory
    <exit 1>

If this test fails, manually delete `$TEMP/MNIST_data` and re-run the
test.
