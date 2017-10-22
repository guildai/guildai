# MNIST example models

    >>> cd("guild-examples/mnist2")

The models in the MNIST example include:

    >>> run("guild models")
    Limiting models to the current directory (use --all to include all)
    ./mnist-expert  MNIST model from TensorFlow expert tutorial
    ./mnist-intro   MNIST model from TensorFlow intro tutorial
    <exit 0>

If we use the -a option, we can see all the models:

    >>> run("guild models -a")
    ./mnist-expert       MNIST model from TensorFlow expert tutorial
    ./mnist-intro        MNIST model from TensorFlow intro tutorial
    mnist/mnist-cnn      CNN classifier for MNIST
    mnist/mnist-softmax  Softmax regression classifier for MNIST
    <exit 0>
