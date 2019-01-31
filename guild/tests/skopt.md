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
