# Batch runs - part 2

[Part 1](batch-1.md) illustrated basic grid search. These tests look
at the random search features of Guild batch runs.

There are two applications of random search in Guild's batch facility:

- Random trials selected when runs are limited
- Flag distribution values

## Max runs and random search

When Guild runs a batch, it generates trials by computing the
cartesian product of flag list values. This is illustrated in detail
in [Part 1](batch-1.md).

The number of generated trials can be limited using the `--max-runs`
run option. If the max runs is less than the number of generated
trials, Guild will select at random trials to omit in order to stay
within the specified maximum.

For our tests, we'll use the preview feature (print trials) to display
trial info rather than run actually run the operation. We'll use the
sample batch project script `add.py`.

    >>> project = sample("projects", "batch")

Here's a helper function:

    >>> from guild import _api as gapi

    >>> def trials(max=None, random_seed=None, **flags):
    ...   try:
    ...     output = gapi.run_capture_output(
    ...       "add.py", cwd=project, flags=flags,
    ...       max_trials=max, random_seed=random_seed,
    ...       print_trials=True)
    ...   except gapi.RunError as e:
    ...     print("ERROR (%i)" % e.returncode)
    ...     print(e.output)
    ...   else:
    ...     print(output.strip())

Here are the trials for a single run:

    >>> trials(x=1, y=1, z=1)
    #  x  y  z
    1  1  1  1

And many trials:

    >>> trials(x=[1,2], y=[3,4], z=[5,6])
    #  x  y  z
    1  1  3  5
    2  1  3  6
    3  1  4  5
    4  1  4  6
    5  2  3  5
    6  2  3  6
    7  2  4  5
    8  2  4  6

It's easy to generate experiments!

We can limit the number of experiments with the `max` arg:

    >>> trials(x=[1,2], y=[3,4], z=[5,6], max=2)
    #  x  y  z
    1  ...
    2  ...

In this case, we generate two trials (the max) but we don't know which
ahead of time because they are randomly selected using a randomly
generated seed.

We can know the trials ahead of time by providing our own random seed:

    >>> trials(x=[1,2], y=[3,4], z=[5,6], max=2, random_seed=1)
    #  x  y  z
    1  1  3  6
    2  2  3  6
