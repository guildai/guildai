# Uninstall `mnist` package

We can remove an installed package using `uninstall` (which is a
synonym for `packages delete`).

TODO: instate when uninstall is implemented:

    >> run("guild uninstall mnist")

    >>> run("guild packages ls -a mnist")
    mnist       ...
    pypi/mnist  ...
    <exit 0>

    >>> run("pip uninstall -y gpkg.mnist")
    Uninstalling gpkg.mnist-...:
    Successfully uninstalled gpkg.mnist-...
    <exit 0>

    >>> run("guild packages ls -a mnist")
    pypi/mnist  ...
    <exit 0>
