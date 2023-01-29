---
doctest: -PY3 +PY37  # 2022-04-11 on python 3.8+, wheels are not available for h5py<3, so we fail to build. These tests can't currently pass on python 3.8+
---

# Packages after `mnist` install

The `packages` command shows Guild packages (i.e. packages in the
`gpkg` namespace) by default. Here the list of currently installed
Guild packages:

    >>> run("guild packages")
    gpkg.mnist  0.6.1  CNN and multinomial logistic regression classifiers for MNIST digits
    <exit 0>

Here's the list of all packages matching `mnist`:

    >>> run("guild packages ls -a mnist")
    gpkg.mnist  0.6.1    CNN and multinomial logistic regression classifiers for MNIST digits
    mnist       0.2.2    Python utilities to download and parse the MNIST dataset
    <exit 0>
