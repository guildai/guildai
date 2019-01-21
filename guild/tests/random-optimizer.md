# Random optimizer

These tests illustrate the behavior of the random search optimizer.

The random optimizer isn't technically an optimizer as it generates
random trials without respect to an objective. It's useful however for
general exploration.

We'll use the `optimizers` project, which provides test operations for
use with optimizers.

    >>> project = sample("projects", "optimizers")



    >>> def trials(op, **flags):
    ...   print("whoop")
