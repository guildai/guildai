# MNIST example resources

The MNIST example provides the following resources:

    >>> run("guild -C examples/mnist2 resources", ignore="FutureWarning")
    Limiting resources to 'examples/mnist2' (use --all to include all)
    ./examples/mnist2/mnist-expert:model  Exported model
    ./examples/mnist2/mnist-intro:model   Exported model
    <exit 0>

The same list after changing directories:

    >>> cd("examples/mnist2")
    >>> run("guild resources", ignore="FutureWarning")
    Limiting resources to the current directory (use --all to include all)
    ./mnist-expert:model  Exported model
    ./mnist-intro:model   Exported model
    <exit 0>

And listing all resources with the `-a` option:

    >>> run("guild resources mnist -a", ignore="FutureWarning")
    ./mnist-expert:model  Exported model
    ./mnist-intro:model   Exported model
    <exit 0>
