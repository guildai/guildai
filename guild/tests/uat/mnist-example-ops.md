# MNIST example ops

    >>> cd("guild-examples/mnist2")

The ops defined in the MNIST example are:

    >>> run("guild ops")
    Limiting models to the current directory (use --all to include all)
    ./mnist-expert:evaluate  Evaluate a trained model using test data
    ./mnist-expert:prepare   Prepare the MNIST data for training
    ./mnist-expert:train     Train the MNIST model
    ./mnist-intro:evaluate   Evaluate a trained model using test data
    ./mnist-intro:prepare    Prepare the MNIST data for training
    ./mnist-intro:test       A test operations
    ./mnist-intro:train      Train the MNIST model
    <exit 0>

We can view all ops using -a:

    >>> run("guild ops -a")
    ./mnist-expert:evaluate    Evaluate a trained model using test data
    ./mnist-expert:prepare     Prepare the MNIST data for training
    ./mnist-expert:train       Train the MNIST model
    ./mnist-intro:evaluate     Evaluate a trained model using test data
    ./mnist-intro:prepare      Prepare the MNIST data for training
    ./mnist-intro:test         A test operations
    ./mnist-intro:train        Train the MNIST model
    mnist/mnist-cnn:train      Train the CNN
    mnist/mnist-softmax:train  Train the softmax regression
    <exit 0>
