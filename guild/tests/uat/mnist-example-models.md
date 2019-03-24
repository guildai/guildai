# MNIST example models

In this test we'll list the available models for the MNIST example. As
example directory contains a file named `guild.yml` ("guildfile")
Guild includes models from that directory, as well as globally
installed models.

We can reference a guildfile in one of two ways:

- Change the current directory to the guildfile directory
- Using the `-C` option of the `guild` command to reference the
  guildfile drectory

Here are the models associated with the MNIST example (using the `-C`
option):

    >>> run("guild -C examples/mnist models", ignore="Refreshing")
    ./examples/mnist/mnist-expert  MNIST model from TensorFlow expert tutorial
    ./examples/mnist/mnist-intro   MNIST model from TensorFlow intro tutorial
    gpkg.hello/...
    gpkg.keras.mnist/...
    <exit 0>

Here's the same list after we've changed to that directory:

    >>> cd("examples/mnist")
    >>> run("guild models")
    gpkg.hello/...
    gpkg.keras.mnist/...
    mnist-expert  MNIST model from TensorFlow expert tutorial
    mnist-intro   MNIST model from TensorFlow intro tutorial
    <exit 0>

We can limit the results to model defined in the current directory by
specifying it as a path filter:

    >>> run("guild models -p .")
    mnist-expert       MNIST model from TensorFlow expert tutorial
    mnist-intro        MNIST model from TensorFlow intro tutorial
    <exit 0>
