---
doctest: -PY3 +PY36 +PY37 # 2022-04-11 these tests fail on github actions because TF 1.14 fails to install. We need to update to a more current tensorflow version that has wheels available.
---

# Create MNIST package

Guild packages are created using the `package` command. This command
is run within a directory with a guildfile containing a package
definition. It can also be run using the `-C` option.

For our tests we'll just run the command in the `mnist` package
directory:

    >>> cd("$WORKSPACE/packages/gpkg/mnist")
    >>> run("guild package", ignore=[
    ...     'Normalizing', 'normalized_version,',
    ...     'FutureWarning', 'Refreshing'])
    running bdist_wheel
    ...
    <exit 0>
