# MNIST example runs after intro train

Once we've trained the MNIST intro example, we can see an associated
run:

    >>> run("guild runs")
    [0:...]  ./examples/mnist/mnist-intro:train  ... ...  completed
    [1:...]  gpkg.mnist/mnist-softmax:train      ... ...  completed
    <exit 0>

Here we see the run for the MNIST example `mnist-intro` model along
with a run for the `mnist` package `mnist-softmax` model.

We can limit the result by running the command in the context of the
example guildfile directory:

    >>> run("guild -C examples/mnist runs")
    [0:...]  ./mnist-intro:train  ... ...  completed
    <exit 0>

We can alternatively change to the example directory and see the run
without having to specify the `-C` option:

    >>> cd("examples/mnist")
    >>> run("guild runs")
    [0:...]  ./mnist-intro:train  ... ...  completed
    <exit 0>

Note that Guild prints a message letting the user know the results are
limited.

To show all runs within the current context, we can use the `-a`
option:

    >>> run("guild runs -a")
    [0:...]  ./mnist-intro:train             ... ...  completed
    [1:...]  gpkg.mnist/mnist-softmax:train  ... ...  completed
    <exit 0>
