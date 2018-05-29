# MNIST example resources

The MNIST example provides the following resources:

    >>> run("guild -C examples/mnist2 resources", ignore="FutureWarning")
    ./examples/mnist2/mnist-expert:model  Exported model
    ./examples/mnist2/mnist-intro:model   Exported model
    hello/...
    <exit 0>

The same list after changing directories:

    >>> cd("examples/mnist2")
    >>> run("guild resources", ignore="FutureWarning")
    ./mnist-expert:model  Exported model
    ./mnist-intro:model   Exported model
    hello/...
    <exit 0>

We can limit resources to those defined in the current directory:

    >>> run("guild resources .", ignore="FutureWarning")
    ./mnist-expert:model  Exported model
    ./mnist-intro:model   Exported model
    <exit 0>
