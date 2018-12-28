# Packages after `mnist` install

The `packages` command shows Guild packages (i.e. packages in the
`gpkg` namespace) by default. Here the list of currently installed
Guild packages:

    >>> run("guild packages")
    gpkg.mnist     0.6.0...  CNN and multinomial logistic regression classifiers for MNIST digits
    <exit 0>

Here's the list of all packages matching `mnist`:

    >>> run("guild packages ls -a mnist")
    gpkg.mnist  0.6.0...    CNN and multinomial logistic regression classifiers for MNIST digits
    mnist       0.2.2       Python utilities to download and parse the MNIST dataset
    <exit 0>
