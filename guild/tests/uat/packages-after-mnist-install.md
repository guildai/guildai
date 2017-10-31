# Packages after `mnist` install

The `packages` command shows Guild packages (i.e. packages in the
`gpkg` namespace) by default. Here the list of currently installed
Guild packages:

    >>> run("guild packages")
    mnist  ...
    <exit 0>

Here's the list of all packages (using the `-a` option with the
`packages` command):

    >>> run("guild packages ls -a mnist")
    mnist       ...
    pypi.mnist  ...
    <exit 0>
