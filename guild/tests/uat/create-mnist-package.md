# Create MNIST package

Guild packages are created using the `package` command. This command
is run within a directory with a guildfile containing a package
definition. It can also be run using the `-C` option.

For our tests we'll just run the command in the `mnist` package
directory:

    >>> cd("packages/gpkg/mnist")
    >>> run("guild package", ignore=[
    ...     'Normalizing', 'normalized_version,',
    ...     'FutureWarning', 'Refreshing'])
    running bdist_wheel
    ...
    <exit 0>
