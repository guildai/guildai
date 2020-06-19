# Batch runs - grid search

For our tests, we'll use the preview feature (print trials) to display
trial info rather than run actually run the operation. We'll use the
sample batch project script `add.py`.

    >>> project_dir = sample("projects", "batch")

Here's a helper function:

    >>> from guild import _api as gapi
    >>> def print_trials(max_trials=None, random_seed=None,
    ...                  capture=False, optimizer=None, **flags):
    ...   try:
    ...     output = gapi.run_capture_output(
    ...       "add.py",
    ...       cwd=project_dir,
    ...       flags=flags,
    ...       max_trials=max_trials,
    ...       random_seed=random_seed,
    ...       optimizer=optimizer,
    ...       print_trials=True)
    ...   except gapi.RunError as e:
    ...     if capture:
    ...       return e
    ...     print("ERROR (%i)" % e.returncode)
    ...     print(e.output)
    ...   else:
    ...     if capture:
    ...       return output.strip()
    ...     print(output.strip())

If we try to print trials for a non-batch run, we get an error.

    >>> print_trials(x=1, y=1, z=1)
    ERROR (1)
    guild: cannot print trials for a non-batch operation

## Basic grid search

Guild generates trials consisting of the cartesian product of the
specified flags.

    >>> print_trials(x=[1,2], y=[3,4], z=[5,6])
    #  x  y  z
    1  1  3  5
    2  1  3  6
    3  1  4  5
    4  1  4  6
    5  2  3  5
    6  2  3  6
    7  2  4  5
    8  2  4  6

## Grid search with random flag functions

Guild defaults to 'random' optimizer when the user specifies a flag
function specifying a random distribution.

    >>> print_trials(x="[1:1000]", y=[1,2], z=[3,4])
    #   x    y  z
    1   ...
    2   ...
    3   ...
    ...
    19  ...
    20  ...

In this case, Guild generates the default number of trials and uses
list values for `y` and `z` as category spaces to select from.

However, if we force the optimizer to be '+', we run a grid search
where flag functions are used to provide randomly generated values for
each trial.

    >>> print_trials(x="[1:1000]", y=[1,2], z=[3,4], optimizer="+")
    #  x    y  z
    1  ...  1  3
    2  ...  1  4
    3  ...  2  3
    4  ...  2  4

We can specify a random seed to ensure that we get a consistent result
on a given system.

    >>> out1 = print_trials(x="[1:1000]", y=[1,2], z=[3,4], optimizer="+",
    ...                     random_seed=43, capture=True)

    >>> out2 = print_trials(x="[1:1000]", y=[1,2], z=[3,4], optimizer="+",
    ...                     random_seed=43, capture=True)

    >>> out1 == out2, out1, out2
    (True, ..., ...)

## Max runs and grid search

Guild typically limits trials to 20. However, grid search is not
limited to 20 unless `--max-trials` is specified explicitly.

    >>> print_trials(x=[1,2,3], y=[1,2,3], z=[1,2,3])
    #   x  y  z
    1   1  1  1
    2   1  1  2
    3   1  1  3
    ...
    26  3  3  2
    27  3  3  3

The number of generated trials can be limited using the `--max-trials`
run option. If the max is less than the number of generated trials,
Guild selects trials at random to omit to stay within the specified
maximum.

    >>> print_trials(x=[1,2], y=[3,4], z=[5,6], max_trials=2)
    #  x  y  z
    1  ...
    2  ...

In this case, we generate two trials but we don't know which ahead of
time because they are randomly selected using a randomly generated
seed.

We can provide a random seed to ensure consistent trial selection. The
results are consistent only within the same implementation of Python's
random.sample function. We can use a generalized test to demonstrate,
but we can run the preview twice using the same seed and compare the
results.

    >>> out1 = print_trials(x=[1,2], y=[3,4], z=[5,6], max_trials=2,
    ...                     random_seed=1, capture=True)

    >>> out2 = print_trials(x=[1,2], y=[3,4], z=[5,6], max_trials=2,
    ...                     random_seed=1, capture=True)

    >>> out1 == out2, out1, out2
    (True, ..., ...)
