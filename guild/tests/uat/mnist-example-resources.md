# MNIST example resources

The MNIST example provides the following resources:

    >>> run("guild -C examples/mnist resources")
    ./examples/mnist/mnist-expert:model  Exported model
    ./examples/mnist/mnist-intro:model   Exported model
    gpkg.hello/...
    <exit 0>

The same list after changing directories:

    >>> cd("examples/mnist")
    >>> run("guild resources")
    ./mnist-expert:model  Exported model
    ./mnist-intro:model   Exported model
    gpkg.hello/...
    <exit 0>

We can limit resources to those defined in the current directory:

    >>> run("guild resources .")
    ./mnist-expert:model  Exported model
    ./mnist-intro:model   Exported model
    <exit 0>
