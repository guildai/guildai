# MNIST initial runs

Regardless of the working directory, all runs for an environment are
listed.

Here are the runs from previous tests:

    >>> run("guild -C examples/mnist2 runs")
    [0:...]  keras.mnist/mnist-mlp:train   ...  completed
    ...
    [6:...]  mnist/mnist-softmax:train     ...  completed
    <exit 0>

We can alternatively change to that directory and see the same results:

    >>> cd("examples/mnist2")
    >>> run("guild runs")
    [0:...]  keras.mnist/mnist-mlp:train   ...  completed
    ...
    [6:...]  mnist/mnist-softmax:train     ...  completed
    <exit 0>
