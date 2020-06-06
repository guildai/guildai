# MNIST example ops

Available operations are listed using the `operations` command (or
`ops` for short). This command follows the same pattern used by
`models`, which is to limit results to a modefile when the command is
applied to a directory containing a file named `guild.yml`.

For more information on this logic, see
[mnist-example-models.md](mnist-example-models.md).

In this test, we'll limit our operations by changing the current
directory to the MNIST example:

    >>> cd(example("models"))

The ops available in this context example are:

    >>> run("guild ops")
    mnist-expert:evaluate  Evaluate a trained model using test data
    mnist-expert:train     Train the MNIST model
    mnist-intro:evaluate   Evaluate a trained model using test data
    mnist-intro:train      Train the MNIST model
    <exit 0>

As with models, operations are limited to those available in the
project when shown from the project directory. To include installed
operations as well, use the `-i, --installed` option:

    >>> run("guild ops -i")
    gpkg.hello/...
    gpkg.keras.mnist/...
    mnist-expert:evaluate    Evaluate a trained model using test data
    mnist-expert:train       Train the MNIST model
    mnist-intro:evaluate     Evaluate a trained model using test data
    mnist-intro:train        Train the MNIST model
    <exit 0>
