# MNIST example resources

The MNIST example provides the following resources:

    >>> run("guild -C guild-examples/mnist2 resources")
    Limiting resources to 'guild-examples/mnist2' (use --all to include all)
    ./guild-examples/mnist2/mnist-expert:model  Exported expert model
    ./guild-examples/mnist2/mnist-intro:model   Exported intro model
    <exit 0>

The same list after changing directories:

    >>> cd("guild-examples/mnist2")
    >>> run("guild resources")
    Limiting resources to the current directory (use --all to include all)
    ./mnist-expert:model  Exported expert model
    ./mnist-intro:model   Exported intro model
    <exit 0>

And listing all resources with the `-a` option:

    >>> run("guild resources mnist -a")
    ./mnist-expert:model  Exported expert model
    ./mnist-intro:model   Exported intro model
    <exit 0>
