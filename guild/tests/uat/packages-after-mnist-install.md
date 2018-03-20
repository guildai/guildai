# Packages after `mnist` install

The `packages` command shows Guild packages (i.e. packages in the
`gpkg` namespace) by default. Here the list of currently installed
Guild packages:

    >>> run("guild packages")
    mnist          0.3.1...  CNN and softmax regression classifiers for MNIST digits
    <exit 0>

Here's the list of all packages matching `mnist`:

    >>> run("guild packages ls -a mnist")
    mnist          0.3.1...  CNN and softmax regression classifiers for MNIST digits
    pypi.mnist     ...       Python utilities to download and parse the MNIST dataset
    <exit 0>
