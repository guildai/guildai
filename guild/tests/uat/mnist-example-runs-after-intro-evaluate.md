# MNIST example runs after intro evaluate

After running `evaluate` on `mnist-intro` we get a second run.

    >>> cd(example("models"))

    >>> run("guild runs --limit 2")
    [1:...]  mnist-intro:evaluate  ... ...  completed  train=...
    [2:...]  mnist-intro:train     ... ...  completed  batch-size=100 epochs=1 lr=0.5
    <exit 0>
