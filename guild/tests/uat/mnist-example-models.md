---
doctest: -PY3 +PY36 +PY37  # 2022-04-11 on python 3.8+, wheels are not available for h5py<3, so we fail to build. These tests can't currently pass on python 3.8+
---

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

    >>> run("guild -C %s models" % example("models"))
    mnist-expert  MNIST model from TensorFlow expert tutorial
    mnist-intro   MNIST model from TensorFlow intro tutorial
    <exit 0>

Note that the installed packages are not included in this list. This
is because the list is shown from the project directory. To include
installed packages, use the `-i, --installed` option:

    >>> run("guild -C %s models -i" % example("models"))
    gpkg.hello/...
    gpkg.keras.mnist/...
    mnist-expert  MNIST model from TensorFlow expert tutorial
    mnist-intro   MNIST model from TensorFlow intro tutorial
    <exit 0>

Here's the same list after we've changed to that directory:

    >>> cd(example("models"))
    >>> run("guild models")
    mnist-expert  MNIST model from TensorFlow expert tutorial
    mnist-intro   MNIST model from TensorFlow intro tutorial
    <exit 0>

And with installed models:

    >>> run("guild models -i")
    gpkg.hello/...
    gpkg.keras.mnist/...
    mnist-expert       MNIST model from TensorFlow expert tutorial
    mnist-intro        MNIST model from TensorFlow intro tutorial
    <exit 0>
