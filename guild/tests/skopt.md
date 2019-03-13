# Scikit optimize

Before running tests with the `skopt` module, let's silence the
warnings from `numpy.core.umath_tests`:

    >>> import warnings
    >>> warnings.filterwarnings("ignore", category=Warning)
    >>> import numpy.core.umath_tests

## Bayesian optimization

Support for Bayesian optimization is provided by `gp_minimize`
function:

    >>> from skopt import gp_minimize

Here's a case where we provide a list of x0 and corresponding
y0. These are flag values and resulting objective values respectively.

    >>> res = gp_minimize(
    ...     func=lambda *args: 0,
    ...     dimensions=[(-2.0, 2.0)],
    ...     n_calls=1,
    ...     n_random_starts=0,
    ...     x0=[[-1.0], [0.0], [1.0]],
    ...     y0=[-1.0, 0.0, 1.0],
    ...     random_state=66)

    >>> res.x_iters
    [[-1.0], [0.0], [1.0], [-2.0]]

In this case we want a random value, so we ask for one call and one
random start.

    >>> res = gp_minimize(
    ...     func=lambda *args: 0,
    ...     dimensions=[(-2.0, 2.0)],
    ...     n_calls=1,
    ...     n_random_starts=1,
    ...     x0=None,
    ...     y0=None,
    ...     random_state=66)

    >>> x0 = res.x_iters[0][0]
    >>> x0 >= -2.0 and x0 <= 2.0, x0
    (True, ...)

Here's a case where we don't have any prior information and so use a
known start value for x0.

    >>> res = gp_minimize(
    ...     func=lambda *args: 0,
    ...     dimensions=[(-2.0, 2.0)],
    ...     n_calls=1,
    ...     n_random_starts=0,
    ...     x0=[-1.0],
    ...     y0=None,
    ...     random_state=66)

    >>> res.x_iters
    [[-1.0]]

Case where we want to use a default flag value and randomly generate a
value for a second flag.

    >>> res = gp_minimize(
    ...     func=lambda *args: 0,
    ...     dimensions=[[1.0], (-2.0, 2.0)],
    ...     n_calls=1,
    ...     n_random_starts=1,
    ...     x0=None,
    ...     y0=None,
    ...     random_state=66)

    >>> res.x_iters
    [[1.0, ...]]

    >>> x0_1 = res.x_iters[0][1]
    >>> x0_1 >= -2.0 and x0_1 <= 2.0, x0_1
    (True, ...)

Case where we have a single x0 rather than 3.

    >>> res = gp_minimize(
    ...     func=lambda *args: 0,
    ...     dimensions=[(-2.0, 2.0)],
    ...     n_calls=1,
    ...     n_random_starts=0,
    ...     x0=[[0.2]],
    ...     y0=[0],
    ...     random_state=66)

    >>> res.x_iters
    [[0.2], [...]]

    >>> x1 = res.x_iters[1][0]
    >>> x1 >= -2.0 and x1 <= 2.0, x1
    (True, ...)

## Repeating trials

This fragment demonstrates that gp_minimimize repeats trials.

    >>> res = gp_minimize(
    ...     lambda xs: xs[0],
    ...     [(-2.0, 2.0)],
    ...     n_calls=10,
    ...     n_random_starts=1,
    ...     random_state=1)
    >>> trials = [iter[0] for iter in res.x_iters]
    >>> unique_trials = set(trials)
    >>> len(trials) > len(unique_trials), trials
    (True, ...)

However, random forest does not:

    >>> from skopt import forest_minimize

    >>> res = forest_minimize(
    ...     lambda xs: xs[0],
    ...     [(-2.0, 2.0)],
    ...     n_calls=10,
    ...     n_random_starts=1,
    ...     random_state=1)
    >>> trials = [iter[0] for iter in res.x_iters]
    >>> unique_trials = set(trials)
    >>> len(trials) == len(unique_trials), trials
    (True, ...)

Nor does gbrt:

    >>> from skopt import gbrt_minimize

    >>> res = gbrt_minimize(
    ...     lambda xs: xs[0],
    ...     [(-2.0, 2.0)],
    ...     n_calls=10,
    ...     n_random_starts=1,
    ...     random_state=1)
    >>> trials = [iter[0] for iter in res.x_iters]
    >>> unique_trials = set(trials)
    >>> len(trials) == len(unique_trials), trials
    (True, ...)

## Minimizing objective

Let's use the bayesian optimizer to minimize loss for the `echo`
operation. Loss in this case is simply the value of `x` that we
specify.

    >>> project = Project(sample("projects", "optimizers"))

And the run:

    >>> project.run("echo", flags={"x": "[-2.0:2.0:0.0]", "z": "a"},
    ...             optimizer="gp",
    ...             minimize="loss",
    ...             random_seed=1,
    ...             max_trials=4)
    INFO: [guild] Found 0 previous trial(s) for use in optimization
    INFO: [guild] Initialized trial ... (x=0.0, y=2, z=a)
    INFO: [guild] Running trial ...: echo (x=0.0, y=2, z=a)
    0.0 2 'a'
    INFO: [guild] Found 1 previous trial(s) for use in optimization
    INFO: [guild] Initialized trial ... (x=..., y=2, z=a)
    INFO: [guild] Running trial ...: echo (x=..., y=2, z=a)
    ... 2 'a'
    INFO: [guild] Found 2 previous trial(s) for use in optimization...
    INFO: [guild] Initialized trial ... (x=..., y=2, z=a)
    INFO: [guild] Running trial ...: echo (x=..., y=2, z=a)
    ... 2 'a'
    INFO: [guild] Found 3 previous trial(s) for use in optimization...
    INFO: [guild] Initialized trial ... (x=-..., y=2, z=a)
    INFO: [guild] Running trial ...: echo (x=..., y=2, z=a)
    ... 2 'a'

Let's get the loss for the latest run:

    >>> latest_run = project.list_runs()[0]
    >>> loss = project.run_scalar(latest_run, None, "loss", "last", False)
    >>> isinstance(loss, float) and loss < 0, loss, latest_run.path
    (True, ...)

## Maximizing objective

While we generally don't want to maximize loss, let's run the same
operation with maximize:

    >>> project.run("echo", flags={"x": "[-2.0:2.0:0.0]", "z": "a"},
    ...             optimizer="gp",
    ...             maximize="loss",
    ...             random_seed=1,
    ...             max_trials=4)
    INFO: [guild] Found 0 previous trial(s) for use in optimization
    INFO: [guild] Initialized trial ... (x=0.0, y=2, z=a)
    INFO: [guild] Running trial ...: echo (x=0.0, y=2, z=a)
    0.0 2 'a'
    INFO: [guild] Found 1 previous trial(s) for use in optimization
    INFO: [guild] Initialized trial ... (x=..., y=2, z=a)
    INFO: [guild] Running trial ...: echo (x=..., y=2, z=a)
    ... 2 'a'
    INFO: [guild] Found 2 previous trial(s) for use in optimization
    INFO: [guild] Initialized trial ... (x=..., y=2, z=a)
    INFO: [guild] Running trial ...: echo (x=..., y=2, z=a)
    ... 2 'a'
    INFO: [guild] Found 3 previous trial(s) for use in optimization
    INFO: [guild] Initialized trial ... (x=..., y=2, z=a)
    INFO: [guild] Running trial ...: echo (x=..., y=2, z=a)
    ... 2 'a'

And the latest loss:

    >>> latest_run = project.list_runs()[0]
    >>> loss = project.run_scalar(latest_run, None, "loss", "last", False)
    >>> isinstance(loss, float) and loss > 0, loss, latest_run.path
    (True, ...)
