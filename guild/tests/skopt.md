# Scikit optimize

Before running tests with the `skopt` module, let's silence the
warnings from `numpy.core.umath_tests`:

    >>> import warnings
    >>> warnings.filterwarnings("ignore", category=Warning)
    >>> import numpy.core.umath_tests

## Bayesian optimization

Support for Bayesian optimization is provided by `skopt.gp_minimize`
function. However, we use
`guild.plugins.skopt_util.patched_gp_minimize` as a drop-in
replacement to work around an issue with skopt and sklearn. See
docstring for that function for details.

    >>> from guild.plugins.skopt_util import patched_gp_minimize as gp_minimize

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
    INFO: [guild] Random start for optimization (1 of 3)
    INFO: [guild] Running trial ...: echo (x=..., y=2, z=a)
    ... 2 'a'
    INFO: [guild] Random start for optimization (2 of 3)
    INFO: [guild] Running trial ...: echo (x=..., y=2, z=a)
    ... 2 'a'
    INFO: [guild] Random start for optimization (3 of 3)
    INFO: [guild] Running trial ...: echo (x=..., y=2, z=a)
    ... 2 'a'
    INFO: [guild] Found 3 previous trial(s) for use in optimization
    INFO: [guild] Running trial ...: echo (x=..., y=2, z=a)
    ... 2 'a'

## Missing objective

When previous trials don't have specified objective, generates a
random trials.

    >>> project = Project(sample("projects", "optimizers"))
    >>> project.run("echo", flags={"x": "[-2.0:2.0]"},
    ...             opt_flags={"random-starts": 2},
    ...             optimizer="gp",
    ...             minimize="no_such_scalar",
    ...             max_trials=4)
    INFO: [guild] Random start for optimization (1 of 2)
    INFO: [guild] Running trial ...: echo (x=..., y=2, z=...)
    ... 2 ...
    INFO: [guild] Random start for optimization (2 of 2)
    INFO: [guild] Running trial ...: echo (x=..., y=2, z=...)
    ... 2 ...
    INFO: [guild] Random start for optimization (cannot find objective 'no_such_scalar')
    INFO: [guild] Running trial ...: echo (x=..., y=2, z=...)
    ... 2 ...
    INFO: [guild] Random start for optimization (cannot find objective 'no_such_scalar')
    INFO: [guild] Running trial ...: echo (x=..., y=2, z=...)
    ... 2 ...

## Errors

Invalid objective specs:

    >>> project.run("echo", flags={"x": "[-2:2]"}, optimizer="gp",
    ...             maximize="the quick brown fox")
    ERROR: [guild] invalid objective 'the quick brown fox': unexpected
    token 'quick', line 1, pos 11
    <exit 1>

    >>> project.run("echo", flags={"x": "[-2:2]"}, optimizer="gp",
    ...             minimize="loss, accuracy")
    ERROR: [guild] invalid objective 'loss, accuracy': too many columns
    <exit 1>
