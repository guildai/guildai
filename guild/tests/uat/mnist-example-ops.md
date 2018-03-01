# MNIST example ops

Available operations are listed using the `operations` command (or
`ops` for short). This command follows the same pattern used by
`models`, which is to limit results to a modefile when the command is
applied to a directory containing a file named `guild.yml`.

For more information on this logic, see
[mnist-example-models.md](mnist-example-models.md).

In this test, we'll limit our operations by changing the current
directory to the MNIST example:

    >>> cd("examples/mnist2")

The ops available in this context example are:

    >>> run("guild ops")
    Limiting models to the current directory (use --all to include all)
    ./mnist-expert:evaluate  Evaluate a trained model using test data
    ./mnist-expert:train     Train the MNIST model
    ./mnist-intro:evaluate   Evaluate a trained model using test data
    ./mnist-intro:train      Train the MNIST model
    <exit 0>

Note that Guild prints a message letting the user know the results are
limited.

We can view all ops using -a:

    >>> run("guild ops -a")
    ./mnist-expert:evaluate    Evaluate a trained model using test data
    ./mnist-expert:train       Train the MNIST model
    ./mnist-intro:evaluate     Evaluate a trained model using test data
    ./mnist-intro:train        Train the MNIST model
    hello/...
    keras.mnist/...
    <exit 0>
