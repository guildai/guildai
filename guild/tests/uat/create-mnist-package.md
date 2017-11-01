# Create MNIST package

Guild packages are created using the `package` command. This command
is commonly run within a directory containing a `PACKAGE` file, but it
can also be run using the `-C` option.

For our tests we'll just run the command in the `mnist` package
directory:

    >>> cd("guild-packages/mnist")
    >>> run("guild package", ignore=['Normalizing', 'normalized_version,'])
    running bdist_wheel
    ...
    <exit 0>
