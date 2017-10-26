# MNIST example resources

The MNIST example provides the following resources:

    >>> run("guild -C guild-examples/mnist2 resources")
    Limiting resources to 'guild-examples/mnist2' (use --all to include all)
    ./guild-examples/mnist2/data  Yann Lecun's MNIST dataset in compressed IDX format
    <exit 0>

The same list after changing directories:

    >>> cd("guild-examples/mnist2")
    >>> run("guild resources")
    Limiting resources to the current directory (use --all to include all)
    ./data  Yann Lecun's MNIST dataset in compressed IDX format
    <exit 0>

And listing all resources with the `-a` option:

    >>> run("guild resources -a")
    ./data  Yann Lecun's MNIST dataset in compressed IDX format
    <exit 0>
