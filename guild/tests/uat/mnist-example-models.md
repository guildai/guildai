# MNIST example models

In this test we'll list the available models for the MNIST example. As
example directory contains a file named `MODELS` ("modelfile") Guild
limits its results to models defined in that file.

We can reference a modelfile in one of two ways:

- Change the current directory to the modelfile directory
- Using the `-C` option of the `guild` command to reference the
  modelfile drectory

Here are the models associated with the MNIST example (using the `-C`
option):

    >>> run("guild -C guild-examples/mnist2 models")
    Limiting models to 'guild-examples/mnist2' (use --all to include all)
    ./guild-examples/mnist2/mnist-expert  MNIST model from TensorFlow expert tutorial
    ./guild-examples/mnist2/mnist-intro   MNIST model from TensorFlow intro tutorial
    <exit 0>

Here's the same list after we've changed to that directory:

    >>> cd("guild-examples/mnist2")
    >>> run("guild models")
    Limiting models to the current directory (use --all to include all)
    ./mnist-expert  MNIST model from TensorFlow expert tutorial
    ./mnist-intro   MNIST model from TensorFlow intro tutorial
    <exit 0>

Note that Guild prints a message letting the user know the results are
limited. We can show all models, including those in the example
directory, using the `-a` option:

    >>> run("guild models -a")
    ./mnist-expert       MNIST model from TensorFlow expert tutorial
    ./mnist-intro        MNIST model from TensorFlow intro tutorial
    mnist/mnist-cnn      CNN classifier for MNIST
    mnist/mnist-softmax  Softmax regression classifier for MNIST
    <exit 0>
