# Packages after `mnist` install

The `packages` command shows Guild packages (i.e. packages in the
`gpkg` namespace) by default. Here the list of currently installed
Guild packages:

    >>> run("guild packages")
    mnist          0.1.2.dev1  CNN and softmax regression classifiers for MNIST digits
    mnist-dataset  0.1.1.dev1  MNIST datasets
    <exit 0>

Note that `mnist-dataset` is also installed. This package is required
by `mnist` and was installed automatically as a dependency.

Here's the list of all packages matching `mnist`:

    >>> run("guild packages ls -a mnist")
    mnist          0.1.2.dev1  CNN and softmax regression classifiers for MNIST digits
    mnist-dataset  0.1.1.dev1  MNIST datasets
    pypi.mnist     ...         Python utilities to download and parse the MNIST dataset
    <exit 0>
